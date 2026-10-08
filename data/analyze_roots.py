# -*- coding: utf-8 -*-
"""统计高考3500词里有多少能挂上拉丁/希腊词根。
v2：修正 v1 的假阳性（e→ex、补 ad- 同化形式），并把词根表扩到可用规模。"""
import json, re, io, sys, collections
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

W = json.load(open(r'D:\AI coding\义符\data\gaokao3500.json', encoding='utf-8'))
words = [e['w'].lower().strip() for e in W]
words = [w for w in words if re.fullmatch(r"[a-z][a-z'\- ]*", w)]
print('总词条:', len(words))

# ---- 义类词根表已抽到 yilei_roots.py（与卡片生产流水线共用同一份）----
from yilei_roots import PREFIX, SUFFIX, ROOTS

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
import random; random.seed(7)
print(' '.join(random.sample(rest, min(25, len(rest)))))

out = {'total': len(words), 'prefix': nP, 'suffix': nS,
       'prefix_or_suffix': nPS, 'root': nR, 'union': len(union), 'rest': len(rest)}
json.dump(out, open(r'D:\AI coding\义符\data\coverage.json', 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)

# ---- 关键假设检验：难词是否恰好是词根词？----
import statistics as st
print('\n===== 长度分层：难词是否恰好可挂根 =====')
print('可挂根词  平均长度 %.2f' % st.mean(len(x) for x in union))
print('挂不上词  平均长度 %.2f' % st.mean(len(x) for x in rest))
print()
for n in (4,5,6,7,8,9,10,11):
    a=sum(1 for x in words if len(x)>=n and x in union)
    b=sum(1 for x in words if len(x)>=n and x not in union)
    if a+b: print('%2d 字母以上: 可挂根 %4d / 不可 %4d → 可挂根占 %.0f%%' % (n,a,b,100*a/(a+b)))
