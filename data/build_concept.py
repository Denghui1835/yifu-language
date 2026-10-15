#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""产品概念图生成器（Issue #10）。

为什么是"代码绘制"而不是生图工具
--------------------------------
#10 的方向已由项目方改过：不再要"氛围参考图"，要的是**产品概念图**——
图里必须出现真实的对齐关系 `氵 ↔ aqua-（拉丁）/ hydr-（希腊）/ mar-（拉丁）`，
一眼看出产品在干嘛。

凡"必须带可读文字"的图，**不能用 SD1.5 之类生图模型**：它写字必乱码，
第一版 B 方向满纸鬼画符即为证（见 Issue #10 的留言）。正解是代码绘制：
字是真的、零乱码、可重跑、可复现。

红线（几条不许破）
------------------
1. **图上每个字、每个词全部来自仓库既有数据**，无一处杜撰。
   数据源：`data/yifu_cards.json`（义符卡的复核内容层，由 docs/index.html 的
   const DATA 生成，且经 Issue #25 裁定）。本脚本**只读**该文件，不改它。
2. **配色只用 DESIGN.md 的令牌**，且守三条铁律：
   朱砂（--zhu）只给汉语侧，靛青（--dian）只给英语侧，金（--jin）只给中枢。
3. 本脚本**不改任何页面、不改任何数据**；产物只落在 docs/design/。

依赖
----
仅标准库 + Pillow（画布与字体）。字体走本机已装字：楷体写汉字/义符，
宋体写中文说明，Georgia 写英文。字体按候选表逐个找，全找不到才报错，
不静默降级成方块。

跑法
----
    python data/build_concept.py             # 产出到 docs/design/
    python data/build_concept.py --out D:/x  # 改落点
"""

import argparse
import json
import os
import sys

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
CARDS = os.path.join(HERE, 'yifu_cards.json')
OUT_DEFAULT = os.path.join(ROOT, 'docs', 'design')

# ---- 画布 ----
W, H = 2400, 1350
M = 120  # 外边距

# ---- 色板：逐个对 DESIGN.md §1（令牌值写死，保证离线可重跑）----
PAPER = '#f7f4ee'
PAPER2 = '#fffdf8'
INK = '#221f1b'
INK2 = '#6b6357'
INK3 = '#9c9385'
ZHU = '#b8452f'
ZHU_BG = '#f6e6e0'
ZHU_LINE = '#eed6cd'
ZHU_INK = '#6d4a3f'
DIAN = '#2f6d8f'
DIAN_BG = '#e2edf4'
DIAN_LINE = '#cfe0ea'
DIAN_INK = '#2f5570'
JIN = '#c2922c'
JIN_BG = '#f8efd8'
JIN_LINE = '#e8d5a5'
JIN_INK = '#7a5a17'
LINE = '#e3ddd1'
ON = '#ffffff'

# ---- 字体：候选表，取第一个存在的（跨机器不至于因缺某一种字体就崩）----
FONTS = {
    'kai':   ['C:/Windows/Fonts/simkai.ttf', 'C:/Windows/Fonts/STKAITI.TTF'],
    'song':  ['C:/Windows/Fonts/simsun.ttc', 'C:/Windows/Fonts/STSONG.TTF'],
    'songb': ['C:/Windows/Fonts/STZHONGS.TTF', 'C:/Windows/Fonts/simhei.ttf',
              'C:/Windows/Fonts/msyhbd.ttc'],
    'geo':   ['C:/Windows/Fonts/georgia.ttf'],
    'geob':  ['C:/Windows/Fonts/georgiab.ttf'],
}
_cache = {}


def _font_path(kind):
    for p in FONTS[kind]:
        if os.path.exists(p):
            return p
    sys.exit('缺字体 %s：候选 %s 都不存在，无法继续' % (kind, FONTS[kind]))


def font(kind, size):
    key = (kind, size)
    if key not in _cache:
        _cache[key] = ImageFont.truetype(_font_path(kind), size)
    return _cache[key]


# ---- 代码 → 产物文件名（与 docs/assets 的字形资产同一套命名）----
SLUG = {'shui': 'water', 'shou': 'hand', 'xin': 'heart'}


def text(d, xy, s, kind, size, fill, anchor='la'):
    d.text(xy, s, font=font(kind, size), fill=fill, anchor=anchor)


def tl(s, kind, size):
    """文字宽度，用于横排拼接。"""
    return font(kind, size).getlength(s)


def card(d, box, fill=PAPER2, outline=LINE, width=3):
    """统一走 2px 直角卡片（DESIGN §3.2）。"""
    d.rounded_rectangle(box, radius=2, fill=fill, outline=outline, width=width)


def square_tag(d, x, y, size, ch, bg):
    """汉语/英语的方形字标（DESIGN §5.3 .tag.square）。"""
    d.rounded_rectangle([x, y, x + size, y + size], radius=2, fill=bg)
    text(d, (x + size / 2, y + size / 2 + 2), ch, 'songb', int(size * 0.56), ON, anchor='mm')


def compose(y, words):
    """按一个义类 y 画一张 2400×1350 概念图。

    y      : yifu_cards.json 的 yilei 元素（name/sub/fu/chars/roots）。
    words  : 该义类的词条列表 [(word, mean), ...]，用于右栏"派生词"与页脚。
    """
    img = Image.new('RGB', (W, H), PAPER)
    d = ImageDraw.Draw(img)

    name, sub = y['name'], y['sub']
    fu = y['fu']
    chars = [c['c'] for c in y['chars']]
    roots = y['roots']

    # ================= 页眉 =================
    text(d, (M, 62), '义符', 'songb', 92, INK)
    text(d, (M + tl('义符', 'songb', 92) + 44, 118), '用母语的逻辑学外语', 'song', 36, INK3)
    text(d, (W - M, 118), '产品概念图 · 阶段零', 'song', 30, INK3, anchor='ra')
    d.line([(M, 196), (W - M, 196)], fill=LINE, width=3)

    TOP = 260
    LX0, LX1 = M, 880            # 左栏（汉语侧）
    RX0, RX1 = 1520, W - M       # 右栏（英语侧）
    CX = 1200                    # 中轴

    # ================= 左栏：汉语侧 =================
    square_tag(d, LX0, TOP, 40, '汉', ZHU)
    text(d, (LX0 + 60, TOP + 6), '汉语 · 义符', 'songb', 36, ZHU)

    # 义符大卡：氵 / 水 两个字形各占半格
    # 以同一基线（baseline）落字，氵 是窄偏旁，稍放大并把墨色调成同重，
    # 免得两个字形一个高一个低、看着不像一对。
    cy0, chgt = TOP + 80, 236
    base = cy0 + 176
    card(d, [LX0, cy0, LX1, cy0 + chgt], fill=PAPER2, outline=ZHU_LINE)
    d.line([(LX0 + 380, cy0 + 40), (LX0 + 380, cy0 + chgt - 40)], fill=ZHU_LINE, width=3)
    for cx, g, gs, cap in ((LX0 + 190, fu[0]['ch'], 198, fu[0]['ch'] + '　变形'),
                           (LX0 + 570, fu[1]['ch'], 176, fu[1]['ch'] + '　本字')):
        text(d, (cx, base), g, 'kai', gs, ZHU, anchor='ms')
        text(d, (cx, base + 34), cap, 'song', 30, INK3, anchor='mm')

    ey = cy0 + chgt + 46
    text(d, (LX0, ey), fu[0]['ch'] + ' 是 ' + fu[1]['ch'] + ' 作左偏旁时的写法',
         'song', 34, ZHU_INK)
    text(d, (LX0, ey + 50), '对应英语词根　' + ' · '.join(r['form'] for r in roots),
         'song', 30, INK2)

    ly = ey + 118
    text(d, (LX0, ly), '同义类汉字', 'songb', 32, INK2)
    gy = ly + 60
    cols, gap, chh = 5, 16, 156
    cw = (LX1 - LX0 - gap * (cols - 1)) / cols
    for i, c in enumerate(chars):
        r, ci = divmod(i, cols)
        x0 = LX0 + ci * (cw + gap)
        y0 = gy + r * (chh + gap)
        card(d, [x0, y0, x0 + cw, y0 + chh], fill=PAPER2, outline=LINE)
        text(d, (x0 + cw / 2, y0 + chh / 2), c, 'kai', 92, INK, anchor='mm')

    # ================= 右栏：英语侧 =================
    square_tag(d, RX0, TOP, 40, '英', DIAN)
    text(d, (RX0 + 60, TOP + 6), '英语 · 词根', 'songb', 36, DIAN)

    ry, rh = TOP + 80, 110
    for r in roots:
        card(d, [RX0, ry, RX1, ry + rh], fill=PAPER2, outline=DIAN_LINE)
        mid = ry + rh / 2
        text(d, (RX0 + 40, mid), r['form'], 'geob', 62, DIAN, anchor='lm')
        lw = tl(r['src'], 'song', 26) + 40
        d.rounded_rectangle([RX1 - 40 - lw, mid - 22, RX1 - 40, mid + 22],
                            radius=2, outline=LINE, width=2, fill=PAPER)
        text(d, (RX1 - 40 - lw / 2, mid), r['src'], 'song', 26, INK3, anchor='mm')
        text(d, (RX1 - 40 - lw - 30, mid), r['gloss'], 'song', 34, INK2, anchor='rm')
        ry += rh + 16

    wy = ry + 44
    text(d, (RX0, wy), '派生词', 'songb', 32, INK2)
    for i, (wd, mean) in enumerate(words[:3]):
        y0 = wy + 60 + i * 100
        card(d, [RX0, y0, RX1, y0 + 84], fill=PAPER2, outline=LINE)
        text(d, (RX0 + 40, y0 + 42), wd, 'geob', 46, DIAN, anchor='lm')
        text(d, (RX1 - 40, y0 + 42), mean, 'song', 30, INK3, anchor='rm')

    # ================= 中轴：义类节点 =================
    text(d, (CX, TOP + 6), '义　类', 'song', 34, INK3, anchor='ma')
    dcy, R = 620, 150
    d.line([(LX1, cy0 + chgt / 2), (CX - R, dcy)], fill=ZHU_LINE, width=4)
    d.line([(CX + R, dcy), (RX0, ry - rh / 2 - 90)], fill=DIAN_LINE, width=4)
    d.ellipse([CX - R, dcy - R, CX + R, dcy + R], fill=JIN_BG, outline=JIN_LINE, width=4)
    text(d, (CX, dcy - 16), name, 'kai', 148, JIN_INK, anchor='mm')
    text(d, (CX, dcy + 82), sub, 'song', 30, JIN_INK, anchor='mm')
    text(d, (CX, dcy + R + 56), '一个义类，两种语言各自长出的形式', 'song', 30, INK3, anchor='ma')

    # ================= 页脚：啊哈一句 =================
    by = 1172
    card(d, [M, by, W - M, by + 114], fill=JIN_BG, outline=JIN_LINE)
    ymid = by + 57
    fc, root0, word0 = chars[0], roots[0]['form'], (words[0][0] if words else '')
    x = M + 50
    segs = [('「', INK2, 'song', 40), (fc, ZHU, 'kai', 52), ('」的　', INK2, 'song', 40),
            (fu[0]['ch'], ZHU, 'kai', 48), ('　和　', INK2, 'song', 40),
            (word0, DIAN, 'geob', 44), (' 的 ', INK2, 'song', 40),
            (root0, DIAN, 'geob', 44), ('　是同一个义类', INK2, 'song', 40)]
    for s, col, kind, size in segs:
        text(d, (x, ymid), s, kind, size, col, anchor='lm')
        x += tl(s, kind, size)
    text(d, (W - M - 50, ymid), '别人教规则，我们调用本能。', 'songb', 38, JIN_INK, anchor='rm')

    return img


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', default=OUT_DEFAULT, help='产物目录（默认 docs/design/）')
    args = ap.parse_args()

    with open(CARDS, encoding='utf-8') as f:
        data = json.load(f)

    # 每个义类的词条（按 cards 里的顺序）
    words = {}
    for c in data['cards']:
        words.setdefault(c['yilei_key'], []).append((c['w'], c['mean']))

    os.makedirs(args.out, exist_ok=True)
    for y in data['yilei']:
        img = compose(y, words.get(y['key'], []))
        out = os.path.join(args.out, 'concept_%s.png' % SLUG[y['key']])
        img.save(out)
        print('写出', os.path.relpath(out, ROOT), '%dx%d' % (W, H))


if __name__ == '__main__':
    main()
