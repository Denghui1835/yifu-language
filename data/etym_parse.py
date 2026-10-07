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
       'slbor', 'obor', 'ubor', 'reborrowing', 'calque', 'psm', 'com',
       # ★ lbor = learned borrowing。只有 slbor/obor/ubor 而没有 lbor 是个漏，
       #   很多学术词（emancipate、psychiatrist 这类）走的正是 lbor，
       #   漏了它祖先链就断在英语这一层。
       'lbor'}
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


# 语言码 → 中文语种名。只收祖先链里高频出现的那些，够用即可。
LANG_NAME = {
    'la': '拉丁语', 'la-med': '中世纪拉丁', 'la-new': '新拉丁', 'la-vul': '俗拉丁',
    'grc': '希腊语', 'gkm': '中古希腊语', 'el': '现代希腊语',
    'fr': '法语', 'frm': '中古法语', 'fro': '古法语', 'nrf': '诺曼语',
    'it': '意大利语', 'es': '西班牙语', 'pt': '葡萄牙语', 'ca': '加泰罗尼亚语',
    'enm': '中古英语', 'ang': '古英语', 'de': '德语', 'gmh': '中古高地德语',
    'goh': '古高地德语', 'nl': '荷兰语', 'dum': '中古荷兰语',
    'non': '古诺斯语', 'is': '冰岛语', 'sv': '瑞典语', 'da': '丹麦语',
    'gem-pro': '原始日耳曼语', 'gmw-pro': '原始西日耳曼语',
    'ine-pro': '原始印欧语', 'itc-pro': '原始意大利语', 'itc-ola': '古拉丁语',
    'he': '希伯来语', 'ar': '阿拉伯语', 'fa': '波斯语', 'sa': '梵语',
    'zh': '汉语', 'ja': '日语', 'ru': '俄语', 'cel-pro': '原始凯尔特语',
    'sga': '古爱尔兰语', 'cy': '威尔士语', 'tr': '土耳其语',
}
AT1_PAIRS = AT1


def tpl_pairs(tpl_text):
    """从普通模板串里抽 (语言码, 词条)，补内嵌 JSON 树缺失的场合。

    很多 kaikki 页没有 "lang_name" 的 JSON 树，只有
        {{der|en|la|maritimus}}   {{inh|en|enm|maritime}}
    这类模板。这类模板的第 2 位固定是**语言码**，第 3 位是**词条**。
    AT1 里的模板名就是这个形状（der/inh/bor/…），AT0 的（m/l/link）不是，
    所以只认 AT1，免得再把词当语种（第一版栽过）。
    """
    out = []
    for m in TPL.finditer(tpl_text or ''):
        if m.group(1).strip().lower() not in AT1_PAIRS:
            continue
        parts = [p.split('=')[0].strip() for p in m.group(2).split('|')]
        if len(parts) < 3:
            continue
        code, term = parts[1].split(':')[0], parts[2]
        if code and code != 'en' and code in WL and term and term not in ('-', '—'):
            out.append((LANG_NAME.get(code, code), term, code))
    return out


F_NAME = re.compile(r'"lang_name"\s*:\s*"([^"]*)"')

# 英语语种名 → 语言码。kaikki 的 "Etymology tree" 文本块用的是**英语语种名**，
# 内嵌 JSON 才用语言码，所以要一张反查表。
LANG_CODE_EN = {
    'Latin': 'la', 'Medieval Latin': 'la-med', 'New Latin': 'la-new',
    'Late Latin': 'la-lat', 'Vulgar Latin': 'la-vul', 'Old Latin': 'itc-ola',
    'Ancient Greek': 'grc', 'Greek': 'grc', 'Mycenaean Greek': 'gmy',
    'Koine Greek': 'grc-koi', 'Medieval Greek': 'gkm',
    'French': 'fr', 'Middle French': 'frm', 'Old French': 'fro', 'Norman': 'nrf',
    'Anglo-Norman': 'xno', 'Old Northern French': 'fro-nor',
    'Italian': 'it', 'Spanish': 'es', 'Portuguese': 'pt', 'Catalan': 'ca',
    'Old Spanish': 'osp', 'Old Occitan': 'pro',
    'English': 'en', 'Middle English': 'enm', 'Old English': 'ang',
    'German': 'de', 'Middle High German': 'gmh', 'Old High German': 'goh',
    'Dutch': 'nl', 'Middle Dutch': 'dum', 'Old Dutch': 'odt',
    'Old Norse': 'non', 'Icelandic': 'is', 'Swedish': 'sv', 'Danish': 'da',
    'Norwegian': 'no', 'Gothic': 'got', 'Frankish': 'frk',
    'Proto-Indo-European': 'ine-pro', 'Proto-Italic': 'itc-pro',
    'Proto-Germanic': 'gem-pro', 'Proto-West Germanic': 'gmw-pro',
    'Proto-Northwest Germanic': 'gmw-pro', 'Proto-Hellenic': 'grk-pro',
    'Proto-Romance': 'roa-pro', 'Proto-Celtic': 'cel-pro',
    'Proto-Slavic': 'sla-pro', 'Proto-Balto-Slavic': 'ine-bsl-pro',
    'Proto-Brythonic': 'cel-bry-pro', 'Proto-Semitic': 'sem-pro',
    'Hebrew': 'he', 'Arabic': 'ar', 'Persian': 'fa', 'Sanskrit': 'sa',
    'Chinese': 'zh', 'Japanese': 'ja', 'Russian': 'ru', 'Old Irish': 'sga',
    'Welsh': 'cy', 'Turkish': 'tr', 'Middle Irish': 'mga', 'Irish': 'ga',
}


def parse_tree_lines(tree_text):
    """把 "Etymology tree" 文本块解析成 [(语种名, 词条, 语种码)]。

    kaikki 渲染出来的这个文本块每行就是「语种名 词条」，形如：
        Proto-Indo-European *h₂ékʷeh₂
        Proto-Italic *akʷā
        Latin aqua
    它是**字面文本**，不存在内嵌 JSON 那种按下标对齐的串位问题，
    所以当主路径用；解析不出来的行走 templates 兜底。
    """
    out = []
    for line in (tree_text or '').split('\n'):
        line = line.strip()
        if not line:
            continue
        if ' ' not in line:
            continue
        name, term = line.rsplit(' ', 1)
        name = name.strip()
        # 树文本会把词条与关系标签渲染在一起（"*h₂ékʷeh₂der."、"*mer-?"），
        # 以及没词条的占位符 "-"，这些都得清掉，否则会当成词条混进义类匹配。
        term = re.sub(r'(?:der|inh|bor|derived|inherited|borrowed|calque)\.?$', '', term).strip()
        term = term.rstrip('?').strip()
        if not term or term == '-':
            continue
        code = LANG_CODE_EN.get(name, '')
        if not code:
            # {"lang_name":"x"} 那种两字母码偶尔也会原样渲染出来
            code = LANG_CODE_EN.get(name, name if re.fullmatch(r'[a-z\-]{2,8}', name) else '')
        out.append((name, term.strip(), code))
    return out


F_TERM = re.compile(r'"term"\s*:\s*"([^"]*)"')
F_LANG = re.compile(r'"lang"\s*:\s*"([^"]*)"')


def _json_nodes(tpl_text):
    """把内嵌的 JSON 词源树真解析出来，返回 [(lang_name, term, lang)]。

    ★ 以前是用三条正则分别抓 lang_name / term / lang，再按**下标**对齐。
      这是错的：有些节点有 lang_name 却没有 term（如 aquamarine 的
      "Latin / aqua marīna" 只有 alt），下标一对齐，整套语种名就整体串位，
      生成出 "Latin:*h₂ékʷeh₂"（*h₂ékʷeh₂ 实为原始印欧语）这种假链。
      解析不了就返回 None，让调用方退回模板路径。
    """
    # 逐个 '{' 当起点试：能配平、能 json.loads、且含 lang_name 的第一个就是根。
    # ★ 不能只取「第一个含 lang_name 的 {」——那往往是**内层**对象，括号不配平，
    #   解析必然失败；一转正则就又把下标对齐的错犯一遍。
    i = tpl_text.find('{')
    while i >= 0:
        depth, j, instr, esc = 0, i, False, False
        while j < len(tpl_text):
            ch = tpl_text[j]
            if instr:
                if esc:
                    esc = False
                elif ch == '\\':
                    esc = True
                elif ch == '"':
                    instr = False
            elif ch == '"':
                instr = True
            elif ch == '{':
                depth += 1
            elif ch == '}':
                depth -= 1
                if depth == 0:
                    break
            j += 1
        if j < len(tpl_text):
            blob = tpl_text[i:j + 1]
            if 'lang_name' in blob:
                try:
                    obj = json.loads(blob)
                except Exception:
                    obj = None
                if obj is not None:
                    out = []

                    def walk(n):
                        if isinstance(n, dict):
                            for v in n.values():
                                walk(v)
                            if n.get('lang_name') and n.get('lang'):
                                out.append((n['lang_name'], n.get('term', ''), n['lang']))
                        elif isinstance(n, list):
                            for v in n:
                                walk(v)

                    walk(obj)
                    if out:
                        return out
        i = tpl_text.find('{', i + 1)
    return None


def triples(tpl):
    got = _json_nodes(tpl)
    if got is not None:
        # 去重，保序
        seen, out = set(), []
        for t in got:
            if t not in seen:
                seen.add(t)
                out.append(t)
        return out
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

# ★ 只有「转发句」的词源段不含信息：
#   record 的 Adjective 段是 "From Middle English recorde, ... See record."
#   真正的词源在 Verb 段（re- + cor 心）。以前按「最长」挑，恰好挑中转发段。
REDIRECT = re.compile(r'^\s*(?:See\s|Alternative (?:form|spelling) of|'
                      r'Misspelling of|Plural of|Clipping of|Short for|'
                      r'Abbreviation of|Initialism of|Acronym of|'
                      r'Contraction of)\b', re.I)


def primary(blocks):
    """挑一个「主词源」：优先实义词性，其次最长的那段。
    转发段（See X）在存在有效段时一律跳过。"""
    if not blocks:
        return None
    good = [b for b in blocks if b['pos'] in CONTENT_POS]
    pool = good or blocks
    real = [b for b in pool if not REDIRECT.match(b['prose'] or '')]
    pool = real or pool
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
