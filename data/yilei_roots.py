# -*- coding: utf-8 -*-
"""义类 ↔ 词根对照表（产品内核）。

从 analyze_roots.py 里抽出来单独成模块，让统计脚本与卡片生产流水线共用同一份表，
避免两处各写一份、改了这边忘了那边。

两张表：
    ROOTS  义类 → 该义类下的英语词根（古典语源，多为拉丁/希腊）
    PREFIX / SUFFIX  判断一个词是不是古典语源的辅助信号
"""
import re

# ---- 义类 → 词根 ----
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


def _norm(s):
    """把祖先词条归一化，便于比对：去变音符号以外的噪声、小写。"""
    s = (s or '').lower().strip()
    s = re.sub(r'^[\*\-]+', '', s)          # 去掉构拟标记 * 与连接符
    s = re.sub(r'[^a-z]', '', s)            # 只留字母（希腊/拉丁转写里常有 ʰ ʷ 等）
    return s


def match_roots(terms, min_len=3):
    """在一组词条（现代词 + 词源祖先）里找义类词根。

    返回 [(义类, 词根, 命中的词条)]，按 ROOTS 表序、去重。
    命中要求词根是某个词条的**子串**，且词根长度 >= min_len。
    注意：这是**候选**，不是结论 —— 短词根（如 am / ag / par）歧义很大，
    必须经人工复核才可入卡。
    """
    normed = [(t, _norm(t)) for t in terms if t]
    out, seen = [], set()
    for cls, roots in ROOTS.items():
        for r in roots:
            if len(r) < min_len:
                continue
            for orig, n in normed:
                if r in n:
                    key = (cls, r)
                    if key not in seen:
                        seen.add(key)
                        out.append((cls, r, orig))
                    break
    return out


def match_affix(word):
    """判断现代词本身带不带古典前缀/后缀。返回 (前缀, 后缀)。"""
    w = _norm(word)
    p = next((p for p in PREFIX if w.startswith(p) and len(w) > len(p) + 2), None)
    s = next((s for s in SUFFIX if w.endswith(s) and len(w) > len(s) + 2), None)
    return p, s