# -*- coding: utf-8 -*-
"""
把高考词按义类分桶，回答「每个义类覆盖多少词」。

★ 第一版直接用子串匹配，结果全是假阳性：
    arrive 命中 水(riv)、average 命中 真(ver)、ceiling 命中 言(ling)。
  三个字母的词根在无关词里到处都是。加两条约束后干净多了：
    (1) 词素边界：词根要么在词首，要么它前面那段本身是已知词根/前缀
        -> adopt(ad+opt) 收，arrive(ar+riv) 拒
    (2) 祖先词素：词根本身出现在拉丁/希腊祖先词里也算
        -> biography 的 graph 出现在 Latin graphia 里

只在**已确认源自拉丁/希腊**的词上分桶 —— 日耳曼底层词没古典词根，
算进来只会稀释。这是启发式统计，不是逐词人工判定，文档里要这么说。
"""
import io, json, os, re, sys, collections, unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))

# ★ 只用「真前缀」。第一版塞了 ac/af/ag/al/an/ap/ar/as/at 这些两字母组合，
#   结果什么词都能被"合法分词"：average 的 av、arrive 的 ar 全过了，全是假阳性。
#   现在：三字母及以上的前缀一律认；两字母只认下面这几个不会看错的。
PREFIX_LONG = set("""
abs circum col com con cor contra counter dis extra inter intro intra non
post pre pro retro semi sub suc suf sug sup sur super trans ultra
ambi amphi ana anti auto cata dia epi eu hyper hypo meta para peri
syn sym syl uni vice
""".split())
PREFIX_SHORT = {'ad', 'ab', 'ex', 'de', 'in', 're', 'un', 'ob', 'se', 'bi', 'co'}
# co/bi 太弱（cover、bike 会被误切），只在词根≥4 时才允许
PREFIX_WEAK = {'co', 'bi'}
PREFIX = PREFIX_LONG | PREFIX_SHORT


sys.path.insert(0, HERE)

# ★ 义类词根表直接 import，**不再从 analyze_roots.py 的源码文本里抠**。
#   那套写法（读 .py 文本 → 找 `ROOTS = {` → exec 切片）在 ROOTS 被抽到
#   yilei_roots.py 之后就失效了：src.find('ROOTS = {') 返回 -1，切片成空串，
#   exec('') 得到空命名空间，于是 ns['ROOTS'] 抛 KeyError —— 整个脚本跑不起来，
#   连带 yilei_buckets.json 也再没法重新生成。
#   yilei_roots.py 的注释自己写了这个模块就是为了「让统计脚本与卡片生产流水线
#   共用同一份表」，当初只是这里没跟着改。
from yilei_roots import ROOTS  # noqa: E402


def load_roots():
    """返回义类词根表。

    保留函数名是为了不动 main() 里的调用点；实现改成直接拿 import 进来的那一份。
    """
    return ROOTS


CLASSICAL = {'la', 'la-lat', 'la-med', 'la-new', 'la-vul', 'la-ecc', 'la-ren',
             'la-cla', 'la-ine', 'LL', 'NL', 'ML', 'grc', 'grc-koi', 'grc-att',
             'grc-dor', 'grc-hom', 'grc-pie', 'grc-hel', 'gkm', 'el'}


def norm(s):
    s = unicodedata.normalize('NFKD', s)
    s = ''.join(c for c in s if not unicodedata.combining(c))
    return re.sub(r'[^a-z]', '', s.lower())


def _at_boundary(rn, a):
    """词根 rn 是否在词 a 里落在词素边界上（词首，或强前缀之后）"""
    if a.startswith(rn):
        return True
    for L in (3, 4, 5, 6, 7):
        if L >= len(a):
            break
        if a.startswith(rn, L) and (a[:L] in PREFIX_LONG or a[:L] in ALLROOTS):
            return True
    return False


def match(rn, n, anc):
    """词根 rn 是否可信地出现在词 n 里。
    ★ 收紧过：第一版只要词里含这个词根就算，于是
      parrot(rot)、tortoise(tort)、course(cour)、country(count)、medal(med)
      全被收进来了。现在只认三种位置：
        (1) 拉丁/希腊祖先词里的词素边界 —— 最可信
        (2) 英语词的词首
        (3) 英语词中，且前面那段是三字母以上的真前缀
    """
    if len(rn) >= 3:
        for a in anc:
            if _at_boundary(rn, a):
                return '祖先'
    if n.startswith(rn):
        return '词首'
    for L in (3, 4, 5, 6, 7):
        if L >= len(n):
            break
        if n.startswith(rn, L) and n[:L] in PREFIX_LONG:
            return '前缀'
    return None


ALLROOTS = set()


def main():
    roots = load_roots()
    cls = json.load(io.open(os.path.join(HERE, 'etym_class.json'), encoding='utf-8'))
    trees = json.load(io.open(os.path.join(HERE, 'etym_trees.json'), encoding='utf-8'))

    # 所有词根归一化后的集合，用来判断「词根前面那段是不是也是个词素」
    global ALLROOTS
    ALLROOTS = {norm(r) for v in roots.values() for r in v if len(norm(r)) >= 3}

    hit = collections.defaultdict(list)
    unmatched = []
    skipped = 0
    for w, c in cls.items():
        if c in ('germanic', 'other', 'unknown'):
            skipped += 1
            continue
        n = norm(w)
        # 只取拉丁/希腊祖先词素 —— 混进中古英语词素会让 ceiling 命中 celing 里的 ling
        # ★ 剔除自环节点：kaikki 有时把词本身也列成祖先（college 的祖先里就有
        #   "college"），于是 leg 在"祖先"里匹配上自己，纯属循环论证。
        anc = [a for a in (norm(nd[1]) for nd in trees.get(w, {}).get('nodes', [])
                           if len(nd) > 2 and nd[2] in CLASSICAL
                           and nd[1] and not nd[1].startswith('*'))
               if a and a != n and len(a) > len(n)]

        best = None
        for y, rs in roots.items():
            for r in rs:
                rn = norm(r)
                if len(rn) < 3:
                    continue
                where = match(rn, n, anc)
                if where:
                    if best is None or len(rn) > best[1]:
                        best = (y, len(rn), r, where)
                    break
        if best:
            hit[best[0]].append((w, best[2], best[3]))
        else:
            unmatched.append(w)

    total = sum(len(v) for v in hit.values())
    print('=== 义类分桶（只在可挂古典词根的词上算）===')
    print('归入义类 %d 词 / 没匹配上 %d 词 / 日耳曼等未参与 %d 词'
          % (total, len(unmatched), skipped))
    print()
    print('%-6s %5s  %s' % ('义类', '词数', '例词'))
    for y, ws in sorted(hit.items(), key=lambda kv: -len(kv[1])):
        ex = '  '.join('%s(%s)' % (w, r) for w, r, _ in ws[:6])
        print('%-6s %5d  %s' % (y, len(ws), ex))

    json.dump({y: [w for w, _, _ in ws] for y, ws in hit.items()},
              io.open(os.path.join(HERE, 'yilei_buckets.json'), 'w', encoding='utf-8'),
              ensure_ascii=False, indent=0)
    print('\n-> yilei_buckets.json 已写出')


if __name__ == '__main__':
    main()
