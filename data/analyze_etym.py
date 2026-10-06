# -*- coding: utf-8 -*-
"""
用 kaikki 词源树给高考词表逐词定性。离线跑，读 etym_raw/*.html。

判定：看这个词的**祖先链上有没有拉丁/希腊节点**。
  classical  链上有拉丁或古希腊        -> 能挂上义符词根
  romance    链上只有罗曼斯语族        -> 多可追到拉丁
  germanic   链上只有日耳曼语族        -> 底层词，无古典词根
  mixed      拉丁/希腊 与 日耳曼 都有  -> 只算「有古典成分」
  other      阿拉伯语等其它来源
  unknown    抓不到词源，且派生链也解不出

派生回退：ability 只有 {{suffix|en|able|ity}} 没有词源树，
  那就拆出 able，去查 able 的词源（拉丁 habilis）-> 归为 classical。

产出：etym_class.json（词 -> 类别）、etym_trees.json（词 -> 祖先链，给演变时间轴用）
"""
import io, json, os, re, glob, sys, collections
import etym_parse as ep

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, 'etym_raw')

LATIN = {'la', 'la-lat', 'la-med', 'la-new', 'la-vul', 'la-ecc', 'la-ren',
         'la-cla', 'la-ine', 'LL', 'NL', 'ML'}
GREEK = {'grc', 'grc-koi', 'grc-att', 'grc-dor', 'grc-hom', 'grc-pie',
         'grc-hel', 'gkm', 'el'}
ROMANCE = {'fro', 'frm', 'fr', 'xno', 'nrf', 'pro', 'pro-fro', 'frp', 'pic',
           'wa', 'oc', 'roa-oil', 'it', 'es', 'pt', 'ca', 'ro', 'scn', 'vec',
           'fur', 'lmo', 'nap', 'rm', 'dlm', 'ast', 'gl', 'mwl', 'co', 'lij',
           'pms', 'egl', 'rgn', 'osp', 'roa', 'roa-opt', 'roa-fra', 'roa-pro',
           'roa-ibe'}
GERMANIC = {'ang', 'enm', 'non', 'gem-pro', 'gmh', 'goh', 'got', 'de', 'nl',
            'dum', 'odt', 'ofs', 'osx', 'is', 'sv', 'da', 'no', 'nb', 'nn',
            'yi', 'frk', 'gmq', 'gmw', 'gme', 'sco', 'fo', 'gmq-pro',
            'gmw-pro', 'gml', 'and', 'ovl'}
PIE = {'ine-pro', 'ine', 'ine-ana', 'ine-ine'}

CLASSICAL, ROMANIC, GERM = 'classical', 'romance', 'germanic'

# 拆词模板：参数全是词素的
DERIV = re.compile(r'\{\{\s*(suffix|prefix|compound|affix|blend|clipping|'
                   r'back-formation|abbreviation|initialism|acronym|'
                   r'short for|ellipsis|alternative form of|'r'plural of)\s*\|([^{}]*)\}\}')


def key_of(hw):
    return re.sub(r'[^\w\-]', '_', hw.lower())


def components(tpl_text):
    """从模板里抠出可递归查的词素"""
    out = []
    for m in DERIV.finditer(tpl_text or ''):
        parts = [p.strip() for p in m.group(2).split('|')]
        for p in parts[1:]:                      # 跳过 en
            p = p.split('=')[0].strip()
            if not p or p == 'en' or p.startswith('-') or p.endswith('-'):
                continue
            if not re.fullmatch(r"[A-Za-z][A-Za-z'\- ]{0,24}", p):
                continue
            out.append(p.lower())
    return out


def codes_of(blocks):
    cs = set()
    for b in blocks:
        for _, _, lg in b['codes']:
            cs.add(lg)
        cs.update(b.get('tlangs') or [])
    return cs


# ★ 散文兜底：不少页面没有语言模板，只有正文
#   attract  -> "From Latin attractus, past participle of attrahere..."
#   catholic -> "From Old French catholique, from Latin catholicus, from Ancient Greek..."
#   没有这一段，光看模板会把一大批拉丁词漏成 unknown。
PROSE = re.compile(
    r'\b(?:from|borrowed\s+from|inherited\s+from|based\s+on|derived\s+from|'
    r'ultimately\s+from|coined\s+.{0,40}?based\s+on)\s+'
    r'(?:(?:ancient|new|medieval|late|vulgar|classical|old|middle|proto-?)\s+)*'
    r'(latin|greek|french|norman|anglo-norman|italian|spanish|portuguese|'
    r'english|german|dutch|norse|scandinavian|danish|swedish|germanic|'
    r'arabic|persian|hindi|sanskrit|hebrew|chinese|japanese|korean|turkish|'
    r'russian|polish|celtic|irish|welsh|gothic)', re.I)


def prose_fam(blocks):
    """正文里先出现哪个来源语。古典优先于罗曼斯，罗曼斯优先于日耳曼。"""
    hits = set()
    for b in blocks:
        for m in PROSE.finditer(b['prose'] or ''):
            hits.add(m.group(1).lower())
    if not hits:
        return None
    if hits & {'latin', 'greek'}:
        return CLASSICAL
    if hits & {'french', 'norman', 'anglo-norman', 'italian', 'spanish', 'portuguese'}:
        return ROMANIC
    if hits & {'english', 'german', 'dutch', 'norse', 'scandinavian', 'danish',
               'swedish', 'germanic', 'gothic'}:
        return GERM
    return 'other'


def fam_of(codes):
    if codes & LATIN or codes & GREEK:
        return CLASSICAL
    if codes & ROMANCE:
        return ROMANIC
    if codes & GERMANIC:
        return GERM
    return None


def main():
    recs = json.load(io.open(os.path.join(HERE, 'gaokao3500.json'), encoding='utf-8'))
    heads, meta = [], {}
    for r in recs:
        h = r['hw']
        if h.lower() in meta:
            continue
        meta[h.lower()] = r
        heads.append(h)

    info = {}
    for h in heads:
        p = os.path.join(RAW, key_of(h) + '.html')
        if not os.path.exists(p) or os.path.getsize(p) == 0:
            info[h.lower()] = {'cls': 'unknown', 'codes': [], 'tree': '', 'tpl': '', 'src': 'nofile'}
            continue
        bs = ep.parse_file(p)
        codes = codes_of(bs)
        prim = ep.primary(bs)
        fam = fam_of(codes) or prose_fam(bs)
        allc = collections.Counter()
        for b in bs:
            for _, _, lg in b['codes']:
                allc[lg] += 1
        both = (frozenset(codes) & (LATIN | GREEK)) and (frozenset(codes) & (GERMANIC | {'frk'}))
        info[h.lower()] = {
            'cls': fam or 'unknown',
            'both': bool(both),
            'codes': sorted(codes),
            'freq': dict(allc),
            'tree': (prim or {}).get('tree', ''),
            'pos': (prim or {}).get('pos', ''),
            'tpl': ' || '.join(b['tpl'][:400] for b in bs)[:1200],
            'src': 'etym',
        }

    # ---- 派生回退：多轮，直到不再有新解出的 ----
    for rnd in range(4):
        changed = 0
        for h in heads:
            k = h.lower()
            d = info[k]
            if d['cls'] != 'unknown':
                continue
            comps = components(d['tpl'])
            fams = [info[c]['cls'] for c in comps if c in info and info[c]['cls'] != 'unknown']
            if not fams:
                continue
            for f in (CLASSICAL, ROMANIC, GERM):
                if f in fams:
                    d['cls'] = f
                    d['src'] = 'deriv(%s)' % ','.join(c for c in comps if c in info)
                    changed += 1
                    break
        if not changed:
            break

    cls = collections.Counter(d['cls'] for d in info.values())
    n = len(info)
    mixed = sum(1 for d in info.values() if d.get('both'))
    print('=== 词表 %d 词 ===' % n)
    for k, v in cls.most_common():
        print('  %-10s %4d  %5.1f%%' % (k, v, 100.0 * v / n))
    print('  （其中「拉丁希腊＋日耳曼」混合的 %d 词，上面已按 classical 计入）' % mixed)

    print('\n=== 长度分层：能挂古典词根的比例 ===')
    for lo, hi in [(1, 3), (4, 6), (7, 9), (10, 99)]:
        sub = [h for h in heads if lo <= len(re.sub(r'[^A-Za-z]', '', h)) <= hi]
        if not sub:
            continue
        g = sum(1 for h in sub if info[h.lower()]['cls'] in (CLASSICAL, ROMANIC))
        print('  %2d-%2d 字母: %4d 词, 可挂古典词根 %5.1f%%' % (lo, hi, len(sub), 100.0 * g / len(sub)))

    print('\n=== 词源来源 ===')
    for k, v in collections.Counter(d['src'].split('(')[0] for d in info.values()).most_common():
        print('  %-14s %4d' % (k, v))

    print('\n=== 语言代码频次 Top 25 ===')
    fc = collections.Counter()
    for d in info.values():
        for c, cnt in d.get('freq', {}).items():
            fc[c] += 1
    for c, v in fc.most_common(25):
        print('  %-10s %4d' % (c, v))

    if '--dump' in sys.argv:
        i = sys.argv.index('--dump')
        k = int(sys.argv[i + 1]) if len(sys.argv) > i + 1 else 20
        by = collections.defaultdict(list)
        for h in heads:
            by[info[h.lower()]['cls']].append(h)
        for key in (CLASSICAL, ROMANIC, GERM, 'other', 'unknown'):
            print('\n[%s] %d 词: %s' % (key, len(by[key]), '  '.join(by[key][:k])))

    json.dump({h: info[h.lower()]['cls'] for h in heads},
              io.open(os.path.join(HERE, 'etym_class.json'), 'w', encoding='utf-8'),
              ensure_ascii=False, indent=0)
    # 存下祖先链的每个节点：(语言名, 词, 语言码)。分桶时用真实词素去匹配，
    # 比拿英语拼写瞎猜准得多。没有 JSON 树的页面存空的，不影响。
    def nodes_of(h):
        p = os.path.join(RAW, key_of(h) + '.html')
        if not os.path.exists(p) or os.path.getsize(p) == 0:
            return []
        return [[n, t, c] for b in ep.parse_file(p) for n, t, c in b['codes']]

    json.dump({h: {'cls': info[h.lower()]['cls'], 'pos': info[h.lower()]['pos'],
                   'tree': info[h.lower()]['tree'], 'codes': info[h.lower()]['codes'],
                   'nodes': nodes_of(h)}
               for h in heads if info[h.lower()]['tree'] or info[h.lower()]['cls'] != 'unknown'},
              io.open(os.path.join(HERE, 'etym_trees.json'), 'w', encoding='utf-8'),
              ensure_ascii=False, indent=0)
    print('\n-> etym_class.json / etym_trees.json 已写出')


if __name__ == '__main__':
    main()
