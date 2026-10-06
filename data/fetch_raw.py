# -*- coding: utf-8 -*-
"""
从 kaikki.org 抓每个词的原始 HTML 切片，落盘缓存。

★ 为什么存原始 HTML 而不是解析结果：
  第一版只存了「第一个 Etymology 段」的模板串，结果发现两个坑 ——
  (a) {{ety|en|...}} 这个新模板没解析；
  (b) 只取第一段是错的：act 的第一段是「actually 的缩写」（网络俚语），
      be 的第一段是「字母名借自俄语」，都不是要讲的那个词源。
  要正确处理就得把所有 Etymology 段都拿到，并按词性挑主段。
  与其反复重抓，不如把原始切片存下来，解析逻辑随便改。

★ 路径大小写：kaikki 按原大小写分目录。Africa 在 A/Af/Africa.html，
  小写路径 404（因为小写 china 是"瓷器"另一个词条，Africa 没有小写对应词）。
  所以先用原大小写试，404 再退回小写。

用法：
  python fetch_raw.py            # 全量
  python fetch_raw.py 40         # 试跑前 40
"""
import io, json, os, re, sys, time
import urllib.request, urllib.error, urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, 'gaokao3500.json')
OUTDIR = os.path.join(HERE, 'etym_raw')
os.makedirs(OUTDIR, exist_ok=True)

RANGE = 24576           # 24KB：词源偏移中位数 8.3KB、最大 12.4KB
RANGE_BIG = 786432      # 兜底 768KB
WORKERS = 12
UA = 'yifu-etym-research/0.1 (educational; github.com/Denghui1835/yifu-language)'

for k in ('HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy', 'ALL_PROXY', 'all_proxy'):
    os.environ.pop(k, None)
os.environ['NO_PROXY'] = '*'


def key_of(hw):
    return re.sub(r'[^\w\-]', '_', hw.lower())


def urls(hw):
    """先原大小写，再全小写"""
    seg = urllib.parse.quote(hw, safe='')
    low = hw.lower()
    seg_low = urllib.parse.quote(low, safe='')
    base = 'https://kaikki.org/dictionary/English/meaning/%s/%s/%s.html'
    out = [base % (hw[0], hw[:2], seg)]
    if low != hw:
        out.append(base % (low[0], low[:2], seg_low))
    return out


def fetch(url, nbytes):
    req = urllib.request.Request(url, headers={
        'User-Agent': UA, 'Range': 'bytes=0-%d' % (nbytes - 1),
        'Accept-Encoding': 'identity'})
    with urllib.request.urlopen(req, timeout=45) as r:
        return r.read()


def one(hw):
    fn = os.path.join(OUTDIR, key_of(hw) + '.html')
    if os.path.exists(fn):
        return hw, 'skip'
    last = '404'
    for i, u in enumerate(urls(hw)):
        try:
            body = fetch(u, RANGE)
            # 首片里没有 Etymology 就加大窗口再来一次
            if b'Etymology' not in body:
                try:
                    body = fetch(u, RANGE_BIG)
                except Exception:
                    pass
            with open(fn, 'wb') as f:
                f.write(body)
            return hw, 'ok' if i == 0 else 'ok(lower)'
        except urllib.error.HTTPError as e:
            last = 'http%d' % e.code
            continue
        except Exception as e:
            last = 'err:' + type(e).__name__
            continue
    with open(fn, 'wb') as f:      # 记下失败，避免重复试
        f.write(b'')
    return hw, last


def main():
    recs = json.load(io.open(SRC, encoding='utf-8'))
    heads = []
    for r in recs:
        h = r['hw']
        if r['kind'] == 'letter':
            continue
        if h not in heads:
            heads.append(h)
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else len(heads)
    heads = heads[:limit]
    todo = [h for h in heads if not os.path.exists(os.path.join(OUTDIR, key_of(h) + '.html'))]
    print('词头 %d / 待抓 %d / 并发 %d' % (len(heads), len(todo), WORKERS))
    if not todo:
        return
    t0 = time.time(); done = 0; stat = {}
    with ThreadPoolExecutor(max_workers=WORKERS) as ex:
        futs = [ex.submit(one, h) for h in todo]
        for f in as_completed(futs):
            h, st = f.result()
            stat[st] = stat.get(st, 0) + 1
            done += 1
            if done % 200 == 0 or done == len(todo):
                el = time.time() - t0
                print('  %5d/%d  %6.1fs  %.1f/s  %s' % (
                    done, len(todo), el, done / el,
                    ' '.join('%s=%d' % kv for kv in sorted(stat.items()))))
    print('完成 %.1fs' % (time.time() - t0))


if __name__ == '__main__':
    main()
