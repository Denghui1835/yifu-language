# 设计规范 · docs/DESIGN.md

> Issue #11 交付物。**纯文档：不写 CSS、不改页面。**
> 目标：**不看你那三张参考图，只读这份文字，做出来的东西就一致。**
> 每个取值都标了 〔现状 `index.html:行号`〕 或 〔新值〕，可逐条对照。

## 前提：这份规范站在哪一边

`docs/index.html` 现在**同时装着两套互相矛盾的设计语言**：

| | 早期「图谱漫游」（上半，:8–253） | 后加「玩法层」（下半，:254–447） |
|---|---|---|
| 圆角 | 14 / 13 / 12 / 11 / 10 / 9 / 8 / 7 / 99px / 50% | **2px** |
| 渐变、发光阴影 | 有 | **明确不要**（:256 自己写明了） |
| 字体 | 宋体 + 无衬线混用 | 宋体为主 |
| emoji | — | **无**（:256） |

**玩法层在 :254–258 自己声明了规则**：「遵循 2px 圆角、无渐变、无发光阴影、无 emoji」。
这是 `index.html` 里**唯一被明写过的设计规则**，且已被采用 20 处（`2px` 出现 20 次，是全文件最高频的圆角）。

**本规范以这一条为「底子」**：2px · 去渐变 · 去发光 · 去 emoji · 纸/墨五色。
「皮」（配色气质是否更"刻本"、疏密）等 Issue #10 定稿后可能微调，**但底子先立住**。

> ⚠️ **待 #10 定稿后只需复核两处**：① 色板气质；② 字号阶梯是否再收紧。
> **其余各节现在就能执行。**

---

## 零、先列出发现的不一致（本规范要消灭的东西）

| # | 不一致 | 现状（实测） | 本规范的处理 |
|---|---|---|---|
| 1 | **并排两套规则** | 上半有渐变+发光+大圆角，下半明令禁止 | 全站按下半（玩法层） |
| 2 | **圆角 11 种** | `2px`(20) `50%`(4) `99px`(3) `11px`(3) `12px`(2) `9px` `8px` `7px` `10px` `13px` `14px` `2px 2px 0 0` | 只留 **2px** 与 **50%** |
| 3 | **字号 25 种** | 10 / 10.5 / 11 / 11.5 / 12 / 12.5 / 13 / 13.5 / 14 / 14.5 / 15 / 16 / 16.5 / 19 / 20 / 25 / 26 / 27 / 30 / 32 / 34 / 36 / 44 / 50 | 收敛为 **12 级**（第二节） |
| 4 | **硬编码颜色** | **31 个 hex + 14 个 rgba** 散在样式里，不走令牌 | 一律走令牌；新增 9 个（第一节） |
| 5 | **发光阴影 7 处** | `.tab.on:59` `.fu.hot:92` `.hz.hot:106` `.root.hot:123` `.w.hot:136` `.disc:151` `.disc.pulse:154` | **废止**（要区分"选中"用底色/描边） |
| 6 | **渐变 1 处** | `.disc:149` 一个径向渐变用了 3 个色 `#fff8e6 #f3e0b0 #e8cf93`（描边另用 `#e0c98d:150`） | **废止**，改平涂 `--jin-bg` |
| 7 | **同义描边多值** | `#e6c8bd` 与 `#eed6cd` 都当"朱砂描边"；`#cbe0ec` 与 `#cfe0ea` 都当"靛青描边" | 各统一成一个令牌 |
| 8 | **间距无公因数** | 4/5/6/7/8/9/10/11/12/13/14/15/16/17/18/19/20/22/26/30/34/150px 混用 | **基数 4px**，只走 9 个档 |
| 9 | **字体栈首选不当** | `--sans:19` 第 2 位就是 `"Microsoft YaHei"`，Windows 必落它 | 见第四节 |
| 10 | **半透明面板** | header `rgba(247,244,238,.9):44`、`.tally rgba(255,253,248,.86):160`、`.notice code rgba(255,255,255,.7):286` | 改平涂 |

---

## 一、色板

### 1.1 既有令牌（**保留**，已定义在 `index.html:8–19`）

| 令牌 | 值 | 用途 | 现状去处 |
|---|---|---|---|
| `--paper` | `#f7f4ee` | 页面底 | `body:24` |
| `--paper2` | `#fffdf8` | 卡片／格底（**比纸更亮**） | `:51 :89 :121 …` |
| `--ink` | `#221f1b` | 正文 | `:25` |
| `--ink2` | `#6b6357` | 次文（释义、副标题） | `:51 :128` |
| `--ink3` | `#9c9385` | 弱文（脚注、meta、标签字） | `:48 :79` |
| `--zhu` | `#b8452f` | **朱砂 · 只给汉语侧** | `:82 :92 :96 …` |
| `--zhu-bg` | `#f6e6e0` | 汉语侧强调块底 | `:92 :203 :289 …` |
| `--dian` | `#2f6d8f` | **靛青 · 只给英语侧** | `:83 :123 :125 …` |
| `--dian-bg` | `#e2edf4` | 英语侧强调块底 | `:123 :189` |
| `--jin` | `#c2922c` | **金 · 只给中枢／强调** | `:56 :195 :385` |
| `--jin-bg` | `#f8efd8` | 金底 | `:197 :281` |
| `--line` | `#e3ddd1` | 分隔线／描边 | `:43 :51 :73` |

**三条铁律（不许破）**：

1. **朱砂只给汉语侧，靛青只给英语侧，金只给中枢／强调——不许交叉**（`:11 :13 :15` 的注释就是这么写的）。
2. 块底用 `--paper2`，**不要用 `#fff`**；页面底用 `--paper`。
3. 画线只用 `--line`，以及下面 `1.2` 的三个"底上的描边"。

### 1.2 新增令牌（把散落的硬编码收编）

| 新令牌 | 值 | 用途 | 顶替掉 |
|---|---|---|---|
| `--zhu-line` | `#eed6cd` | 朱砂底上的描边 | `#eed6cd:203,361` `#e6c8bd:242,289` |
| `--dian-line` | `#cfe0ea` | 靛青底上的描边 | `#cfe0ea:190,291,336` `#cbe0ec:243` |
| `--jin-line` | `#e8d5a5` | 金底上的描边 | `#e8d5a5:198,281,286,338` |
| `--zhu-ink` | `#6d4a3f` | 朱砂底上的文字 | `#6d4a3f:207,363`（顺带收 `#8d6a5f:205`） |
| `--dian-ink` | `#2f5570` | 靛青底上的文字 | `#2f5570:291` |
| `--jin-ink` | `#7a5a17` | 金底上的文字 | `#7a5a17:155,198,284,339`（顺带收 `#6d551f:282` `#9c7c36:156`） |
| `--on` | `#ffffff` | **深色块上的文字** | 11 处 `#fff`（`:58 :109 :139 …`） |
| `--ink-story` | `#3a352e` | 长文正文（比 `--ink` 略浅） | `#3a352e:214,366,432` |
| `--line2` | `#ded7c9` | 滚动条 | `#ded7c9:75` |

> `--greek`（**可选，给 `docs/assets/` 用**）：`#6f5b9e`。Issue #12 的谱系图用它区分「希腊来源」。
> **它只在矢量资产里用，页面 CSS 不引入**；若将来页面也要标希腊来源，再由本规范升格为正式令牌。

### 1.3 废止清单（本规范生效后**不得再出现**）

| 废止 | 现值 | 替换为 |
|---|---|---|
| 径向渐变 | `#fff8e6 #f3e0b0 #e8cf93`（`.disc:149`） | 平涂 `--jin-bg`，圆心字 `--jin-ink` |
| 彩色发光阴影 | `rgba(194,146,44,.28/.34/.55)` `rgba(184,69,47,.14/.3)` `rgba(47,109,143,.14/.32)` | **删**。选中态靠 `底 --*-bg + 描边 --*` |
| 内阴影 | `rgba(255,255,255,.85/.9)`（`.disc:151,154`） | 删 |
| 纸纹点阵 | `radial-gradient(rgba(0,0,0,.028) 1px …)`（`body::before:33–37`） | **保留唯一例外**（它是"纸"的质感，不是装饰发光） |
| 面板半透明 | `rgba(247,244,238,.9):44`、`rgba(255,253,248,.86):160`、`rgba(255,255,255,.7):286` | 平涂 `--paper` / `--paper2` |
| 方向性阴影 | `rgba(34,31,27,.13)`（`#detail:170`） | **保留唯一例外**（抽屉要浮起来，必须有一层） |
| 胶囊圆角 | `border-radius:99px`（`:52 :127 :219`） | `2px` |
| 同义多值 | `#e6c8bd` / `#cbe0ec` / `#6d551f` / `#9c7c36` / `#8d6a5f` | 见 1.2 |

---

## 二、字号阶梯

现状 **25 种**取值 → 收敛为 **12 级**。**改法：就近归级，逐处替换。**

| 级 | 值 | 用途 | 收编掉的现状值 |
|---|---|---|---|
| 1 | **11px** | 角标、脚注、meta、标签字 | `10` `10.5` `11` `11.5` |
| 2 | **12px** | 辅助说明（note、rel 项） | `12` `12.5` |
| 3 | **13px** | 次级正文、chip、小标签 | `13` `13.5` |
| 4 | **14px** | 小正文、按钮、下拉 | `14` `14.5` |
| 5 | **15px** | **正文（基准）** —— `body` 现在就是 15 | `15` |
| 6 | **16px** | 强调正文、输入框、主按钮 | `16` `16.5` |
| 7 | **19px** | 卡片标题、区块小标题 | `19` `20` |
| 8 | **26px** | 页面标题、区块大标题 | `25` `26` `27` |
| 9 | **30px** | 词头（详情／词卡的大词） | `30` `32` |
| 10 | **34px** | 卡片主字（闪卡正面） | `34` `36` |
| 11 | **44px** | 义符大字（`.fu .big`） | `44` |
| 12 | **50px** | 中枢字（`.disc .ch`）—— **只此一处** | `50` |

**降级规则（`@media` 内）**：窄屏把 9/10 两级各降一档（`:442 :443` 现在就是这么做的：`30→25`、`34→28`）。
**规范写法**：窄屏 = 上一级；即 `30→26`、`34→30`。

> 现在**没有** 22px 这一级；若将来需要，插在 19 与 26 之间，否则不许自造。

---

## 三、间距与圆角

### 3.1 间距：基数 **4px**

所有 `padding / margin / gap` 都取 4 的倍数。**允许的 9 个档**：

```
4 · 8 · 12 · 16 · 20 · 24 · 32 · 40 · 48
```

**归位规则**（现状 → 档）：

| 现状 | 归到 | 现状 | 归到 |
|---|---|---|---|
| 4 / 5 | **4** | 14 / 15 | **16** |
| 6 / 7 / 8 / 9 | **8** | 17 / 18 | **16** |
| 10 / 11 / 12 / 13 | **12** | 19 / 20 / 22 | **20** |

- 组件内边距（padding）**只准用 4 / 8 / 12 / 16**；块间距（margin/gap）**只准用 8 / 12 / 16 / 24**。
- 页面级留白用 **32 / 40 / 48**（现状 `30px 26px 90px:273`、`22px 26px 30px:174` → `32px 24px 48px`）。
- 列表底部"滚到底不贴边"的 `150px:71` → **`96px`**（12 的倍数，且比原来短）。

### 3.2 圆角：**只有一个值 `2px`**

| 取值 | 用途 | 现状处数 |
|---|---|---|
| **`2px`** | **所有卡片、按钮、标签、输入框、面板、分段器** | 20（已是多数） |
| **`50%`** | **只有正圆**：`圆盘 .disc`、`圆点 .sidehead i`、`关闭钮 .dclose`、`时间轴节点 .tlitem::before` | 4 |
| ~~`99px` 胶囊~~ | **废止** → `2px` | `:52 :127 :219` |
| ~~`7/8/9/10/11/12/13/14px`~~ | **废止** → `2px` | `:233 :239 :75 :161 :132 :101 :120 :88` |

- `border-radius:2px 2px 0 0`（`.tabx:379`）**允许**——它是"页签"，形状语义上就是上方圆。
- **边框宽度统一 `1px`**（现状各处都已是 `1px`、`1px dashed` 除外，保持）。

---

## 四、字体

### 4.1 现状

```
--serif:"Songti SC","STSong","SimSun","Noto Serif SC",serif;                                  (:18)
--sans :"PingFang SC","Microsoft YaHei","Hiragino Sans GB",system-ui,-apple-system,"Segoe UI",sans-serif;  (:19)
代码    :ui-monospace,Consolas,monospace;                                                       (:287)
```

### 4.2 三个问题

1. **`--sans` 第 2 位就是 `"Microsoft YaHei"`。** Windows 上绝大多数机器**没装** `PingFang SC`（那是 macOS 的字），
   于是**必落 YaHei**——观感偏"通用办公"，把质感拉下来。
2. **回退顺序是"平台字混排"，不是策略。** 谁先谁后没有理由。
3. **`--serif` 里 `"Noto Serif SC"` 排在最后**，Windows 一般没装，落到 `"SimSun"`（宋体，屏幕上偏瘦硬）。

### 4.3 新值

```css
--sans : "PingFang SC","HarmonyOS Sans SC","Source Han Sans SC","Noto Sans SC",
         "Microsoft YaHei","Hiragino Sans GB",system-ui,-apple-system,"Segoe UI",sans-serif;
--serif: "Songti SC","STSong","Source Han Serif SC","Noto Serif SC",
         "SimSun",Georgia,serif;
--mono : ui-monospace,"Cascadia Mono",Consolas,monospace;
```

### 4.4 回退策略（按这四层排，顺序即理由）

| 层 | 字体 | 说明 |
|---|---|---|
| ① macOS 系统字 | `PingFang SC` / `Songti SC` | 装了就最好看 |
| ② **开源可装字** | `HarmonyOS Sans SC`、`Source Han Sans/Serif SC`、`Noto Sans/Serif SC` | 免费。**装了就用**——这是本次改动的关键：把"好字"插在 YaHei 前面 |
| ③ Windows 桌面字 | `Microsoft YaHei` / `SimSun` | **保底**，不再当首选 |
| ④ 平台默认 | `system-ui` … `serif` | 兜底 |

**一句话记法**：**`Microsoft YaHei` 从第 2 位挪到第 5 位。**
想要「典籍」气质（#10 的 A 方向）时，**正文改用 `--serif`**，不要在无衬线栈里硬凑。

---

## 五、组件规格

**每个组件只给一种写法。** 下面每个都能直接抄。

### 5.1 按钮 `.btn`

**基准**：`2px` 圆角 · 描边 `--line` · 底 `--paper2` · 字 `--ink2` · `sans` · **14px** · `padding:12px 16px`。
**主按钮**：底与描边换 `--dian`，字 `--on`。**小号**：`padding:8px 12px`，字 13px。

```html
<button class="btn">普通</button>
<button class="btn primary">主按钮</button>
<button class="btn small">小号</button>
```
```css
.btn{border:1px solid var(--line);background:var(--paper2);color:var(--ink2);
     padding:12px 16px;border-radius:2px;font:14px var(--sans);cursor:pointer;white-space:nowrap}
.btn:hover{border-color:var(--dian);color:var(--dian)}
.btn.primary{background:var(--dian);border-color:var(--dian);color:var(--on)}
.btn.small{padding:8px 12px;font-size:13px}
```
**收编**：`.btn:302` `.chip:312` `.play:260` `.tab:50` `.quizopt:406` `.tabx:377` —— 它们都改成这一种，
差别只由 `.primary` / `.small` 两个修饰类表达，**不再各写一套**。

### 5.2 卡片 `.card`

**基准**：`2px` 圆角 · 描边 `--line` · 底 `--paper2` · `padding:12px 16px`。
**选中态**（hot）：**底换 `--*-bg` + 描边换 `--*`，不加发光**（汉 `--zhu`／英 `--dian`）。

```html
<div class="card hot">…</div>
```
```css
.card{border:1px solid var(--line);background:var(--paper2);border-radius:2px;padding:12px 16px}
.card.hot{border-color:var(--zhu);background:var(--zhu-bg)}          /* 汉语侧 */
.card.hot.eng{border-color:var(--dian);background:var(--dian-bg)}    /* 英语侧 */
```
**收编**：`.fu:86`（14px 圆角）`.root:119`（13px）`.w:131`（11px）`.thecard:388` `.wrongitem:417` `.cnode:354`。

### 5.3 标签 `.tag`

**基准**：`2px` 圆角 · `padding:3px 12px` · 字 **11px** · 描边与字 `--ink3`。
**确定态**：底 `--zhu` 或 `--dian`，字 `--on`。**居中方形字标**（26×26，如汉语／英语的「汉」「英」）用同一个类 + `.square`。

```html
<span class="tag">待定</span>
<span class="tag ok">已确认</span>
<span class="tag square h">汉</span>
```
```css
.tag{display:inline-block;border:1px solid var(--ink3);color:var(--ink3);background:transparent;
     padding:3px 12px;border-radius:2px;font-size:11px;letter-spacing:.06em;white-space:nowrap}
.tag.ok{background:var(--zhu);border-color:var(--zhu);color:var(--on)}
.tag.square{width:26px;height:26px;padding:0;display:flex;align-items:center;justify-content:center;
     font-family:var(--serif);font-size:14px;font-weight:600;border:0;color:var(--on)}
.tag.square.h{background:var(--zhu)} .tag.square.e{background:var(--dian)}
```
**收编**：`.badge:319` `.mtag:398` `.pill:350` `.root .src:126` `.rel span:218` `.tag:232`。

### 5.4 提示条 `.notice`

**基准**：`2px` 圆角 · `padding:16px 16px` · 字 **13px** · 三态各一套色。

| 态 | 底 | 描边 | 字 |
|---|---|---|---|
| 默认（金） | `--jin-bg` | `--jin-line` | `--jin-ink` |
| `err`（朱砂） | `--zhu-bg` | `--zhu-line` | `--zhu-ink` |
| `info`（靛青） | `--dian-bg` | `--dian-line` | `--dian-ink` |

```html
<div class="notice">默认是金的提示。</div>
<div class="notice err">出错用朱砂。</div>
<div class="notice info">说明用靛青。</div>
```
```css
.notice{border:1px solid var(--jin-line);background:var(--jin-bg);color:var(--jin-ink);
        border-radius:2px;padding:16px;font-size:13px;line-height:1.9}
.notice.err{border-color:var(--zhu-line);background:var(--zhu-bg);color:var(--zhu-ink)}
.notice.info{border-color:var(--dian-line);background:var(--dian-bg);color:var(--dian-ink)}
```
**收编**：`.notice:280` `.empty:364` `.xref:200` `.furow:360` `.tally:158`。

### 5.5 分段器 `.seg`

**基准**：外层容器 `2px` 圆角 + `--line` 描边 + `--paper2` 底 + `padding:12px 16px`；
每段 `padding:8px 12px`、`2px` 圆角，**段的类型由底色区分**（词根 `--dian-bg`／前缀 `--jin-bg`／其余 `--paper`）。

```html
<div class="seg">
  <span class="segp root"><b>aqua</b><i>root · 词根</i></span>
  <span class="segp"><b>aquatic</b><i>词</i></span>
</div>
```
```css
.seg{display:inline-flex;gap:8px;flex-wrap:wrap;background:var(--paper2);
     border:1px solid var(--line);border-radius:2px;padding:12px 16px}
.segp{border-radius:2px;padding:8px 12px;text-align:center;background:var(--paper);border:1px dashed var(--line)}
.segp.root{background:var(--dian-bg);border:1px solid var(--dian-line)}
```
**收编**：`.seg:331` `.segp:333` `.tabsx:376` `.tabx:377` `.tabs:49` `.plays:259`。

---

## 六、怎么用这份规范

1. **看到** `radius` 不是 `2px`／`50%` → **错**。
2. **看到** `font-size` 不在 12 级里 → **错**。
3. **看到** 间距不是 4 的倍数 → **错**。
4. **看到** `box-shadow` 带颜色、或 `linear/radial-gradient`（纸纹那一处除外） → **错**。
5. **看到** `#` 开头的颜色（`:root` 那 12 个令牌除外） → **错**，去 `1.2` 找对应令牌。
6. **看到** 朱砂用在英语侧、靛青用在汉语侧 → **错**。

## 七、本卡没做的

- **没有改动 `docs/index.html`**（验收要求）。
- **没有写 CSS、没有改页面** —— 本卡只出规范；照规范重构视觉层是「视觉层重构」那条卡的事。
- 第 4 条（字体栈）与第 5 条（组件）**现在就能落地**；
  第一节（色板气质）与第二节（字号是否再收紧）**待 #10 定稿后复核一次**。
