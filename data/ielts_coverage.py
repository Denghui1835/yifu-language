# -*- coding: utf-8 -*-
"""
雅思词表的义符覆盖率实测。

复用高考词表那条管线（fetch_raw 抓 kaikki → etym_parse 解析 →
analyze_etym 的判定函数），只换词表。用来回答一个问题：
**扩到雅思词汇后，可挂古典词根的比例是升还是降？**

预期是升 —— 雅思词更长更学术，拉丁/希腊来源占比应高于高考词表
（高考 7-9 字母才 62.9%）。

用法：
  python ielts_coverage.py             # 全量
  python ielts_coverage.py 100         # 试跑前 100
"""
import io, json, os, re, sys, collections

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import etym_parse as ep
import analyze_etym as A          # 复用判定逻辑，不重写

SRC_TXT = os.path.join(HERE, 'ielts_raw.txt')      # 雅思词汇真经（词|词性|释义|例句）
LIST = os.path.join(HERE, 'ielts_words.json')
RAW = os.path.join(HERE, 'etym_raw_ielts')
CLASS = os.path.join(HERE, 'ielts_class.json')
TREES = os.path.join(HERE, 'ielts_trees.json')


def parse_list():
    """雅思词汇真经：word|pos.|释义|例句，夹杂话题标题与 +++/--- 分隔符"""
    if os.path.exists(LIST):
        return json.load(io.open(LIST, encoding='utf-8'))
    d = io.open(SRC_TXT, encoding='utf-8').read()
    rows, topic = [], ''
    for l in d.split('\n'):
        l = l.strip()
        if not l or l in ('+++', '---'):
            continue
        if '|' not in l:
            topic = l                     # 话题标题行（自然地理、学校教育…）
            continue
        p = l.split('|')
        if len(p) < 3 or not re.match(r"^[A-Za-z][A-Za-z \-'\.]*$", p[0]):
            continue
        hw = p[0].strip()
        rows.append({'hw': hw, 'pos': p[1].strip(), 'def': p[2].strip(),
                     'ex': (p[3].strip() if len(p) > 3 else ''), 'topic': topic,
                     'kind': 'phrase' if ' ' in hw else 'word'})
    seen, out = set(), []
    for r in rows:
        k = r['hw'].lower()
        if k in seen:
            continue
        seen.add(k)
        out.append(r)
    json.dump(out, io.open(LIST, 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
    return out


def key_of(hw):
    return re.sub(r'[^\w\-]', '_', hw.lower())


def main():
    recs = parse_list()
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else len(recs)
    print('雅思词表 %d 词（前 %d 参与本次）' % (len(recs), limit))

    # ---- 抓词源：复用 fetch_raw 的抓取与缓存，只换目录 ----
    import fetch_raw as F
    F.OUTDIR = RAW
    os.makedirs(RAW, exist_ok=True)
    heads = [r['hw'] for r in recs][:limit]
    from concurrent.futures import ThreadPoolExecutor, as_completed
    todo = [h for h in heads if not os.path.exists(os.path.join(RAW, key_of(h) + '.html'))]
    print('待抓 %d' % len(todo))
    if todo:
        with ThreadPoolExecutor(max_workers=F.WORKERS) as ex:
            for _ in as_completed([ex.submit(F.one, h) for h in todo]):
                pass

    # ---- 判定：走 analyze_etym 的那套口径 ----
    info = {}
    for h in heads:
        p = os.path.join(RAW, key_of(h) + '.html')
        if not os.path.exists(p) or os.path.getsize(p) == 0:
            info[h.lower()] = {'cls': 'unknown', 'codes': [], 'tree': '', 'tpl': ''}
            continue
        bs = ep.parse_file(p)
        codes = A.codes_of(bs)
        fam = A.fam_of(codes) or A.prose_fam(bs)
        prim = ep.primary(bs)
        info[h.lower()] = {'cls': fam or 'unknown', 'codes': sorted(codes),
                           'tree': (prim or {}).get('tree', ''),
                           'tpl': ' || '.join(b['tpl'][:400] for b in bs)[:1200]}

    for _ in range(4):                     # 派生回退，同 analyze_etym
        changed = 0
        for h in heads:
            d = info[h.lower()]
            if d['cls'] != 'unknown':
                continue
            fams = [info[c]['cls'] for c in A.components(d['tpl'])
                    if c in info and info[c]['cls'] != 'unknown']
            for f in (A.CLASSICAL, A.ROMANIC, A.GERM):
                if f in fams:
                    d['cls'] = f
                    changed += 1
                    break
        if not changed:
            break

    n = len(heads)
    cls = collections.Counter(info[h.lower()]['cls'] for h in heads)
    print('\n=== 雅思词表 %d 词 ===' % n)
    for k, v in cls.most_common():
        print('  %-10s %4d  %5.1f%%' % (k, v, 100.0 * v / n))
    g = cls[A.CLASSICAL] + cls[A.ROMANIC]
    print('  可挂古典词根 = %d = %.1f%%' % (g, 100.0 * g / n))

    print('\n=== 长度分层（对比高考：27.8 / 47.5 / 62.9 / 60.0）===')
    for lo, hi in ((1, 3), (4, 6), (7, 9), (10, 99)):
        sub = [h for h in heads if lo <= len(re.sub(r'[^A-Za-z]', '', h)) <= hi]
        if not sub:
            continue
        gg = sum(1 for h in sub if info[h.lower()]['cls'] in (A.CLASSICAL, A.ROMANIC))
        print('  %2d-%2d 字母: %4d 词, 可挂古典词根 %5.1f%%' % (lo, hi, len(sub), 100.0 * gg / len(sub)))

    json.dump({h: info[h.lower()]['cls'] for h in heads},
              io.open(CLASS, 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
    json.dump({h: {'cls': info[h.lower()]['cls'], 'tree': info[h.lower()]['tree'],
                   'codes': info[h.lower()]['codes']} for h in heads},
              io.open(TREES, 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
    print('\n-> ielts_class.json / ielts_trees.json 已写出')


if __name__ == '__main__':
    main()