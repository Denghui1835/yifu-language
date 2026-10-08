# -*- coding: utf-8 -*-
r"""义符 · 「字形演变」与「词根谱系」矢量资产生成器

用法：
    python data/build_hz_assets.py          # 重新生成 docs/assets/ 下的 SVG
    python data/build_hz_assets.py --check  # 只校验产物与生成器是否还一致

为什么要有这个脚本
------------------
Issue #12 要一套能被页面直接引用的矢量资产：≥6 张义符演变图 + ≥3 张词根谱系图。
手写 9 个 SVG，会把「一格画多大、字摆哪、线怎么连」这些规则散成 9 份 ——
改一次版式要改 9 个文件、还必然改漏。本脚本把版式收敛成**一份规则**，
字形与例词放进下面的表（`YIFU` / `ROOTS`）里 —— **改表即改图**。

红线（Issue #12 明写，本脚本严格执行）
--------------------------------------
**字形演变不许编。** 查不到就只画到能查到的年代为止，并在图里注明。
所以 `YIFU` 表里 `missing` 非空的字（如「手」缺甲骨），
生成出来的就是**缺一格 + 一行说明**，而不是拿想象填一格。

字形从哪来
----------
`docs/assets/src/` 下 17 个 `<字>-<阶段>.svg`，
取自 Wikimedia Commons（**Public domain**，逐字可查，出处见 `docs/assets/README.md`）。
它们坐标系不统一：有的 `viewBox="0 0 300 300"`，有的靠 `<g transform="translate(0,-752)">` 平移。
所以本脚本**不重算坐标**，而是把原文件按 data URI **原样内嵌** ——
内嵌的东西浏览器按它自己的坐标系摆，**不会画歪**。

产物与生成器的边界
------------------
`docs/assets/src/` 是**来源**，本脚本只读不改；
`docs/assets/*.svg` 是**产物**，全部由本脚本生成，**不要手改**（手改会被 `--check` 抓到）。
"""
import base64, os, sys, xml.sax.saxutils as su

HERE = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.join(HERE, '..', 'docs', 'assets', 'src')   # 来源：只读
OUT_DIR = os.path.join(HERE, '..', 'docs', 'assets')          # 产物：本脚本写

# ---------------------------------------------------------------------------
# 设计令牌 —— 逐字抄自 docs/index.html 的 :root（见 :9-19）。
# 这里**故意写死**而不是去解析 index.html：资产要能单独重跑、不依赖 HTML。
# 色值若在 index.html 里改了，这里跟随，属已知的「两处同值」——
# 规范的归口在 Issue #11（docs/DESIGN.md），届时按规范统一。
# ---------------------------------------------------------------------------
INK   = '#221f1b'   # 墨 —— 正文
INK2  = '#6b6357'   # 墨淡 —— 副文
INK3  = '#9c9385'   # 墨更淡 —— 脚注
LINE  = '#e3ddd1'   # 线
PAPER2 = '#fffdf8'  # 纸2 —— 底色
ZHU   = '#b8452f'   # 朱砂 —— 汉语侧
DIAN  = '#2f6d8f'   # 靛青 —— 英语侧 · 拉丁来源
GREEK = '#6f5b9e'   # 紫   —— 英语侧 · 希腊来源（#12 提议值，待 #11 归口）

SERIF = '"Songti SC","STSong","SimSun","Noto Serif SC",serif'
KAI   = '"Kaiti SC","STKaiti","KaiTi","Kaiti TC","SimSun",serif'
SANS  = '"PingFang SC","Microsoft YaHei",system-ui,-apple-system,sans-serif'

# 四个阶段：key 对应源文件名 <字>-<key>.svg；楷书没有源文件，用真字渲染
STAGES = [('oracle', '甲骨文'), ('bronze', '金文'), ('seal', '小篆'), ('kai', '楷书')]

# ---------------------------------------------------------------------------
# 表一：义符演变图。slug 决定输出文件名；missing 列出查不到可靠字形的阶段（红线：不补）。
# 出处逐条见 docs/assets/README.md。
# ---------------------------------------------------------------------------
YIFU = [
    dict(slug='shui', zi='水', radical='氵', pin='shuǐ', en='水', bridge='aqua · hydr · mar', missing=set()),
    dict(slug='shou', zi='手', radical='扌', pin='shǒu', en='手', bridge='manu · chiro',   missing={'oracle'}),
    dict(slug='xin',  zi='心', radical='忄', pin='xīn',  en='心', bridge='cord · psych · path', missing=set()),
    dict(slug='mian', zi='宀', radical='宀', pin='mián', en='屋顶／家', bridge='', missing=set()),
    dict(slug='yan',  zi='言', radical='讠', pin='yán',  en='言语', bridge='', missing=set()),
    dict(slug='mu',   zi='木', radical='木', pin='mù',   en='树木', bridge='', missing=set()),
]

# ---------------------------------------------------------------------------
# 表二：词根谱系图。latin / greek 两组，例词全部取自 docs/index.html 演示层的真实词。
# 「拉丁 vs 希腊」是产品要讲的那件事：同一个意思，两条不同来路。
# ---------------------------------------------------------------------------
ROOTS = [
    dict(slug='water', zi='水', radical='氵', pin='shuǐ', en='water',
         latin=[('aqua', 'aquatic · aquarium · aqueduct · aquamarine'),
                ('mar',  'marine · maritime · submarine')],
         greek=[('hydr', 'hydrate · dehydrate · hydrogen')]),
    dict(slug='hand', zi='手', radical='扌', pin='shǒu', en='hand',
         latin=[('manu', 'manual · manuscript · manufacture · manicure · manipulate · emancipate')],
         greek=[('chiro', 'chiropractor · chirography')]),
    dict(slug='heart', zi='心', radical='忄', pin='xīn', en='heart',
         latin=[('cord', 'cordial · accord · discord · concord · record · courage')],
         greek=[('psych', 'psychology · psychiatrist'), ('path', 'sympathy · empathy')]),
]

SOURCE_LINE = '字形来源：Wikimedia Commons（Public Domain），逐字出处见 docs/assets/README.md'
PROV_DESC = ('义符项目 · Issue #12 资产。字形取自 Wikimedia Commons 公共领域字形文件，'
             '按 data URI 原样内嵌，未重绘、未改动。生成：python data/build_hz_assets.py')


# ---------------------------------------------------------------------------
# 小工具
# ---------------------------------------------------------------------------
def esc(s):
    return su.escape(str(s))

def data_uri(path):
    """把一份源 SVG 原样包成 data URI —— 内嵌而非重绘，坐标系一致，不会画歪。"""
    with open(path, 'rb') as f:
        return 'data:image/svg+xml;base64,' + base64.b64encode(f.read()).decode('ascii')

def src_path(zi, stage):
    """返回 <字>-<阶段>.svg 的路径；不存在返回 None。"""
    p = os.path.join(SRC_DIR, '%s-%s.svg' % (zi, stage))
    return p if os.path.exists(p) else None

def txt(x, y, s, size, fill, anchor='start', family=None, weight=None, spacing=None):
    a = ['x="%s"' % x, 'y="%s"' % y, 'font-size="%s"' % size, 'fill="%s"' % fill]
    if anchor != 'start':  a.append('text-anchor="%s"' % anchor)
    if family:  a.append('font-family=%s' % _q(family))
    if weight:  a.append('font-weight="%s"' % weight)
    if spacing: a.append('letter-spacing="%s"' % spacing)
    return '<text %s>%s</text>' % (' '.join(a), esc(s))

def _q(family):
    # font-family 值本身含引号，用单引号包整串，避免与属性双引号打架
    return "'%s'" % family.replace("'", "")

def line(x1, y1, x2, y2, color, w=1, dash=None):
    d = ' stroke-dasharray="%s"' % dash if dash else ''
    return '<line x1="%s" y1="%s" x2="%s" y2="%s" stroke="%s" stroke-width="%s"%s/>' % (x1, y1, x2, y2, color, w, d)

def rect(x, y, w, h, fill='none', stroke=None, rx=2, dash=None, sw=1):
    a = ['x="%s"' % x, 'y="%s"' % y, 'width="%s"' % w, 'height="%s"' % h, 'rx="%s"' % rx, 'fill="%s"' % fill]
    if stroke: a.append('stroke="%s" stroke-width="%s"' % (stroke, sw))
    if dash:   a.append('stroke-dasharray="%s"' % dash)
    return '<rect %s/>' % ' '.join(a)

def svg_open(w, h, title):
    return ('<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
            'width="%s" height="%s" viewBox="0 0 %s %s">' % (w, h, w, h)
            + '<title>%s</title><desc>%s</desc>' % (esc(title), esc(PROV_DESC)))


# ---------------------------------------------------------------------------
# 义符演变图：一格 = 一个阶段。三种格：内嵌字形 / 楷书真字 / 缺格（不补）
# ---------------------------------------------------------------------------
CELL_W, CELL_H, GAP, X0, ROW_Y = 151, 176, 12, 40, 92
GLYPH = 124

def _cell(zi, stage, x, y, missing):
    cx = x + CELL_W / 2.0
    label = STAGE_ZH(stage)
    if stage == 'kai':
        ch = '<rect x="%s" y="%s" width="%s" height="%s" rx="2" fill="#ffffff" stroke="%s"/>' % (x, y, CELL_W, CELL_H, LINE)
        ch += txt(cx, y + GLYPH * 0.5 + 40, zi, 92, INK, anchor='middle', family=KAI)
        ch += txt(cx, y + CELL_H - 14, label, 13, INK2, anchor='middle', spacing='0.06em')
        return ch
    if stage in missing:
        ch = rect(x, y, CELL_W, CELL_H, fill='none', stroke=INK3, dash='4 4')
        ch += txt(cx, y + CELL_H / 2 - 6, '未找到', 14, INK3, anchor='middle')
        ch += txt(cx, y + CELL_H / 2 + 16, '可靠字形', 14, INK3, anchor='middle')
        ch += txt(cx, y + CELL_H - 14, label + ' · 不补', 13, INK3, anchor='middle', spacing='0.06em')
        return ch
    p = src_path(zi, stage)
    uri = data_uri(p)
    ch = '<rect x="%s" y="%s" width="%s" height="%s" rx="2" fill="#ffffff" stroke="%s"/>' % (x, y, CELL_W, CELL_H, LINE)
    ch += ('<image x="%.1f" y="%s" width="%s" height="%s" preserveAspectRatio="xMidYMid meet" '
           'xlink:href="%s" href="%s"/>' % (x + (CELL_W - GLYPH) / 2.0, y + 12, GLYPH, GLYPH, uri, uri))
    ch += txt(cx, y + CELL_H - 14, label, 13, INK2, anchor='middle', spacing='0.06em')
    return ch

def STAGE_ZH(stage):
    return dict(STAGES)[stage]

def build_yifu(row):
    w, h = 720, 316
    sub = '%s · %s' % (row['radical'], row['en'])
    if row['bridge']:
        sub += '   ↔   英语词根  ' + row['bridge']
    out = [svg_open(w, h, '%s 的字形演变' % row['zi'])]
    out.append(rect(0, 0, w, h, fill=PAPER2))
    out.append(txt(X0, 48, row['zi'], 34, ZHU, family=SERIF))
    out.append(txt(X0 + 48, 46, row['pin'], 16, INK2, family=SANS))
    out.append(txt(X0, 74, sub, 13.5, INK2, family=SANS))
    for i, (stage, _) in enumerate(STAGES):
        out.append(_cell(row['zi'], stage, X0 + i * (CELL_W + GAP), ROW_Y, row['missing']))
    out.append(txt(X0, 300, SOURCE_LINE, 11.5, INK3, family=SANS))
    out.append('</svg>\n')
    return ''.join(out)


# ---------------------------------------------------------------------------
# 词根谱系图：左「义符」，中「语族（拉丁／希腊）」，右「词根 → 例词」
# ---------------------------------------------------------------------------
FAM_ZH = {'latin': '拉丁', 'greek': '希腊'}
ROW_H = 84

def _wrap(s, width=38):
    """把 ' · ' 分隔的例词折成 ≤2 行，不丢词。"""
    if len(s) <= width:
        return [s]
    lines, cur = [], ''
    for p in s.split(' · '):
        t = p if not cur else cur + ' · ' + p
        if len(t) <= width:
            cur = t
        else:
            lines.append(cur); cur = p
    if cur:
        lines.append(cur)
    if len(lines) > 2:                       # 超过两行则把尾巴并到第二行，宁可挤不丢
        lines = [lines[0], ' · '.join(lines[1:])]
    return lines

def build_root(row):
    rows = [('latin', m, wds) for m, wds in row['latin']] + [('greek', m, wds) for m, wds in row['greek']]
    n = len(rows)
    head, top = 104, 104
    fam_x, fam_w = 176, 78
    root_x, root_w = 300, 122
    word_x = 436
    legend_y = top + n * ROW_H + 22
    h = legend_y + 40
    cx_zi, cx_fam, cx_root = 118, 215, 361   # 各列中心 x
    cy_zi = top + (n * ROW_H) / 2.0

    out = [svg_open(720, h, '%s 的英语词根谱系' % row['zi'])]
    out.append(rect(0, 0, 720, h, fill=PAPER2))
    out.append(txt(X0, 46, '%s · %s' % (row['zi'], row['pin']), 26, ZHU, family=SERIF))
    out.append(txt(X0, 74, '%s   ↔   英语词根，拉丁与希腊不是同一个来源' % row['en'], 13.5, INK2, family=SANS))

    # 左：义符节点
    out.append(rect(X0, cy_zi - 44, 88, 88, fill='#ffffff', stroke=ZHU, sw=1.5))
    out.append(txt(X0 + 44, cy_zi + 6, row['zi'], 44, ZHU, anchor='middle', family=SERIF))
    out.append(txt(X0 + 44, cy_zi + 30, row['radical'], 14, INK3, anchor='middle', family=SERIF))

    # 中：语族列（合并同类行）
    fam_spans = {}
    for i, (fam, _, _) in enumerate(rows):
        fam_spans.setdefault(fam, []).append(i)
    for fam, idxs in fam_spans.items():
        color = DIAN if fam == 'latin' else GREEK
        y0 = top + idxs[0] * ROW_H + (ROW_H - 56) / 2.0
        fy = top + (idxs[0] * ROW_H + (idxs[-1] + 1) * ROW_H) / 2.0
        out.append(rect(fam_x, y0, fam_w, len(idxs) * ROW_H - 28, fill='#ffffff', stroke=color, sw=1.5))
        out.append(txt(fam_x + fam_w / 2.0, fy + 6, FAM_ZH[fam], 17, color, anchor='middle', family=SERIF))
        # 义符 → 语族：折线（先横、再竖、再横）
        out.append(line(X0 + 88, cy_zi, cx_zi + 30, cy_zi, color))
        out.append(line(cx_zi + 30, cy_zi, cx_zi + 30, fy, color))
        out.append(line(cx_zi + 30, fy, fam_x, fy, color))

    # 右：词根 + 例词
    for i, (fam, mor, words) in enumerate(rows):
        color = DIAN if fam == 'latin' else GREEK
        cy = top + i * ROW_H + ROW_H / 2.0
        out.append(line(fam_x + fam_w, cy, root_x, cy, color))
        out.append(rect(root_x, cy - 26, root_w, 52, fill='#ffffff', stroke=color, sw=1.5))
        out.append(txt(root_x + 14, cy + 8, mor, 22, color, family=SERIF))
        ls = _wrap(words)
        if len(ls) == 1:
            out.append(txt(word_x, cy + 5, ls[0], 14.5, INK, family=SANS))
        else:
            out.append(txt(word_x, cy - 6, ls[0], 14.5, INK, family=SANS))
            out.append(txt(word_x, cy + 15, ls[1], 14.5, INK, family=SANS))

    # 图例 + 脚注
    out.append(rect(X0, legend_y - 9, 11, 11, fill=DIAN, rx=2))
    out.append(txt(X0 + 18, legend_y, '拉丁（靛青）', 13, INK2, family=SANS))
    out.append(rect(X0 + 150, legend_y - 9, 11, 11, fill=GREEK, rx=2))
    out.append(txt(X0 + 168, legend_y, '希腊（紫）', 13, INK2, family=SANS))
    out.append(txt(X0 + 320, legend_y, '例词取自 docs/index.html 演示层', 11.5, INK3, family=SANS))
    out.append('</svg>\n')
    return ''.join(out)


# ---------------------------------------------------------------------------
# 产物清单 / 写盘 / --check 闸门
# ---------------------------------------------------------------------------
def build_all():
    """返回 {相对路径: 内容}。确定性输出（不含时间戳），否则 --check 无从比对。"""
    arts = {}
    for row in YIFU:
        arts['docs/assets/yifu-%s.svg' % row['slug']] = build_yifu(row)
    for row in ROOTS:
        arts['docs/assets/root-%s.svg' % row['slug']] = build_root(row)
    return arts

def main(argv):
    check = '--check' in argv
    arts = build_all()
    bad = 0
    for rel, content in sorted(arts.items()):
        path = os.path.join(HERE, '..', rel)
        old = None
        if os.path.exists(path):
            with open(path, encoding='utf-8') as f:
                old = f.read()
        if check:
            if old == content:
                print('  ok    %s' % rel)
            else:
                print('  漂移！ %s（仓库里那份与生成器不一致）' % rel)
                bad += 1
        else:
            with open(path, 'w', encoding='utf-8', newline='\n') as f:
                f.write(content)
            print('  %s  %s' % ('ok  ' if old == content else '写入', rel))
    if check:
        print('--check：%d 个产物，%d 处漂移' % (len(arts), bad))
        return 1 if bad else 0
    print('已生成 %d 个 SVG（来源 docs/assets/src/，本脚本不改来源）' % len(arts))
    return 0

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
