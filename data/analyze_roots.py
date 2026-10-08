# -*- coding: utf-8 -*-
"""统计高考词表里有多少词能挂上拉丁/希腊词根（用 yilei_roots.py 的 ROOTS 表）。

v2：修正 v1 的假阳性（e→ex、补 ad- 同化形式），并把词根表扩到可用规模。
v3：① 词根表已抽到 yilei_roots.py，本文件改为 import，不再自带一份；
    ② 统计键改用 hw（查词键），不再用 w（显示串）；
    ③ 去掉已宣布作废的「N 字母以上累计占比」，不再写进 coverage.json；
    ④ 路径不再硬编码，跟随文件位置。

⚠️ 本脚本是**启发式子串匹配**——只问"词根是否作为子串出现在这个词里"，
   短词根噪音率很高（见下方样本）。**它不是结论，只是粗口径参考。**
   权威口径在别处：
     · 词源定性覆盖率          -> data/etym_class.json（analyze_etym.py 产出，README 已公布）
     · 按义类分桶（带词素边界约束）-> data/yilei_buckets.json（bucket_yilei.py 产出）
     · 长度分层                 -> README「长度分层」表（同样出自 analyze_etym.py）

用法：
    python data/analyze_roots.py     # 打印覆盖率报告，并写出 data/coverage.json
"""
import io
import json
import os
import random
import sys
import collections

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from yilei_roots import PREFIX, SUFFIX, ROOTS  # noqa: E402


def hit_prefix(w):
    for p in PREFIX:
        if w.startswith(p) and len(w) > len(p) + 2:
            return p
    return None


def hit_suffix(w):
    for s in SUFFIX:
        if w.endswith(s) and len(w) > len(s) + 2:
            return s
    return None


def hit_root(w):
    for cls, roots in ROOTS.items():
        for r in roots:
            if r in w and len(r) >= 3:
                return (cls, r)
    return None


def load_words():
    """词表里的**查词键**。

    ★ 用 hw，不用 w。w 是显示串，**故意保留源件的括号注记**
      （`arise (arose, arisen)`、`bad (worse, worst)`，共 169 条），
      拿它统计会平白丢掉 196 条，总数只剩 3645 —— 和真实的 3841 对不上，
      正是这条以前把 coverage.json 写歪的原因。字段约定见 data/check_data.py。
    """
    recs = json.load(io.open(os.path.join(HERE, 'gaokao3500.json'), encoding='utf-8'))
    return sorted(set(str(r['hw']).lower().strip() for r in recs if r.get('hw')))


def main():
    # Windows 控制台默认 GBK，中文报告会变乱码
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

    words = load_words()
    print('总词条:', len(words))

    P = {w: hit_prefix(w) for w in words}
    S = {w: hit_suffix(w) for w in words}
    R = {w: hit_root(w) for w in words}

    nP = sum(1 for v in P.values() if v)
    nS = sum(1 for v in S.values() if v)
    nR = sum(1 for v in R.values() if v)
    nPS = sum(1 for w in words if P[w] or S[w])
    union = set(w for w in words if P[w] or S[w]) | set(w for w in words if R[w])
    rest = [w for w in words if w not in union]

    print(f'  带拉丁/希腊前缀 : {nP:5d}  ({nP/len(words)*100:.1f}%)')
    print(f'  带拉丁/希腊后缀 : {nS:5d}  ({nS/len(words)*100:.1f}%)')
    print(f'  前缀或后缀      : {nPS:5d}  ({nPS/len(words)*100:.1f}%)')
    print(f'  命中义类词根    : {nR:5d}  ({nR/len(words)*100:.1f}%)')
    print(f'★ 并集(可归入义类) : {len(union):5d}  ({len(union)/len(words)*100:.1f}%)')
    print(f'★ 挂不上(基础/日耳曼): {len(rest):5d}  ({len(rest)/len(words)*100:.1f}%)')

    print('\n--- 各义类覆盖词数 ---')
    cnt = collections.Counter(R[w][0] for w in words if R[w])
    for k, v in cnt.most_common(20):
        print(f'  {k}: {v}')

    print('\n--- 挂不上的样本（前 80）---')
    print(' '.join(rest[:80]))
    print('\n--- 校验：随机抽 25 个"挂不上"的，人工看看有没有冤枉 ---')
    random.seed(7)
    print(' '.join(random.sample(rest, min(25, len(rest)))))

    out = {
        'note': ('analyze_roots.py 的启发式词根子串匹配覆盖率 —— 粗口径，仅供参考，'
                 '不得直接引用为结论。词源定性的权威口径见 etym_class.json；'
                 '按义类分桶的权威口径见 yilei_buckets.json。'),
        'source': 'gaokao3500.json',
        'key': 'hw',
        'total': len(words),
        'prefix': nP,
        'suffix': nS,
        'prefix_or_suffix': nPS,
        'root': nR,
        'union': len(union),
        'rest': len(rest),
    }
    dst = os.path.join(HERE, 'coverage.json')
    json.dump(out, io.open(dst, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('\n-> coverage.json 已写出（total=%d）' % len(words))


if __name__ == '__main__':
    main()