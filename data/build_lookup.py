# -*- coding: utf-8 -*-
"""义符 · 浏览器查词库构建器

把仓库里的真数据压成前端可直接用的 docs/data/lookup.json：

    词源树（etym_trees / ielts_trees）
      → 拆成祖先链 [(语种码, 中文语种名, 词条)]
      → 拿现代词 + 全部祖先词条去撞义类词根表
      → 得到义类【候选】

输出的每一层都保留"这是机器候选还是人工校订"的标记：
    reviewed=true   该词有手写教学卡（当前 30 词 / 3 义类），可直接进成品
    reviewed=false  机器抽出的词源链与义类候选，**卡上必须标"待复核"**

这条分界不是装饰。评审看的正是"哪些是查证过的、哪些还没"。
"""
import io, os, re, json, datetime

from etym_parse import LANG_CODE_EN, LANG_NAME
from yilei_roots import ROOTS, match_roots, match_affix

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, '..', 'docs', 'data', 'lookup.json')

# 尾部关系标签：kaikki 把 "der./bor./inh." 渲染在词条后面，得清掉
REL_TAIL = re.compile(r'(?:der|inh|bor|derived|inherited|borrowed|calque)\.?$')


def clean_term(t):
    t = (t or '').strip()
    t = REL_TAIL.sub('', t).strip()
    t = t.rstrip('?').strip()
    return '' if t in ('-', '—', '') else t


def parse_tree_text(tree):
    """kaikki 渲染好的演变树文本 → [(语种码, 中文语种名, 词条)]。

    每行形如 "Proto-Indo-European *h₂éd" 或 "Latin aqua"。
    取最后一个空格切成 (语种名, 词条)。
    """
    out = []
    for line in (tree or '').split('\n'):
        line = line.strip()
        if not line or ' ' not in line:
            continue
        name, term = line.rsplit(' ', 1)
        term = clean_term(term)
        if not term:
            continue
        name = name.strip()
        code = LANG_CODE_EN.get(name, '')
        zh = LANG_NAME.get(code, name)
        out.append([code, zh, term])
    return out


def load_json(fn):
    p = os.path.join(HERE, fn)
    if not os.path.exists(p):
        return None
    return json.load(io.open(p, encoding='utf-8'))


def candidates_for(w, chain, cls):
    """义类候选。三条口径，都是踩过坑才定下来的：

    1. **词根必须出现在现代词形里**（不是"出现在某个祖先词条里"）。
       第一版拿全部祖先去撞，`abnormal` 撞出「火」、`academic` 撞出「人、死亡」——
       子串匹配在 2281 词的规模上批量生产错误，比不给候选更糟。
       对学习者来说，词根本身要看得见才有用，藏在三层拉丁语后面的不算。
    2. **长度 >= 4**。3 字母词根（don/par/und/dem/cad）在英语里到处都是子串，
       实测 `London→给←don`、`Sunday→水←und` 全是假阳性。
       代价是漏掉 emancipate（man 只有 3 字母）这类——它们由已复核的手写卡覆盖。
    3. 试过"词根须同时出现在词源链里"作佐证，**弃用**：既漏掉 biology→生←bio
       这种显然正确的（该词链为空），又拦不住 London。两头不讨好。

    另：专有名词与日耳曼源词不出候选。前者因为学习者不会把它当词根练；
    后者因为义符法对接的是拉丁/希腊词根，对日耳曼词本就不适用 —— 页面如实标明。
    """
    if cls == 'germanic' or not w.islower() or '-' in w or ' ' in w:
        return []
    return [{'yilei': cls_, 'root': r, 'hit': hit}
            for cls_, r, hit in match_roots([w], min_len=4)]


def main():
    # ---- 词表：音标 + 释义 + 词性 ----
    meta = {}
    for row in (load_json('gaokao3500.json') or []):
        w = row.get('w') or row.get('hw')
        if not w:
            continue
        meta.setdefault(w, {}).update(
            {'ipa': row.get('ipa', ''), 'def': row.get('def', ''), 'src': 'gaokao3500'})
    for row in (load_json('ielts_words.json') or []):
        w = row.get('hw')
        if not w:
            continue
        m = meta.setdefault(w, {})
        m['def'] = m.get('def') or row.get('def', '')
        m['pos'] = row.get('pos', '')
        m['ex'] = row.get('ex', '')
        m['topic'] = row.get('topic', '')
        m['src'] = (m.get('src', '') + '+ielts') if m.get('src') else 'ielts'

    # ---- 词源树：两表合并，取信息更全的那份 ----
    trees = {}
    for fn, tag in (('etym_trees.json', 'gaokao'), ('ielts_trees.json', 'ielts')):
        d = load_json(fn) or {}
        for w, v in d.items():
            old = trees.get(w)
            # 谁的 tree 更长用谁；cls 不是 unknown 的优先
            score = len(v.get('tree') or '') + (100 if v.get('cls') not in (None, 'unknown') else 0)
            if old is None or score > old['_score']:
                trees[w] = {'cls': v.get('cls') or 'unknown',
                            'pos': v.get('pos', ''),
                            'chain': parse_tree_text(v.get('tree')),
                            '_score': score, 'tag': tag}

    # ---- 组装 ----
    # ---- 已复核的手写词：从 index.html 的 DATA 里取 ----
    reviewed_words = set()
    idx = os.path.join(HERE, '..', 'docs', 'index.html')
    if os.path.exists(idx):
        s = io.open(idx, encoding='utf-8', errors='replace').read()
        reviewed_words = set(re.findall(r"\{w:'([^']+)'", s))

    words = {}
    for w, t in trees.items():
        m = meta.get(w, {})
        chain = t['chain']
        pre, suf = match_affix(w)
        yilei = candidates_for(w, chain, t['cls'])
        rec = {
            'def': m.get('def', ''),
            'ipa': m.get('ipa', ''),
            'pos': t.get('pos') or m.get('pos', ''),
            'cls': t['cls'],
            'chain': chain,
            'yilei': yilei,
            'af': [pre or '', suf or ''],
            'tag': t['tag'],
            'reviewed': w in reviewed_words,
        }
        if yilei or chain or w in reviewed_words:
            words[w] = rec

    # ---- 义类表：词根（全部 54 类）+ 汉语义符（仅人工校订过的）----
    yilei_tbl = {}
    for cls, roots in ROOTS.items():
        yilei_tbl[cls] = {'roots': roots, 'fu': [], 'reviewed': False}

    # 汉语义符从 index.html 的 DATA 里取（那份是手写的、已复核）
    idx = os.path.join(HERE, '..', 'docs', 'index.html')
    if os.path.exists(idx):
        s = io.open(idx, encoding='utf-8', errors='replace').read()
        for m in re.finditer(r"name:'([^']+)'[\s\S]{0,600}?fu:\[([\s\S]*?)\]", s):
            name, block = m.group(1), m.group(2)
            fus = []
            for fm in re.finditer(r"\{ch:'([^']*)',\s*from:'([^']*)',\s*note:'([^']*)'", block):
                fus.append({'ch': fm.group(1), 'from': fm.group(2), 'note': fm.group(3)})
            if fus and name in yilei_tbl:
                yilei_tbl[name]['fu'] = fus
                yilei_tbl[name]['reviewed'] = True

    os.makedirs(os.path.dirname(os.path.abspath(OUT)), exist_ok=True)
    json.dump({
        'schema': 1,
        'built': datetime.date.today().isoformat(),
        'note': 'reviewed=false 的词条是机器从 kaikki 词源抽出的候选，'
                '未经人工复核，页面上必须标"待复核"，不得当作结论呈现。',
        'stats': {'words': len(words),
                  'with_chain': sum(1 for v in words.values() if v['chain']),
                  'with_yilei': sum(1 for v in words.values() if v['yilei']),
                  'yilei': len(yilei_tbl),
                  'fu_reviewed': sum(1 for v in yilei_tbl.values() if v['reviewed']),
                  'reviewed_words': len(reviewed_words)},
        'yilei': yilei_tbl,
        'words': words,
    }, io.open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))

    st = json.load(io.open(OUT, encoding='utf-8'))['stats']
    L = ['写入 %s  (%.2f MB)' % (OUT, os.path.getsize(OUT) / 1048576.0), '']
    for k, v in st.items():
        L.append('%-14s %s' % (k, v))
    L.append('')
    L.append('样例（前 8 个有义类候选的词）:')
    n = 0
    for w, v in words.items():
        if not v['yilei']:
            continue
        L.append('  %-14s %-10s 候选=%s  链=%d段  %s'
                 % (w, v['cls'], '、'.join(x['yilei'] for x in v['yilei']),
                    len(v['chain']), v['def'][:22]))
        n += 1
        if n >= 8:
            break
    io.open(os.path.join(HERE, '_lookup_out.txt'), 'w', encoding='utf-8').write('\n'.join(L))


if __name__ == '__main__':
    main()