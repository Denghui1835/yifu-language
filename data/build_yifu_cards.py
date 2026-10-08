# -*- coding: utf-8 -*-
r"""义符 · 卡片内容层生成器 —— 由 docs/index.html 的 const DATA 产出 data/yifu_cards.json

用法：
    python data/build_yifu_cards.py          # 重新生成 data/yifu_cards.json
    python data/build_yifu_cards.py --check  # 只校验仓库里那份与 index.html 是否还一致

为什么要有这个脚本
------------------
`data/yifu_cards.json` 当初是一段**没入库的一次性 node 脚本**产出的（PR #24）。
产物进了仓库、生成方式没进 —— 于是没人能重跑它、没人能复核它，
`docs/index.html` 的 `const DATA` 一改，这份文件就会**静默漂移**。

本脚本把它变成可重现的产物：
  * 纯标准库，不引 node、不新增依赖；
  * `const DATA` 是 JS 对象字面量（单引号串、无引号键、允许尾逗号），
    下面自带一个够用的字面量解析器；
  * `--check` 是防漂移闸门 —— 与 PR #23 在 README 里补的「产物必须跟着生成器走」是同一条规矩。

产物与生成器的边界
------------------
词条正文（w / ipa / root / mean / parts / result / hz / story / rel / yilei 各节）
**逐字来自 `docs/index.html`，本脚本一个字都不改**。
本脚本只**附加**三样仓库里别处没有的东西：
  * `provenance` —— 每词的词源出处与复核状态；
  * `review`     —— 义类归属与汉语侧的复核状态（拿不准一律 pending，不猜）；
  * `known_issues` —— 汉语侧已发现但未裁决的问题（`KNOWN` 表）。
`KNOWN` 与 `EN_NOTE` 两张表是**内容来源**，所以随脚本一起入库 —— 它们原先只存在于作者本机。
"""
import io, os, re, sys, json, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, '..', 'docs', 'index.html')
OUT = os.path.join(HERE, 'yifu_cards.json')

EN_AUDIT = 'data/demo_etym_audit.md'
ZH_NOTE = ('字形构成照字面列出，未引《说文》等字源文献逐字求证 —— '
           '见 data/demo_etym_audit.md 末节与 known_issues')

NOTE = ('义符卡内容层。字段结构照 docs/index.html 的 const DATA（阶段零演示 30 词），'
        '词条内容逐字取自该文件，未改写。每词带 provenance 指向词源出处；'
        '拿不准的字段按 Issue #1 的要求标 pending，不猜。'
        '生成方式：python data/build_yifu_cards.py（把 index.html 里 DATA 对象字面量解析成 JSON，'
        '再补 provenance 与 review 两节 —— 词条正文一字未动）；'
        '跑 python data/build_yifu_cards.py --check 可校验本文件与 index.html 是否还一致。')

SOURCES = {
    'demo': 'docs/index.html 的 const DATA（阶段零演示，3 义类 × 10 词）',
    'en_raw': 'data/etym_raw/<词>.html（kaikki.org 抓取切片，每词一个文件）',
    'en_audit': EN_AUDIT + '（30 词英语侧逐条核对，29/30 与维基词典一致，修正 2 处）',
    'zh': 'pending —— 尚无字源文献级出处',
}

# 汉语侧人工复核的发现（参赛工作目录 01_对照测试/复核记录.md，不在本仓库内）
# 乙-1 字形拆解写错 1 处 · 乙-2 拿的字不带该义类的部首 9 处 · 乙-3 表述含混 1 处（非错误）
KNOWN = [
    ('aqueduct', '乙-1', '字形拆解写错', '渠（氵＋矩）', '渠（氵＋巨＋木）',
     '渠的字形是 氵＋巨（声旁）＋木，没有「矩」这个成分'),
    ('aquamarine', '乙-2', '部首不对', '蓝', '海（氵＋每）', '蓝＝艹＋监，无氵；水义类应取氵部的字'),
    ('dehydrate', '乙-2', '部首不对', '干', '涸（氵＋固）', '干无氵；「水干」就叫涸'),
    ('manuscript', '乙-2', '部首不对', '稿', '抄（扌＋少）', '稿＝禾＋高，无扌；手义类应取扌部的字'),
    ('emancipate', '乙-2', '部首不对', '释', '挣（扌＋争）', '释无扌'),
    ('chirography', '乙-2', '部首不对', '迹', '描（扌＋苗）', '迹＝辶＋亦，无扌'),
    ('accord', '乙-2', '部首不对', '契', '恰（忄＋合）', '契无心；心义类应取含心（忄／心）的字'),
    ('discord', '乙-2', '部首不对', '隙', '悖（忄＋孛）', '隙无心'),
    ('concord', '乙-2', '部首不对', '和', '怡（忄＋台）', '和＝禾＋口，无心'),
    ('psychiatrist', '乙-2', '部首不对', '疗', '愈（俞＋心）',
     '疗＝疒＋了，是病字旁（属「医」义类，不属「心」）；心组六张里只有它带疒，平行关系断在这里'),
    ('submarine', '乙-3', '表述含混（非错误）', '潜（氵＋替的声符）', '潜（氵＋替）', '没说清是什么'),
]
KNOWN_BY_W = dict((k[0], k) for k in KNOWN)

# 英语侧经过修正的词（demo_etym_audit.md 的「修正 1 / 修正 2」）
EN_NOTE = {
    'maritime': '复核修正 1 处：原演示说 maritime「没经过法语」，实为经中古法语'
                '（Borrowed from Middle French maritime）。演示正文已改，本条与 kaikki 一致。',
    'hydrogen': '复核修正 1 处（表述不严）：原演示把氢的希腊词根一律归到「文艺复兴时期」，'
                '已改为「到近代给新发现的东西命名时用希腊词根几乎成了规矩（hydrogen 是 1783 年拉瓦西造的）」。',
    'hydrate': '同 hydrogen，复核修正 1 处（表述不严），演示正文已改。',
}


# ---------------------------------------------------------------- JS 字面量解析
# 只解析 `const DATA = {...}` 用到的那个子集：对象 / 数组 / 单双引号串 / 数字 / true|false|null。
# 不做通用 JS 解析器 —— 够用、可读、出错会当场抛，就够了。

_ESC = {'n': '\n', 't': '\t', 'r': '\r', 'b': '\b', 'f': '\f',
        '/': '/', '\\': '\\', "'": "'", '"': '"', '0': '\0'}


def _skip(s, i):
    while i < len(s):
        if s[i] in ' \t\r\n':
            i += 1
        elif s.startswith('//', i):
            j = s.find('\n', i)
            i = len(s) if j < 0 else j + 1
        elif s.startswith('/*', i):
            j = s.find('*/', i)
            i = len(s) if j < 0 else j + 2
        else:
            break
    return i


def _string(s, i):
    q, i, out = s[i], i + 1, []
    while True:
        if i >= len(s):
            raise ValueError('字面量里的字符串没有收尾引号')
        c = s[i]
        if c == '\\':
            n = s[i + 1]
            if n == 'u':
                out.append(chr(int(s[i + 2:i + 6], 16)))
                i += 6
            else:
                out.append(_ESC.get(n, n))
                i += 2
        elif c == q:
            return ''.join(out), i + 1
        else:
            out.append(c)
            i += 1


def _ident(s, i):
    j = i
    while j < len(s) and (s[j].isalnum() or s[j] in '_$'):
        j += 1
    return s[i:j], j


def _value(s, i):
    i = _skip(s, i)
    if i >= len(s):
        raise ValueError('字面量提前结束')
    c = s[i]
    if c == '{':
        i, out = _skip(s, i + 1), {}
        while True:
            if i >= len(s):
                raise ValueError('对象没有收尾 }')
            if s[i] == '}':
                return out, i + 1
            k, i = _string(s, i) if s[i] in '\'"' else _ident(s, i)
            i = _skip(s, i)
            if s[i] != ':':
                raise ValueError('键 %r 后面不是冒号' % k)
            out[k], i = _value(s, i + 1)
            i = _skip(s, i)
            if s[i] == ',':
                i = _skip(s, i + 1)
    if c == '[':
        i, out = _skip(s, i + 1), []
        while True:
            if i >= len(s):
                raise ValueError('数组没有收尾 ]')
            if s[i] == ']':
                return out, i + 1
            v, i = _value(s, i)
            out.append(v)
            i = _skip(s, i)
            if s[i] == ',':
                i = _skip(s, i + 1)
    if c in '\'"':
        return _string(s, i)
    for lit, val in (('true', True), ('false', False), ('null', None)):
        if s.startswith(lit, i):
            return val, i + len(lit)
    m = re.match(r'-?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?', s[i:])
    if m:
        t = m.group(0)
        return (float(t) if ('.' in t or 'e' in t or 'E' in t) else int(t)), i + len(t)
    raise ValueError('解析不了的字面量: %r' % s[i:i + 40])


def read_data(path=SRC):
    """从 docs/index.html 里取出 `const DATA = {...}` 并解析成 Python 对象。"""
    s = io.open(path, encoding='utf-8').read()
    key = 'const DATA ='
    i = s.find(key)
    if i < 0:
        raise SystemExit('在 %s 里找不到 `%s`' % (path, key))
    data, _ = _value(s, i + len(key))
    return data


# ---------------------------------------------------------------- 组装
def build(data, today):
    yilei, cards = [], []
    for key, blk in data.items():
        yilei.append({'key': key, 'id': blk['id'], 'name': blk['name'], 'sub': blk['sub'],
                      'fu': blk['fu'], 'chars': blk['chars'], 'roots': blk['roots']})
        for c in blk['words']:
            w = c['w']
            prov = {'en': 'data/etym_raw/%s.html' % w, 'en_audit': EN_AUDIT,
                    'en_status': 'reviewed', 'zh': 'pending', 'zh_note': ZH_NOTE}
            if w in EN_NOTE:
                prov['en_note'] = EN_NOTE[w]
            review = {'yilei': 'pending', 'hz': 'pending'}
            if w in KNOWN_BY_W:
                _, tag, kind, old, new, why = KNOWN_BY_W[w]
                review['hz_finding'] = {
                    'tag': tag, 'kind': kind, 'demo_value': old, 'reviewed_value': new, 'why': why,
                    'source': '参赛工作目录 01_对照测试/复核记录.md（不在本仓库内）',
                }
            cards.append({'w': w, 'yilei': blk['name'], 'yilei_key': key,
                          'ipa': c['ipa'], 'root': c['root'], 'mean': c['mean'],
                          'parts': c['parts'], 'result': c['result'],
                          'hz': c['hz'], 'story': c['story'], 'rel': c['rel'],
                          'provenance': prov, 'review': review})
    return {
        'schema': 1,
        'built': today,
        'note': NOTE,
        'sources': SOURCES,
        'yilei': yilei,
        'cards': cards,
        'known_issues': [{
            'scope': '汉语侧（hz 字段），仅覆盖 30 词中的 18 个',
            'what': ('有一轮人工复核对其中 18 个词做过「义类 ↔ 汉语义符部首是否对得上」的检查，'
                     '发现 11 处问题（字形拆解写错 1、部首与义类不符 9、表述含混 1）。'
                     '该轮记录在参赛工作目录 01_对照测试/复核记录.md，**不在本仓库内**。'),
            'why_not_fixed_here': ('本卡的范围是「搬运 + 如实标注」，不改 docs/index.html；'
                                   '且该记录不在仓库里，本文件不宜把它当已入库证据。'
                                   '故 30 词的 hz 一律标 pending，已知的 11 处逐条列在下面，由项目方裁决。'),
            'unreviewed': ('30 词里另有 12 个（aquarium aquatic hydrogen marine manual manufacture '
                           'surgeon manage courage record psychology sympathy）**汉语侧从未被复核过**；'
                           '复核过的那 18 个里就有 9 个部首不对，这 12 个不能假定没问题。'),
            'items': [{'w': k[0], 'tag': k[1], 'kind': k[2], 'demo_value': k[3],
                       'reviewed_value': k[4], 'why': k[5]} for k in KNOWN],
        }],
    }


def write(out):
    with io.open(OUT, 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
        f.write('\n')
    print('OK -> %s  (%d bytes)' % (os.path.abspath(OUT), os.path.getsize(OUT)))
    print('义类 %d · 卡片 %d · known_issues %d 条'
          % (len(out['yilei']), len(out['cards']), len(out['known_issues'][0]['items'])))


# ---------------------------------------------------------------- 漂移检查
def diff_paths(a, b, path=''):
    """逐字段比，返回 [(路径, 仓库值, 重算值)]。只报叶子差异，不报整棵子树。"""
    out = []
    if isinstance(a, dict) and isinstance(b, dict):
        for k in list(a) + [x for x in b if x not in a]:
            if k not in a:
                out.append((path + '/' + k, '（缺）', _short(b[k])))
            elif k not in b:
                out.append((path + '/' + k, _short(a[k]), '（缺）'))
            else:
                out += diff_paths(a[k], b[k], path + '/' + k)
    elif isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            out.append((path + '/长度', len(a), len(b)))
        for i, (x, y) in enumerate(zip(a, b)):
            out += diff_paths(x, y, '%s[%d]' % (path, i))
    elif a != b:
        out.append((path or '/', _short(a), _short(b)))
    return out


def _short(v):
    s = json.dumps(v, ensure_ascii=False)
    return s if len(s) <= 60 else s[:57] + '...'


def check():
    """重算一遍，与仓库里那份比。`built` 是生成日期，跨天必然不同，故忽略。"""
    if not os.path.exists(OUT):
        print('✗ %s 不存在' % OUT)
        return 1
    tracked = json.load(io.open(OUT, encoding='utf-8'))
    fresh = build(read_data(), tracked.get('built') or _today())
    diffs = diff_paths(tracked, fresh)
    diffs = [d for d in diffs if d[0] != '/built']
    rel = os.path.relpath(OUT, os.path.join(HERE, '..')).replace('\\', '/')
    if not diffs:
        print('✓ %s 与 docs/index.html 的 const DATA 一致（%d 张卡）' % (rel, len(fresh['cards'])))
        return 0
    print('✗ %s 与 docs/index.html 不一致 —— %d 处：' % (rel, len(diffs)))
    for p, x, y in diffs[:40]:
        print('   %s' % p)
        print('      仓库里: %s' % x)
        print('      重算得: %s' % y)
    if len(diffs) > 40:
        print('   ...（还有 %d 处未列）' % (len(diffs) - 40))
    print('\n要么跑 python data/build_yifu_cards.py 重新生成，要么把 index.html 改回去。')
    return 1


def _today():
    return datetime.date.today().isoformat()


def main():
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass
    if '--check' in sys.argv:
        return check()
    write(build(read_data(), _today()))
    return 0


if __name__ == '__main__':
    sys.exit(main())