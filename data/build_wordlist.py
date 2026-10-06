# -*- coding: utf-8 -*-
"""
重建高考3500词表。

★ 为什么重做：原来那份 gaokao3500.json 把长词截断了 —— 第 54 条是
  {"w":"acut", "def":"a.尖的,敏锐的,剧烈的"}，即 acute 被砍成 4 个字母。
  追到源头 lazuli_raw.txt 才发现原件是好的（acute、after 都在），
  是我当时的解析正则有问题。地基坏了，整条链都不可信，所以重来。

源：LazuliKao/brochure-of-vocabularies 的 raw.txt（3897 行，词+音标+释义）
产出：gaokao3500.json  ->  [{w, ipa, def, hw, kind}]
      w    = 原始词条串
      hw   = 查词用的词头（去括号、去冠词、-- 归一）
      kind = word | phrase | letter
"""
import io, json, os, re, collections

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, 'lazuli_raw.txt')
OUT = os.path.join(HERE, 'gaokao3500.json')

CJK = r'一-鿿　-〿＀-￯'
ARTICLES = ('the ', 'a ', 'an ')


POS_TOK = re.compile(r'\s+(?:n|v|vt|vi|a|ad|adj|adv|prep|conj|pron|int|num|art|'
                      r'aux|pl|abbr|modal)\.?$', re.I)
# ★ 原件自带的小毛病，逐条修（不修就是真丢词）：
#   'anywa [ˈenɪweɪ]y ad.' —— 源文件把 anyway 的末字母 y 甩到了音标后面
FIX = {'anywa': 'anyway'}


def clean_word(s):
    """把词头串清成能查的样子"""
    s = s.replace('', ' ').replace('�', '')
    s = re.sub(r'[-]', '-', s)       # 私用区字符当连字符用（CD<e011>ROM）
    s = s.replace('--', '-')                     # 原件把破折号写成了 --
    s = re.sub(r'\s*-\s*', '-', s)               # 'department -store' / 'pencil- sharpener'
    s = s.split('/')[0]                          # a.m./A.M. -> a.m.
    s = s.split('=')[0]                          # bike = bicycle -> bike
    s = re.sub(r'[（(][^）)]*[）)]', ' ', s)      # begin(began,begun)、anyway(s)
    s = re.split(r'[（(]', s)[0]                 # 没配对的左括号（CJK 切口切一半留下的）
    s = s.replace('*', '')                       # 脚注星号（Egypt* 这种）
    s = s.strip(' \t.,;:=')
    s = re.sub(r'\s+', ' ', s).strip()
    for _ in range(2):
        s = POS_TOK.sub('', s).strip()           # 无音标行会把词性粘在词头上
    low = s.lower()
    for a in ARTICLES:
        if low.startswith(a) and len(s) > len(a):
            s = s[len(a):].strip()
            break
    return FIX.get(s.lower(), s)


def kind_of(hw):
    if len(hw) == 1 and hw.isalpha():
        return 'letter'
    if ' ' in hw:
        return 'phrase'
    return 'word'


def main():
    raw = io.open(SRC, encoding='utf-8', errors='replace').read()
    rows, skipped = [], []
    for line in raw.split('\n'):
        line = line.strip()
        if not line:
            continue
        # ★ 词头只按「音标 [」或「第一个中日韩字符」切。
        #   不能对整行做括号剥离 —— 释义里的括号是内容（prep. 上（船，飞机…）），
        #   剥了就丢。括号只在词头内部处理。
        ip = line.find('[')
        if ip >= 0:
            head, tail = line[:ip], line[ip:]
        else:
            cut = re.search(r'[一-鿿　-〿＀-￯]', line)
            head = line[:cut.start()] if cut else line
            tail = line[cut.start():] if cut else ''
        mi = re.match(r'^\s*(\[[^\]]*\])?\s*(.*)$', tail)
        ipa, rest = (mi.group(1) or ''), mi.group(2)
        hw = clean_word(head)
        if not hw or not re.match(r"^[A-Za-z]", hw):
            skipped.append(line)
            continue
        if not rest.strip():
            skipped.append(line)
            continue
        rest = re.sub(r'\s+', ' ', rest.replace('', ' ')).strip()
        rows.append({'w': head.strip(), 'ipa': ipa.strip('[]'),
                     'def': rest, 'hw': hw, 'kind': kind_of(hw)})

    # 去重（保留首次出现）
    seen, out = set(), []
    for r in rows:
        k = r['hw'].lower()
        if k in seen:
            continue
        seen.add(k)
        out.append(r)

    json.dump(out, io.open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=0)

    print('解析 %d 行 -> 词条 %d -> 去重后 %d' % (len(raw.split('\n')), len(rows), len(out)))
    print('被跳过 %d 行，样例：' % len(skipped))
    for s in skipped[:10]:
        print('   ', s[:90])
    k = collections.Counter(r['kind'] for r in out)
    print('类型：', dict(k))
    print('\n长度分布：', sorted(collections.Counter(
        min(len(r['hw']), 14) for r in out).items()))
    print('\n前 8 条：')
    for r in out[:8]:
        print('   %-14s %-18s %s' % (r['hw'], r['ipa'][:16], r['def'][:40]))
    print('\n抽样校验：')
    for p in ('acute', 'after', 'acut', 'afte', 'best-seller', 'best--seller',
              'abandon', 'courage', 'Antarctic'):
        hit = [r for r in out if r['hw'].lower() == p.lower()]
        print('   %-14s %s' % (p, ('有 -> ' + hit[0]['def'][:30]) if hit else '无'))


if __name__ == '__main__':
    main()
