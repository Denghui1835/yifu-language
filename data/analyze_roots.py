# -*- coding: utf-8 -*-
"""统计高考3500词里有多少能挂上拉丁/希腊词根。
v2：修正 v1 的假阳性（e→ex、补 ad- 同化形式），并把词根表扩到可用规模。"""
import json, re, io, sys, collections
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

W = json.load(open(r'D:\AI coding\义符\data\gaokao3500.json', encoding='utf-8'))
words = [e['w'].lower().strip() for e in W]
words = [w for w in words if re.fullmatch(r"[a-z][a-z'\- ]*", w)]
print('总词条:', len(words))

# ---- 前缀：只留可靠信号（去掉裸 e/di/in/co 这类高噪声的，补 ad- 同化形式）----
PREFIX = [
    'ab','abs','ad','ac','af','ag','al','ap','ar','as','at','ambi','ante','anti',
    'auto','bene','bi','circum','com','con','contra','counter','de','dis','ex','extra',
    'hyper','hypo','il','im','inter','intra','intro','ir','macro','mal','meta','micro',
    'mis','mono','multi','non','ob','oc','of','op','omni','para','per','peri','poly',
    'post','pre','pro','retro','semi','sub','suc','suf','sup','sur','sus','super',
    'syn','sym','tele','trans','tri','ultra','uni','vice',
]
# ---- 后缀：比较可靠的外来语信号（-tion/-ment/-ous 极少出现在日耳曼词里）----
SUFFIX = [
    'able','ible','acy','age','ance','ancy','ant','ary','ate','ation','ative',
    'ence','ency','ent','eous','fy','ic','ical','ify','ion','ise','ism','ist',
    'ite','itis','ity','ive','ize','logy','graphy','sion','tion','tious','ture',
    'tude','ure','ous','meter','scope','phobia','aceous',
]

# ---- 义类词根表（产品内核；按义类组织，一个义类可挂多个词根）----
ROOTS = {
 '水':['aqua','aqu','hydr','marin','maritim','flu','fluct','riv','und'],
 '手':['manu','mani','chir','chiro'],
 '心':['cord','cour','psych','path','card','anim'],
 '走':['ceed','cede','cess','gress','grad','vad','vas','itiner','ambul','curr','curs'],
 '言':['loqu','locut','dict','ling','lingu','logu','logue','nunc','nunci','verb','claim','clam'],
 '生':['bio','viv','vit','gen','nat'],
 '火':['ign','photo','pyr','flam','ferv'],
 '土':['terr','geo','hum','agr'],
 '石':['lith','petr','sax'],
 '大':['magn','maxi','macro','grand'],
 '小':['micro','minim','minut'],
 '看':['vid','vis','spec','spect','opt','ocul'],
 '听':['aud','son','phon'],
 '写':['scrib','script','graph','gram'],
 '拿':['cap','cept','cip','tain','tent','hab','hibit'],
 '送':['mit','miss','port','fer','vect'],
 '放':['pos','pon','posit','thes','thet'],
 '转':['vert','vers','tort','tors','volv','volut','rot'],
 '拉':['tract','trah','string','strict'],
 '建':['struct','stru','text'],
 '投':['ject','jac'],
 '引':['duc','duct','voy'],
 '数':['numer','count','calcul'],
 '时':['chron','temp','ann','enn','ev'],
 '人':['anthrop','dem','popul','homin','civ'],
 '力':['dyn','fort','val','pot','robor'],
 '光':['luc','lum','clar','splend','radi'],
 '声':['phon','son','aud'],
 '生命':['viv','vit','bio'],
 '死亡':['mort','necr','cad','cas'],
 '爱':['am','amor','phil','dilect'],
 '恨':['odium','phob'],
 '知':['sci','cogn','gnos','not','sap','soph'],
 '信':['cred','fid','feder'],
 '说':['dict','loqu','nunc','fab'],
 '做':['fact','fect','fic','oper','ag'],
 '给':['dat','don','trib','dit'],
 '取':['cap','cept','sum','sumpt','empt'],
 '见':['vid','vis','spec'],
 '名':['nomin','onym','nomen'],
 '钱':['pecun','monet','fisc','valu'],
 '法':['leg','jur','just','lic'],
 '国':['natio','patri','reg','civ'],
 '战':['bell','pugn','milit','belli','fend','fens'],
 '医':['med','iatr','san','cur'],
 '教':['doc','disc','ped','magist'],
 '形':['form','morph','fig'],
 '动':['mot','mov','mob','ag','act'],
 '变':['mut','vers','form'],
 '多':['multi','poly','plur'],
 '同':['equ','simil','par'],
 '远':['tele','long','procul'],
 '真':['ver','fid','cert'],
 '手写':['scrib','script','chiro'],
}

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
