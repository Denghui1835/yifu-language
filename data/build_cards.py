# -*- coding: utf-8 -*-
"""义符 · 词源卡生产流水线（引擎）

一条链：kaikki 原始切片 → 抽取 → 义类候选 → 草稿卡 → 【人工复核闸门】 → 成品卡

设计上的两条硬规矩
------------------
1. **每个字段都必须带 src。** 抽不出 kaikki 原文支撑的字段一律留空并打 flag，
   绝不用模型记忆补。词源和字源是硬知识，凭印象写就是给评委递刀子。
2. **草稿 ≠ 成品。** 本脚本产出的一律是 `status: "draft"`；
   只有经复核、逐字段签过字的卡才能置为 `reviewed` 并进成品库。
   中文释义与词源故事**不由本脚本生成** —— 它们要么由人写，
   要么由模型起草后经复核，两者都必须过闸门。

用法：
    python build_cards.py                # 跑 18 词试点批
    python build_cards.py --all-water    # 跑「水」义类全部候选词
"""
import io, os, re, json, html as htmllib, datetime

from etym_parse import parse_file, primary, REDIRECT, tpl_pairs, parse_tree_lines
from yilei_roots import match_roots, match_affix

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, 'etym_raw')
OUT = os.path.join(HERE, '..', 'docs', 'data', 'cards.json')
CLASS = os.path.join(HERE, 'etym_class.json')

TODAY = datetime.date.today().isoformat()
KAIKKI = 'https://kaikki.org/dictionary/English/'

# ---------------------------------------------------------------- 18 词试点批
# pilot 字段是**设计时定的义类**（见 01_对照测试/00_测试方案.md §四），
# 不是流水线算出来的。复核时拿它和 proposal 对照 —— 不一致的正是要看的。
PILOT = [
    ('aqueduct',      '水'), ('aquamarine', '水'), ('hydrate', '水'),
    ('dehydrate',     '水'), ('maritime',   '水'), ('submarine', '水'),
    ('manuscript',    '手'), ('manicure',   '手'), ('manipulate', '手'),
    ('emancipate',    '手'), ('chiropractor', '手'), ('chirography', '手'),
    ('cordial',       '心'), ('accord',     '心'), ('discord', '心'),
    ('concord',       '心'), ('psychiatrist', '心'), ('empathy', '心'),
]

GLOSS_RE = re.compile(r'<span class="gloss">(.*?)</span>', re.S)
IPA_RE = re.compile(r'infolabel">IPA</span>:\s*(/[^/<]+/)\s*(?:<|,|\n)')
# 有些词的 IPA 后面直接跟别的，放宽一档兜底
IPA_RE2 = re.compile(r'infolabel">IPA</span>:[^/]*(/[^/]+/)')
H2_RE = re.compile(r'<h2[^>]*>(.*?)</h2>', re.S)
TAG = re.compile(r'<[^>]+>')


def txt(s):
    return re.sub(r'\s+', ' ', htmllib.unescape(htmllib.unescape(TAG.sub(' ', s or '')))).strip()


def extract(html):
    """从 kaikki 切片里抠出可核查的原始字段。抠不到就留空，不猜。"""
    ipa = ''
    for rx in (IPA_RE, IPA_RE2):
        m = rx.search(html)
        if m:
            ipa = m.group(1).strip()
            break
    glosses = []
    for g in GLOSS_RE.findall(html):
        t = txt(g)
        if t and t not in glosses:
            glosses.append(t)
    # 词性小标题（h2）里除了语种还有 "Noun"/"Adjective" 这类
    poss = [txt(m) for m in H2_RE.findall(html)]
    poss = [p for p in poss if p in ('Noun', 'Verb', 'Adjective', 'Adverb',
                                     'Preposition', 'Conjunction', 'Interjection')]
    return {'ipa': ipa, 'gloss_en': glosses[:6], 'pos_all': sorted(set(poss))}


def ancestors(block):
    """词源祖先链：[(语种名, 词条, 语种码)]。

    三条路，按可靠性排序取第一个出结果的：
      1. kaikki 渲染好的 "Etymology tree" 文本块 —— 字面文本，不会串位，首选
      2. 内嵌 JSON 树 —— 结构最全，但切片被截断时解析不出来
      3. 普通模板 {{der|en|la|maritimus}} —— 兜底
    ★ 绝不按下标对齐三组正则的结果：有节点缺 term 时整套语种名会串位，
      会生成出 "Latin:*h₂ékʷeh₂"（*h₂ékʷeh₂ 实为原始印欧语）这种假链。
    """
    out = [{'lang': n, 'term': t, 'code': c}
           for n, t, c in parse_tree_lines(block['tree']) if t]
    src = 'tree-text' if out else ''
    if not out:
        for name, term, lang in block['codes']:
            if term and lang:
                out.append({'lang': name, 'term': term, 'code': lang})
        src = 'json-tree' if out else ''
    if not out:
        out = [{'lang': n, 'term': t, 'code': c}
               for n, t, c in tpl_pairs(block['tpl'])]
        src = 'templates' if out else 'none'
    return out, src


CLASSICAL = {'classical': '古典（拉丁/希腊）', 'germanic': '日耳曼',
             'romance': '罗曼语', 'unknown': '未定'}

# 语源分类：优先从**祖先链**推（链是 kaikki 原文，比查表硬），查不到才退回分类表。
# 高碘表对雅思级词覆盖很差（18 词里只有 2 词查得到），所以这条不能靠表。
CLASSICAL_CODES = {'la', 'la-med', 'la-new', 'la-vul', 'la-ecc', 'la-ren', 'la-cla',
                   'la-ine', 'grc', 'gkm', 'el', 'itc-pro', 'itc-ola', 'ine-pro',
                   'grk-pro', 'sa', 'xcl', 'peo'}
GERMANIC_CODES = {'ang', 'enm', 'gem-pro', 'gmw-pro', 'gmq-pro', 'non', 'de', 'gmh',
                  'goh', 'nl', 'dum', 'odt', 'ofs', 'osx', 'is', 'sv', 'da', 'no',
                  'got', 'frk', 'sco'}
ROMANCE_CODES = {'fr', 'frm', 'fro', 'nrf', 'it', 'es', 'pt', 'ca', 'ro', 'pro',
                 'roa-oil', 'roa', 'roa-fra', 'roa-ibe', 'roa-opt', 'oc', 'scn'}


def class_from_chain(anc):
    codes = {a['code'] for a in anc}
    if codes & CLASSICAL_CODES:
        return 'classical'
    if codes & ROMANCE_CODES:
        return 'romance'
    if codes & GERMANIC_CODES:
        return 'germanic'
    return None


def flags_of(rec):
    f = []
    if not rec['ipa']:
        f.append(('no_ipa', '音标未抽到'))
    if not rec['gloss_en']:
        f.append(('no_gloss', '英文释义未抽到'))
    if not rec['etym']['prose']:
        f.append(('no_etym', '词源正文未抽到'))
    elif REDIRECT.match(rec['etym']['prose']):
        f.append(('redirect_prose', '主词源段是转发句，需另找实义词性段'))
    if not rec['etym']['ancestors']:
        f.append(('no_chain', '祖先链为空'))
    cands = rec['proposal']['yilei']
    cls = {c['yilei'] for c in cands}
    if not cands:
        f.append(('no_yilei', '挂不上任何义类'))
    elif len(cls) > 1:
        f.append(('ambiguous_yilei', '义类候选多于一个：%s' % '、'.join(sorted(cls))))
    if any(c['root_len'] <= 3 for c in cands):
        f.append(('short_root', '含 3 字母短词根，假阳性风险高，必须逐条核对'))
    if rec['etym_class'] == 'germanic':
        f.append(('germanic', '日耳曼源词，义符法不适用'))
    if rec['pilot_yilei'] and cands and rec['pilot_yilei'] not in cls:
        f.append(('pilot_mismatch',
                  '设计义类「%s」与流水线候选「%s」不一致，需人工判谁对'
                  % (rec['pilot_yilei'], '、'.join(sorted(cls)))))
    return [{'code': c, 'msg': m} for c, m in f]


def build_one(word, pilot_yilei=None, classmap=None):
    p = os.path.join(RAW, word + '.html')
    rec = {
        'w': word, 'len': len(word),
        'pilot_yilei': pilot_yilei,
        'ipa': '', 'gloss_en': [], 'pos_all': [],
        'def_zh': None,            # ← 人工/模型起草 + 复核，流水线不生成
        'etym': {'prose': '', 'tree': '', 'ancestors': []},
        'proposal': {'yilei': [], 'prefix': None, 'suffix': None,
                     'han_fu': None},   # ← 汉语义符：只给候选位，人工填
        'etym_class': (classmap or {}).get(word, 'unknown'),
        'src': {'site': 'kaikki.org', 'path': 'etym_raw/%s.html' % word,
                'url': KAIKKI, 'fetched': TODAY},
        'flags': [],
        'status': 'draft',
        'review': {'by': None, 'at': None, 'fields': {}, 'notes': []},
    }
    if not os.path.exists(p):
        rec['flags'] = [{'code': 'no_raw', 'msg': '本地没有该词的 kaikki 切片'}]
        return rec

    html = io.open(p, encoding='utf-8', errors='replace').read()
    ex = extract(html)
    rec['ipa'], rec['gloss_en'], rec['pos_all'] = ex['ipa'], ex['gloss_en'], ex['pos_all']

    blocks = parse_file(p)
    b = primary(blocks)
    if b:
        rec['etym']['prose'] = b['prose']
        rec['etym']['tree'] = b['tree']
        anc, src_from = ancestors(b)
        rec['etym']['chain_from'] = src_from
        rec['etym']['ancestors'] = anc
        derived = class_from_chain(anc)
        if derived:
            rec['etym_class'] = derived

    # 义类候选：拿「现代词 + 全部祖先词条」一起去撞词根表。
    # 比只拿现代词去撞准得多 —— maritime 撞不上 'mar'，但它的祖先 maritimus 撞得上。
    terms = [word] + [a['term'] for a in rec['etym']['ancestors']]
    rec['proposal']['yilei'] = [
        {'yilei': cls, 'root': r, 'root_len': len(r), 'hit_in': term}
        for cls, r, term in match_roots(terms)
    ]
    pre, suf = match_affix(word)
    rec['proposal']['prefix'], rec['proposal']['suffix'] = pre, suf

    rec['flags'] = flags_of(rec)
    return rec


def main():
    import sys
    # 语源分类：高考表与雅思表合并。两张表覆盖的词不同，
    # 任一张判为 concrete（classical/germanic/romance）就采信，都是 unknown 才算未定。
    classmap = {}
    for fn in ('etym_class.json', 'ielts_class.json'):
        fp = os.path.join(HERE, fn)
        if os.path.exists(fp):
            for k, v in json.load(io.open(fp, encoding='utf-8')).items():
                if classmap.get(k, 'unknown') == 'unknown' or v != 'unknown':
                    classmap.setdefault(k, v)
                    if classmap[k] == 'unknown' and v != 'unknown':
                        classmap[k] = v

    if '--all' in sys.argv:
        buckets = json.load(io.open(os.path.join(HERE, 'yilei_buckets.json'),
                                    encoding='utf-8'))
        want = sys.argv[sys.argv.index('--all') + 1] if len(sys.argv) > sys.argv.index('--all') + 1 else None
        pairs = []
        for cls, ws in buckets.items():
            if want and cls != want:
                continue
            pairs += [(w, cls) for w in ws]
    else:
        pairs = PILOT

    cards = [build_one(w, y, classmap) for w, y in pairs]
    os.makedirs(os.path.dirname(os.path.abspath(OUT)), exist_ok=True)
    json.dump({'schema': 1, 'built': TODAY,
               'note': '流水线草稿。status=draft 的卡不得进成品库；'
                       '每字段的复核签字记在 review.fields。',
               'cards': cards},
              io.open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

    # ---- 控制台摘要（写文件，避开控制台 GBK 乱码）----
    L = []
    L.append('产出 %d 张草稿卡 -> %s' % (len(cards), OUT))
    L.append('')
    L.append('%-16s %-4s %-6s %-22s %s' % ('词', '设计', '源', '义类候选', 'flag'))
    for c in cards:
        cands = '、'.join(sorted({x['yilei'] for x in c['proposal']['yilei']})) or '—'
        fl = ','.join(f['code'] for f in c['flags']) or 'ok'
        L.append('%-16s %-4s %-6s %-22s %s'
                 % (c['w'], c['pilot_yilei'] or '—', CLASSICAL.get(c['etym_class'], '?'),
                    cands, fl))
    L.append('')
    from collections import Counter
    cnt = Counter(f['code'] for c in cards for f in c['flags'])
    L.append('flag 统计：' + ('、'.join('%s=%d' % kv for kv in cnt.most_common()) or '无'))
    io.open(os.path.join(HERE, '_pipeline_out.txt'), 'w', encoding='utf-8').write('\n'.join(L))


if __name__ == '__main__':
    main()