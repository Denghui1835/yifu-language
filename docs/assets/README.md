# 义符 · 字形演变与词根谱系资产

> Issue #12 的交付物。本目录里的 `*.svg` **全是生成的产物，不要手改**（手改会被闸门抓到）。
> 改版式或加字，改 `data/build_hz_assets.py` 里的表，然后重跑（见文末）。

## 这是什么

产品要讲的是「汉语义符 ↔ 英语词根」的对应。但汉语侧原先只显示一个静态楷体字，
**义符从甲骨一路走到今天的那条线，一直没被画出来**；英语侧也只写着几个词根字母。
这里就是补上那两样：

| 文件 | 内容 |
|---|---|
| `yifu-shui.svg` | 水（氵）的四段字形演变 |
| `yifu-shou.svg` | 手（扌）的四段字形演变 |
| `yifu-xin.svg`  | 心（忄）的四段字形演变 |
| `yifu-mian.svg` | 宀 的四段字形演变 |
| `yifu-yan.svg`  | 言（讠）的四段字形演变 |
| `yifu-mu.svg`   | 木 的四段字形演变 |
| `root-water.svg` | 水 ↔ aqua / mar / hydr 的词根谱系（拉丁 vs 希腊） |
| `root-hand.svg`  | 手 ↔ manu / chiro 的词根谱系 |
| `root-heart.svg` | 心 ↔ cord / psych / path 的词根谱系 |
| `src/` | 上列演变图的**字形来源**（17 个 SVG，只读，见下节） |

六张演变图，每张一行四格：**甲骨文 → 金文 → 小篆 → 楷书**。

## 字形出处（这张卡的红线：字形演变不许编）

`src/` 下 17 个字形全部取自 **Wikimedia Commons**，**授权均为 Public domain**。
逐条可查（点开即见文件页与其描述）：

| 字 | 甲骨文 | 金文 | 小篆 |
|---|---|---|---|
| 水 | [水-oracle.svg](https://commons.wikimedia.org/wiki/File:%E6%B0%B4-oracle.svg) | [水-bronze.svg](https://commons.wikimedia.org/wiki/File:%E6%B0%B4-bronze.svg) | [水-seal.svg](https://commons.wikimedia.org/wiki/File:%E6%B0%B4-seal.svg) |
| 手 | **（未找到）** | [手-bronze.svg](https://commons.wikimedia.org/wiki/File:%E6%89%8B-bronze.svg) | [手-seal.svg](https://commons.wikimedia.org/wiki/File:%E6%89%8B-seal.svg) |
| 心 | [心-oracle.svg](https://commons.wikimedia.org/wiki/File:%E5%BF%83-oracle.svg) | [心-bronze.svg](https://commons.wikimedia.org/wiki/File:%E5%BF%83-bronze.svg) | [心-seal.svg](https://commons.wikimedia.org/wiki/File:%E5%BF%83-seal.svg) |
| 宀 | [宀-oracle.svg](https://commons.wikimedia.org/wiki/File:%E5%AE%80-oracle.svg) | [宀-bronze.svg](https://commons.wikimedia.org/wiki/File:%E5%AE%80-bronze.svg) | [宀-seal.svg](https://commons.wikimedia.org/wiki/File:%E5%AE%80-seal.svg) |
| 言 | [言-oracle.svg](https://commons.wikimedia.org/wiki/File:%E8%A8%80-oracle.svg) | [言-bronze.svg](https://commons.wikimedia.org/wiki/File:%E8%A8%80-bronze.svg) | [言-seal.svg](https://commons.wikimedia.org/wiki/File:%E8%A8%80-seal.svg) |
| 木 | [木-oracle.svg](https://commons.wikimedia.org/wiki/File:%E6%9C%A8-oracle.svg) | [木-bronze.svg](https://commons.wikimedia.org/wiki/File:%E6%9C%A8-bronze.svg) | [木-seal.svg](https://commons.wikimedia.org/wiki/File:%E6%9C%A8-seal.svg) |

**诚实交代一句**：这些是 Commons 上已整理好的字形文件，我们**没有**再回到原始拓片、器铭、
或《说文》各本去逐字核对笔画。也就是说，本目录证明的是「这一格画的是哪个已发表的字形」，
**不是**「这个字形在学术上毫无争议」。要做到后者成本极高，超出本卡范围。

## 一个刻意的缺口：手 · 甲骨文

「手」那张图的甲骨文格是**空的**（虚线框，写明「未找到可靠字形 · 不补」）。

查证过程：Commons 上有 `手-bronze`、`手-seal`，以及一个 `手-ancient.svg`。
但那个 `-ancient` 描述写的是 **"Shuowen ancient script"（《说文》古文）**——**不是甲骨文**。
用《说文》古文冒充甲骨文，就成了编造。

按本卡红线「查不到就只画到能查到的年代为止……宁可少一格，不许拿想象填一格」，
这一格就留空。**空着本身也是内容**：它说明我们没有外推。

## 楷书那一格是怎么来的

楷书**不是**从字形库里取的，而是拿**真的字**（Unicode 里的「水/手/心/宀/言/木」，
也就是今天的正字）用**楷体字体**渲染的。字体栈：

```
"Kaiti SC","STKaiti","KaiTi","Kaiti TC","SimSun",serif
```

（Windows 上会落到 `KaiTi`，macOS 落到 `Kaiti SC`。）

## 词根谱系图的依据

- **拉丁 / 希腊的归属**是词典级常识，不涉争议：
  `aqua`(水)、`mar`(海)、`manu`(手)、`cord`(心) 属**拉丁**；
  `hydr`、`chiro`、`psych`、`path` 属**希腊**。图里用颜色区分并配图例。
- **例词全部取自 `docs/index.html` 的演示层**（const DATA 的 30 词），
  不是另找的 — 所以图上出现的词，产品里本来就讲得到。

## 配色（待 Issue #11 归口）

沿用 `docs/index.html` 的既有令牌：朱砂 `#b8452f`（汉语侧）、靛青 `#2f6d8f`（英语侧）。
谱系图里区分拉丁/希腊时，用了：

- 拉丁 = 靛青 `#2f6d8f`（既有）
- 希腊 = 紫 `#6f5b9e`（**本卡新加的提议值**，既有色板里没有这一号）

**这个紫是临时的**，最终该用哪一号由 `docs/DESIGN.md`（Issue #11）定。
本卡画风也**尚未**与 #10 选定的方向对齐 —— #10 还没定稿，先出结构、后套皮。

## 生成方式

```bash
python data/build_hz_assets.py          # 重新生成 docs/assets/*.svg
python data/build_hz_assets.py --check  # 只校验产物与生成器是否还一致（防漂移）
```

- **版式只写一份**（在这个脚本里），九张图共用，改一处即改九张。
- 字形**不重绘**：脚本把 `src/` 里的源文件按 data URI **原样内嵌**，
  所以不受各源文件坐标系不一致（有的 `viewBox 0 0 300 300`、有的靠 `<g transform>` 平移）影响，**画不歪**。
- `src/` 只读，脚本不改它。

## 本卡没做的（留给别的卡）

- **没有接入页面** —— 接进详情抽屉是另一条卡的事；本卡一行 `docs/index.html` 都没动。
- **没写 JS、没改任何页面**。
- 画风与 #10 的最终方向对齐、以及「紫」的归口，等 #10 / #11。
