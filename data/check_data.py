# -*- coding: utf-8 -*-
"""义符 · 数据卫生检查 —— 一条命令跑完。

    python data/check_data.py            # 人看的报告
    python data/check_data.py --json     # 机器可读
    python data/check_data.py --strict   # WARN 也当失败

退出码：0 = 通过，1 = 发现问题。

为什么要有这个脚本
------------------
词表历史上出过好几类脏数据：词头被源文件截断（anywa / cance / energ）、
词头粘了词性尾巴（patience n.）、缺音标、释义里混进音标垃圾（weatherman）。
这些**修过了，但没有任何机制在检查**，所以一定还会再长出来 ——
「脚本改了、产物没重跑」正是上次的病根。

两条设计上的取舍
----------------
1. **本脚本 import build_wordlist，用生成器自己的 clean_word / kind_of 判定**，
   不另写一套规则。两处各写一份规则，改了这边忘了那边，就是同一个病。

2. **`w` 和 `hw` 是两回事，分开查。**
   `w`   = 原始词条串，**故意保留源件的括号注记**（`arise (arose, arisen)`、
           `bad (worse, worst)`，169 条），它是给学生看的显示串；
   `hw`  = 查词用的干净词头，**这才是唯一该满足"词头只能是词"的字段**。
   所以「含空格」在 `hw` 上是 ERROR，在 `w` 上只是 WARN。

检查项一览
----------
    W001 hw 空 / 不以字母开头            ERROR
    W002 hw 含空格（非 phrase）          ERROR
    W003 hw 含非法字符                   ERROR
    W004 hw 末尾粘词性尾巴               ERROR
    W005 hw 重复                         ERROR
    W006 w 末尾粘词性尾巴                WARN
    W007 w 用 = 标别名（源件写法）        WARN
    W008 缺 ipa                          WARN
    W009 ipa 混进中日韩字符或数字         ERROR
    W010 def 为空                        ERROR
    W011 def 开头混进音标垃圾             ERROR   ← weatherman
    W012 hw 在源表里查不到                WARN
    W013 w 含空格且无法解释               WARN
    W014 w 过 clean_word 回不到 hw        ERROR   ← 产物与生成器不同步
    W015 w 保留了源件已知错拼             WARN    ← anywa
    X001..X005 各 JSON 之间词集不一致     ERROR
"""
import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

# 刻意复用生成器的清洗逻辑 —— 见上文第 1 条
from build_wordlist import clean_word, kind_of, FIX  # noqa: E402

# ---- 阈值 / 正则 ----------------------------------------------------------

# 词头允许的字符：拉丁字母（含重音，café 这种是真词）、连字符、点、撇号；
# 多词短语额外允许空格与 &（Lost & Found 是正当词条）。
HW_PUNCT = set("-'.")
HW_PUNCT_PHRASE = set("-'.") | set(" &")


def hw_chars_ok(hw, kind):
    punct = HW_PUNCT_PHRASE if kind == 'phrase' else HW_PUNCT
    for ch in hw:
        if ch.isalpha() and ord(ch) < 0x250:      # 拉丁字母（含 Latin-1/Extended 重音）
            continue
        if ch in punct:
            continue
        return False
    return bool(hw) and hw[0].isalpha()
# 词性尾巴：n. / v / a. / modal / pl. 之类粘在末尾
POS_TAIL = re.compile(
    r"\s+(?:n|v|vt|vi|a|ad|adj|adv|prep|conj|pron|int|num|art|aux|pl|abbr|modal)\.?$",
    re.I)
CJK = re.compile(r'[一-鿿　-〿＀-￯]')
# 释义开头的音标垃圾：`['weath·er·man ||` 这种
IPA_JUNK = re.compile(r"^\s*\[\s*'|·[^ ]*\|\|")


class Report(object):
    def __init__(self):
        self.items = []

    def add(self, sev, code, msg, samples=(), count=None):
        self.items.append({
            'sev': sev, 'code': code, 'msg': msg,
            'count': len(samples) if count is None else count,
            'samples': [str(s)[:70] for s in list(samples)[:6]],
        })

    @property
    def failed(self):
        return any(i['sev'] == 'ERROR' for i in self.items)


# ---- 各文件加载 -----------------------------------------------------------

def load(name):
    p = os.path.join(HERE, name)
    if not os.path.exists(p):
        return None
    return json.load(io.open(p, encoding='utf-8'))


def source_heads():
    """把 lazuli_raw.txt 的原始词头按**生成器同一套规则**清一遍，做溯源比对用。"""
    p = os.path.join(HERE, 'lazuli_raw.txt')
    if not os.path.exists(p):
        return None
    raw = io.open(p, encoding='utf-8', errors='replace').read()
    heads = set()
    for line in raw.split('\n'):
        line = line.strip()
        if not line:
            continue
        ip = line.find('[')
        if ip >= 0:
            head = line[:ip]
        else:
            cut = CJK.search(line)
            head = line[:cut.start()] if cut else line
        hw = clean_word(head)
        if hw:
            heads.add(hw.lower())
    return heads


# ---- 检查项 ---------------------------------------------------------------

def check_wordlist(rep, rows, src):
    """词表本体：词头 / 音标 / 释义。"""
    ws = [str(r.get('w', '')) for r in rows]
    hws = [str(r.get('hw', '')) for r in rows]

    # --- 词头卫生（判 hw，它才是查词键）---
    bad = [r for r in rows
           if not r.get('hw') or not re.match(r'^[A-Za-z]', str(r.get('hw', '')))]
    rep.add('ERROR', 'W001', 'hw 为空或不以字母开头', [r.get('w') for r in bad], len(bad))

    bad = [r for r in rows if ' ' in str(r.get('hw', '')) and r.get('kind') != 'phrase']
    rep.add('ERROR', 'W002',
            'hw 含空格（多词短语应标 kind=phrase；单条词的词头不该有空格）',
            [r.get('hw') for r in bad], len(bad))

    bad = [r for r in rows if not hw_chars_ok(str(r.get('hw', '')), r.get('kind'))]
    rep.add('ERROR', 'W003', 'hw 含非法字符（只允许拉丁字母、连字符、点、撇号；短语另允许空格与 &）',
            [repr(r.get('hw')) for r in bad], len(bad))

    bad = [r for r in rows if POS_TAIL.search(str(r.get('hw', '')))]
    rep.add('ERROR', 'W004', 'hw 末尾粘了词性尾巴', [r.get('hw') for r in bad], len(bad))

    seen, dup = set(), []
    for h in hws:
        k = h.lower()
        if k in seen:
            dup.append(h)
        seen.add(k)
    rep.add('ERROR', 'W005', 'hw 重复（查词键必须唯一）', dup, len(dup))

    # --- 显示串 w：与 hw 的关系 ---
    # 不变式：w 走一遍生成器的 clean_word 必须回到 hw（两者本来就是同一个 head 的两种存法）。
    # 对不上 = 有人在 JSON 上手改过，或生成器改了但产物没重跑 —— 正是上次的病根。
    bad = [r for r in rows if clean_word(str(r.get('w', ''))) != str(r.get('hw', ''))]
    rep.add('ERROR', 'W014',
            'w 过一遍 clean_word 回不到 hw（产物与生成器不同步，或 JSON 被手改过）',
            ['%s -> %s != %s' % (r.get('w'), clean_word(str(r.get('w', ''))), r.get('hw'))
             for r in bad], len(bad))

    # 源件自带错拼、由生成器 FIX 表兜住的词：hw 已经是对的，但 w 还把源件的错拼原样显示出去
    bad = [r for r in rows
           if str(r.get('w', '')).lower() in FIX and str(r.get('w', '')) != str(r.get('hw', ''))]
    rep.add('WARN', 'W015',
            'w 保留了源件的已知错拼（hw 已由 FIX 表纠正，但显示串没跟上）',
            ['%s（应为 %s）' % (r.get('w'), r.get('hw')) for r in bad], len(bad))

    bad = [r for r in rows if POS_TAIL.search(str(r.get('w', '')))]
    rep.add('WARN', 'W006',
            'w 末尾粘了词性尾巴（w 是显示串，原件这样写多半是源件少了一行音标）',
            [r.get('w') for r in bad], len(bad))

    # 源件用 `=` 标别名/变体（`bike = bicycle`），这是它的写法，不算脏
    bad = [r for r in rows
           if ' ' in str(r.get('w', '')) and '=' in str(r.get('w', ''))]
    rep.add('WARN', 'W007', 'w 用 `=` 标了别名或变体（源件写法，仅供抽查）',
            [r.get('w') for r in bad], len(bad))

    # 空格 + 无括号注记 + 无等号 + 无词性尾巴 + 是单词 —— 这几条都不占，才真可疑
    def _weird_w(r):
        w = str(r.get('w', ''))
        return (' ' in w and r.get('kind') == 'word'
                and not re.search(r'[（(]', w)
                and '=' not in w
                and not POS_TAIL.search(w))
    bad = [r for r in rows if _weird_w(r)]
    rep.add('WARN', 'W013', 'w 含空格，且括号注记 / 等号 / 词性尾巴都解释不了（疑似源件串行）',
            [r.get('w') for r in bad], len(bad))

    # --- 音标 ---
    bad = [r for r in rows if not str(r.get('ipa', '')).strip()]
    rep.add('WARN', 'W008', '缺 ipa', [r.get('hw') for r in bad], len(bad))

    bad = [r for r in rows if CJK.search(str(r.get('ipa', ''))) or re.search(r'\d', str(r.get('ipa', '')))]
    rep.add('ERROR', 'W009', 'ipa 里混进了中日韩字符或数字（多半是切串切歪）',
            [r.get('hw') for r in bad], len(bad))

    # --- 释义 ---
    bad = [r for r in rows if not str(r.get('def', '')).strip()]
    rep.add('ERROR', 'W010', 'def 为空', [r.get('hw') for r in bad], len(bad))

    bad = [r for r in rows if IPA_JUNK.search(str(r.get('def', '')))]
    rep.add('ERROR', 'W011', 'def 开头混进音标垃圾（形如 `[\'weath·er·man ||`）',
            [(r.get('hw'), r.get('def')) for r in bad], len(bad))

    # --- 溯源：hw 必须在源表里 ---
    # 注意：源表**自己**就有错拼（anywa / cance / energ），被修正过的条目反而"查不到"。
    # 所以这里只能是 WARN —— 查不到既可能是修正，也可能是凭空多出来的，得人看一眼。
    if src is not None:
        bad = [r for r in rows if str(r.get('hw', '')).lower() not in src]
        rep.add('WARN', 'W012',
                'hw 在源表 lazuli_raw.txt 里查不到（既可能是源件错拼被修正过，也可能是凭空多出来的条目，需人核）',
                [r.get('hw') for r in bad], len(bad))


def check_cross_file(rep, files):
    """各 JSON 之间的一致性：同一批词在不同文件里的条数/键集必须对得上。"""
    def keys(name):
        d = files.get(name)
        return set(d) if isinstance(d, dict) else None

    def hws(name, field='hw'):
        d = files.get(name)
        if isinstance(d, list):
            return set(str(x.get(field, '')) for x in d)
        return None

    gk = hws('gaokao3500.json')
    ec = keys('etym_class.json')
    et = keys('etym_trees.json')

    if gk is not None and ec is not None and gk != ec:
        only_gk, only_ec = sorted(gk - ec)[:6], sorted(ec - gk)[:6]
        rep.add('ERROR', 'X001',
                'gaokao3500.json 与 etym_class.json 的词集不一致（各有 %d / %d 条对不上）'
                % (len(gk - ec), len(ec - gk)),
                ['只在词表:' + ','.join(only_gk), '只在定性:' + ','.join(only_ec)],
                len(gk - ec) + len(ec - gk))

    if et is not None and ec is not None and not et <= ec:
        rep.add('ERROR', 'X002', 'etym_trees.json 里有词在 etym_class.json 中不存在',
                sorted(et - ec), len(et - ec))

    iw = hws('ielts_words.json')
    ic = keys('ielts_class.json')
    it = keys('ielts_trees.json')
    for name, other in (('ielts_class.json', iw), ('ielts_trees.json', iw)):
        k = keys(name)
        if k is not None and other is not None and k != other:
            rep.add('ERROR', 'X003',
                    '%s 与 ielts_words.json 的词集不一致（%d 条对不上）'
                    % (name, len(k ^ other)),
                    sorted(k ^ other), len(k ^ other))
    if ic is not None and it is not None and ic != it:
        rep.add('ERROR', 'X004', 'ielts_class.json 与 ielts_trees.json 的词集不一致',
                sorted(ic ^ it), len(ic ^ it))

    # 义类分桶里的词必须都来自词典
    yb = files.get('yilei_buckets.json')
    if isinstance(yb, dict) and ec is not None:
        pool = set()
        for v in yb.values():
            pool |= set(str(x) for x in v)
        bad = sorted(pool - ec)
        rep.add('ERROR', 'X005', 'yilei_buckets.json 里有词不在 etym_class.json 中',
                bad, len(bad))


# ---- 输出 -----------------------------------------------------------------

def render(rep, files):
    out = []
    out.append('═' * 66)
    out.append('义符 · 数据卫生检查')
    out.append('═' * 66)
    for name in sorted(files):
        d = files[name]
        if d is None:
            out.append('  %-22s 缺失' % name)
        else:
            n = len(d)
            unit = '词条' if isinstance(d, dict) else '条'
            out.append('  %-22s %5d %s' % (name, n, unit))
    out.append('')

    errs = [i for i in rep.items if i['sev'] == 'ERROR']
    warns = [i for i in rep.items if i['sev'] == 'WARN']

    if not errs and not warns:
        out.append('没有发现问题。')
    for group, title in ((errs, '错误（必须修）'), (warns, '警告（需人看一眼）')):
        shown = [i for i in group if i['count']]
        if not shown:
            continue
        out.append('─' * 66)
        out.append(title)
        out.append('─' * 66)
        for i in shown:
            out.append('[%s] %-5s %s  —— %d 条'
                       % (i['code'], i['sev'], i['msg'], i['count']))
            for s in i['samples']:
                out.append('        · %s' % s)
            if i['count'] > len(i['samples']):
                out.append('        … 另有 %d 条' % (i['count'] - len(i['samples'])))
            out.append('')

    out.append('═' * 66)
    out.append('汇总：错误 %d 类 / 警告 %d 类' % (len([i for i in errs if i['count']]),
                                              len([i for i in warns if i['count']])))
    out.append('═' * 66)
    return '\n'.join(out)


def main():
    # Windows 控制台默认 GBK，中文报告会变乱码；PR 里要贴完整输出，先钉成 UTF-8
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

    strict = '--strict' in sys.argv
    as_json = '--json' in sys.argv

    names = ['gaokao3500.json', 'etym_class.json', 'etym_trees.json',
             'yilei_buckets.json', 'ielts_words.json', 'ielts_class.json',
             'ielts_trees.json', 'coverage.json']
    files = dict((n, load(n)) for n in names)

    rep = Report()
    gk = files.get('gaokao3500.json')
    if isinstance(gk, list):
        check_wordlist(rep, gk, source_heads())
    check_cross_file(rep, files)

    if as_json:
        print(json.dumps(rep.items, ensure_ascii=False, indent=2))
    else:
        print(render(rep, files))

    bad = rep.failed or (strict and any(i['count'] for i in rep.items))
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())