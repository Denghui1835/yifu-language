# -*- coding: utf-8 -*-
"""
离线解析 kaikki 原始 HTML 切片。不联网，随便改随便跑。

kaikki 页面每个词性(h2)下有一组 <span class="info">：
    Etymology          : <词源树几行> + <词源正文>
    Etymology templates: {{模板...}} + 内嵌 JSON 树
内嵌 JSON 里每个节点长这样：
    { "lang_name" : "Latin", "term" : "ācta", "lang" : "la", "children" : [...] }
—— 这就是结构化的祖先链，直接给「两条演变时间轴」里英语那一侧用。

所以本模块输出：
    blocks = [ {pos, prose, tree, codes[(lang_name,term,lang)], tpl} ]
"""
import io, os, re, html as htmllib

POS_RE = re.compile(r'<h2[^>]*>(.*?)</h2>', re.S)
TAG = re.compile(r'<[^>]+>')
# JSON 里节点的键顺序不固定（有的 lang 在前有的 term 在前），
# 所以三个字段各抽各的、按下标对齐，而不是用一个固定顺序的正则去套。
# ── 旧式普通模板的语种抽取 ──────────────────────────────────────────
# 很多页面没有 JSON 树，只有 {{inh|en|enm|abord}} / {{der|en|la|aboleo|...}}。
# 这类模板要看模板名决定第几位是语言：
#   {{der|en|la|aboleo}}   第2位 la 是语言   -> 取
#   {{af|en|a-|board}}     第2位是词不是语言 -> 不取
TPL = re.compile(r'\{\{\s*([a-zA-Z \-]+?)\s*\|([^{}]*)\}\}')
AT1 = {'der', 'derived', 'inh', 'inherited', 'bor', 'borrowed', 'root',
       'etymon', 'cog', 'cognate', 'ncog', 'doublet', 'learned borrowing',
       'slbor', 'obor', 'ubor', 'reborrowing', 'calque', 'psm', 'com'}
AT0 = {'m', 'mention', 'l', 'link', 'lang', 'desc', 'descendant'}
WORD_ONLY = {'suffix', 'prefix', 'affix', 'af', 'compound', 'blend', 'clipping',
             'abbreviation', 'initialism', 'acronym', 'short for', 'ellipsis',
             'alternative form of', 'plural of', 'diminutive', 'en-part',
             'surface analysis', 'back-formation', 'confix', 'pre', 'suf'}
# 白名单：不在表里的丢掉，免得再把词当语种（第一版栽过，ab/able/acre 都被当成语言）
WL = set("""
la la-lat la-med la-new la-vul la-ecc la-ren la-cla la-ine LL NL ML
grc grc-koi grc-att grc-dor grc-hom grc-pie grc-hel gkm el
fro frm fr xno nrf pro pro-fro frp pic wa oc roa-oil
it es pt ca ro scn vec fur lmo nap rm dlm ast gl mwl co lij pms egl rgn
osp roa roa-opt roa-fra roa-pro roa-ibe
ang enm non gem-pro gmh goh got de nl dum odt ofs osx is sv da no nb nn
yi frk gmq gmw gme sco fo gmq-pro gmw-pro gml and ovl
ine-pro ine ine-ana ine-ine itc-pro itc-ola itc grk-pro cel-pro cel-gau
cel celtic sga mga wlm owl ga gd cy br kw gv
ar he fa tr hi sa zh ja ko ms id ta te ru pl cs sk uk bg sr sh hr sl
lt lv et fi hu sq hy ka az kk uz mn th vi km lo my ne bn pa gu mr ur
sd si am sw zu yo ha af xh st tn nso xcl ota peo ae ave inc dra or ml kn
ku ps tg ky tt ba cv sah
""".split())


def plain_codes(tpl_text):
    out = []
    for m in TPL.finditer(tpl_text or ''):
        name = m.group(1).strip().lower()
        if name in WORD_ONLY:
            continue
        parts = [p.split('=')[0].strip() for p in m.group(2).split('|')]
        idx = 1 if name in AT1 else (0 if name in AT0 else None)
        if idx is None or len(parts) <= idx:
            continue
        code = parts[idx].split(':')[0]
        if code and code != 'en' and code in WL:
            out.append(code)
    return out


F_NAME = re.compile(r'"lang_name"\s*:\s*"([^"]*)"')
F_TERM = re.compile(r'"term"\s*:\s*"([^"]*)"')
F_LANG = re.compile(r'"lang"\s*:\s*"([^"]*)"')


def triples(tpl):
    names = F_NAME.findall(tpl)
    terms = F_TERM.findall(tpl)
    langs = F_LANG.findall(tpl)
    n = min(len(names), len(langs))
    out = []
    for i in range(n):
        t = terms[i] if i < len(terms) else ''
        out.append((names[i], t, langs[i]))
    return out


def _txt(s):
    s = TAG.sub(' ', s)
    s = htmllib.unescape(htmllib.unescape(s))
    return re.sub(r'\s+', ' ', s).strip()


def _sections(h):
    """按 h2(词性) 切段，返回 [(pos, 该段HTML)]"""
    marks = [(m.start(), _txt(m.group(1))) for m in POS_RE.finditer(h)]
    out = []
    for i, (p, name) in enumerate(marks):
        end = marks[i + 1][0] if i + 1 < len(marks) else len(h)
        out.append((name, h[p:end]))
    return out


def _info_fields(seg):
    """抠出段内所有 infolabel 字段，返回 {字段名: (塌成一行, 保留换行)}"""
    labels = [(m.start(), _txt(m.group(1)))
              for m in re.finditer(r'<span class="infolabel">(.*?)</span>', seg, re.S)]
    out = {}
    for i, (p, name) in enumerate(labels):
        end = labels[i + 1][0] if i + 1 < len(labels) else len(seg)
        val = seg[p:end]
        val = re.sub(r'^.*?</span>\s*:?', '', val, count=1, flags=re.S)
        raw = htmllib.unescape(htmllib.unescape(TAG.sub(' ', val)))
        raw = '\n'.join(l.strip() for l in raw.split('\n') if l.strip())
        out.setdefault(name, (_txt(val), raw))
    return out


def parse_file(path):
    h = io.open(path, encoding='utf-8', errors='replace').read()
    if not h.strip():
        return []
    blocks = []
    for pos, seg in _sections(h):
        f = _info_fields(seg)
        ety, ety_raw = f.get('Etymology', ('', ''))
        tpl_raw = f.get('Etymology templates', ('', ''))[0]
        if not ety and not tpl_raw:
            continue
        # 词源树 = "Etymology tree" 之后、正文句首之前的那几行（保留换行以分节点）
        tree, prose = '', ety
        if 'Etymology tree' in ety_raw:
            after = ety_raw.split('Etymology tree', 1)[1]
            lines = [l for l in after.split('\n') if l.strip()]
            # 树行形如「拉丁语 词」，正文行是完整句子（含空格后的多个词）
            k = 0
            for j, l in enumerate(lines):
                # 语言名可能带连字符；树节点 = 语言名 + 一个词，词里不含空格
                if re.match(r'^[A-Z][A-Za-z\'\- ]*?\s\S+$', l) and len(l.split()) <= 4:
                    k = j + 1
                else:
                    break
            tree = '\n'.join(lines[:k])
            prose = ' '.join(lines[k:]) or ety
        # 内嵌 JSON 树里的 (语言名, 词, 语言码) 三元组，按树序
        codes = triples(tpl_raw)
        blocks.append({'pos': pos, 'prose': prose or ety, 'tree': tree,
                       'codes': codes, 'tpl': tpl_raw,
                       'tlangs': plain_codes(tpl_raw) or plain_codes(ety_raw)})
    return blocks


CONTENT_POS = ('Noun', 'Verb', 'Adjective', 'Adverb')


def primary(blocks):
    """挑一个「主词源」：优先实义词性，其次最长的那段"""
    if not blocks:
        return None
    good = [b for b in blocks if b['pos'] in CONTENT_POS]
    pool = good or blocks
    return max(pool, key=lambda b: len(b['tree']) + len(b['prose']))


if __name__ == '__main__':
    import sys
    for w in (sys.argv[1:] or ['act']):
        p = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'etym_raw',
                         re.sub(r'[^\w\-]', '_', w.lower()) + '.html')
        bs = parse_file(p)
        print('=== %s  (%d 段) ===' % (w, len(bs)))
        for b in bs:
            print(' [%s] tree=%d字  prose=%s' % (b['pos'], len(b['tree']), b['prose'][:80]))
            if b['tree']:
                print('   树: ' + ' → '.join(b['tree'].split('\n')[:12]))
            print('   码: ' + ','.join(sorted({c for _, _, c in b['codes']})))
