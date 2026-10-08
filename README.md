# 义符

> 用母语的逻辑学外语——把汉语的偏旁部首和英语的词根词缀接起来，
> 像看汉字从甲骨文长成今天这样，也看着英语单词从拉丁语长成今天这样。

**当前状态：阶段零（机制验证）**。产品规划书与交互式演示已出，核心假设尚待实证。

---

## 一句话

汉语母语者脑子里装着一套用了十几年的「义类识别器」——看到「氵」就知道和水有关，
看到「扌」就知道和手有关。这套系统是免费的、已经装好的，但从没被用来对接外语。

**义符**要做的就是把汉语义符与英语词根挂到同一个义类节点上：

| 义类 | 汉语义符 | 英语词根 | 例词 |
|---|---|---|---|
| 水·液体 | 氵 水 | aqua-（拉）, hydr-（希）, mar-（拉） | aquarium, hydrogen, marine |
| 手·操作 | 扌 手 | manu-（拉）, chiro-（希） | manual, manufacture, chiropractor |
| 心·情感 | 忄 心 | cord-（拉）, psych-（希）, path-（希） | record, courage, sympathy |

别人教规则，我们调用本能。

---

## 核心机制

### 一、三层数据模型

```
义类（语言无关的语义原子）
  ├─ 汉语侧：义符（氵 扌 忄 …）
  └─ 英语侧：词根词缀（aqua- manu- cord- …）
        └─ 词条
```

义类节点不绑定任何语言——这是预留的多语种扩展口子。

### 二、两条平行的演变线

不是讲一个静态的词源故事，而是把两条演变时间轴并排放：

- **汉**：甲骨文 → 金文 → 小篆 → 隶变 → 楷书 → 偏旁（水 → 氵）
- **英**：拉丁／希腊 → 古法语 → 中古英语 → 现代（拉丁 cor → 古法语 corage → courage）

「演变」本身是最强的记忆钩子——人们记得住故事，记不住条目。

### 三、词表范围

锁定 **高考 3500 词**，不做大词库。卖点是打破 A–Z 字母序、改按义类重排。

---

## 词源实测数据（2026-10）

覆盖率**不能靠正则猜**。本轮改用机器可读词源库 [kaikki.org](https://kaikki.org)
（维基词典的结构化导出）逐词判定，3841 词全部落地：

| 类别 | 词数 | 占比 |
|---|---:|---:|
| 古典来源（拉丁／古希腊） | 1815 | 47.3% |
| 罗曼斯来源（古法语等，多可追至拉丁） | 216 | 5.6% |
| **→ 可挂古典词根（合计）** | **2031** | **52.9%** |
| 日耳曼底层 | 1483 | 38.6% |
| 其它来源 | 4 | 0.1% |
| 抓不到词源 | 323 | 8.4% |

> **表里数字怎么来的（复算命令，2026-10 复核）**
> ① 各类词数与总数：
> `python -c "import json,collections;print(dict(collections.Counter(json.load(open('data/etym_class.json',encoding='utf-8')).values())))"`
> → `{'classical': 1815, 'germanic': 1483, 'unknown': 323, 'romance': 216, 'other': 4}`
> ② 总条目数：
> `python -c "import json;print(len(json.load(open('data/gaokao3500.json',encoding='utf-8'))))"`
> → `3841`
> ③ 占比 = 该类词数 ÷ 3841。合计 = 古典 + 罗曼斯 = 1815 + 216 = 2031。

抽查 30 词逐条核对演变链（记录见 `data/demo_etym_audit.md`，含逐词原始出处），
**29/30 与维基词典一致，查出并修正 2 处**。分类定性另做过一轮 51 词抽查、结论
51/51 一致，但**该轮记录未入库、不可复现**，故此处不作为证据引用。

**长度分层**（越长越可拆，但会到顶）：

| 词长 | 可挂古典词根 |
|---|---:|
| 1–3 字母 | 27.9% |
| 4–6 字母 | 47.6% |
| 7–9 字母 | 63.0% |
| 10 字母以上 | 60.0% |

短词是日耳曼基础词（go、eat、house），本来就不难；长词才是学生的真痛点，
而长词六成上下可拆。所以对外话术不能说「3500 词全覆盖」（不实），
要说「**专治记不住的长难词**」（真实，而且更有力）。

> ⚠️ 曲线在 7–9 字母达峰后**趋于平缓**，并非「越长越可拆」。10 字母以上的词里
> 合成词与专名占比升高，古典词根比例不再上升。早期正则版给出的
> 「4 字母以上 40%／7 字母以上 60%／10 字母以上 70%」全部作废。

**义类分桶（估算，勿当结论）。** 2031 个可挂古典词根的词里，按现有 54 个义类做
词根匹配（`data/yilei_roots.py` 的 `ROOTS` 表，`grep -c "^ '[^']*':\[" data/yilei_roots.py` 得 54；
**其中只有 43 个真的分到了词，另 11 个为空**，数 `data/yilei_buckets.json` 的键即知），
**只有 335 个能归入**，1696 个匹配不上。手工抽检 60 个归入词，
精度仅约 **70%**（该轮抽检记录未入库）——3 字母词根歧义严重（`par` 既是「相等」又出现在
prepare／part 里，`med` 既是 medicus「治」又出现在 medius「中」里），
启发式修不掉。

**这本身是重要结论**：义类层必须是**人工校订的词典数据**，不能靠推导生成。
335 只说明「方向可行、缺口巨大」，不代表最终覆盖率。

> 义类数 = `data/yilei_roots.py` 里 `ROOTS` 字典的顶层键数（该表原在 `analyze_roots.py`，
> 后抽成独立模块与卡片生产流水线共用）：
> `python -c "import ast;t=ast.parse(open('data/yilei_roots.py',encoding='utf-8').read());print(len([n for n in t.body if isinstance(n,ast.Assign) and getattr(n.targets[0],'id','')=='ROOTS'][0].value.keys))"` → `54`
> 归入词数 335 出自 `data/yilei_buckets.json`：`python -c "import json;d=json.load(open('data/yilei_buckets.json',encoding='utf-8'));print(sum(len(v) for v in d.values()))"` → `335`。

### 四、扩到雅思词汇：义符命中率反而更高

词汇范围从高考 3500 扩到雅思后，用同一条管线实测（雅思词表 3563 词）：

| | 高考 3500 | 雅思词表 |
|---|---:|---:|
| 可挂古典词根 | 2031（52.9%） | **2449（68.7%）** |
| 日耳曼底层 | 38.6% | 25.0% |
| 抓不到词源 | 8.4% | 6.0% |

长度分层差距更明显：

| 词长 | 高考 | 雅思 |
|---|---:|---:|
| 1–3 字母 | 27.9% | 35.8% |
| 4–6 字母 | 47.6% | 60.3% |
| 7–9 字母 | 63.0% | **78.9%** |
| 10 字母以上 | 60.0% | **80.1%** |

**雅思词汇比高考词汇更适合义符机制**——高出约 16 个百分点，长词区间接近八成可拆。
原因是学术英语的拉丁／希腊借词密度天然高于日常英语（高考词表里有大量 go／eat／house
这类日耳曼基础词）。

两份词表**只重叠 1705 词**（高考独有 2136、雅思独有 1858），合起来约 5699 词——
扩到雅思是真扩量，不是把同一批词换个封面。比对键取词头 `hw`（与 `data/check_data.py`
的查词键一致），用
`python -c "import json;g=json.load(open('data/gaokao3500.json',encoding='utf-8'));i=json.load(open('data/ielts_words.json',encoding='utf-8'));a=set(r['hw'].lower() for r in g);b=set(r['hw'].lower() for r in i);print(len(a&b),len(a-b),len(b-a),len(a|b))"`
数出，输出为 `1705 2136 1858 5699`。

> 这条数据支持一个产品判断：义符机制在**学术／留学类词汇**上比在高考词汇上更成立。

---

## 目录结构

```
├── gongwen.py                公文格式 docx 渲染引擎（仿宋三号/28磅/表格四号/目录域/页码），
│                             规划书与参赛材料共用这一套排版机器
├── build_plan.py             规划书生成脚本；内容全部结构化在文件顶部的 C 列表里，
│                             改内容只动那个列表再重跑，不用碰排版代码
│                             产出到 D:\AI coding\规划书\义符_产品规划书_v1.docx（公文格式）
├── docs/                     GitHub Pages 的发布源
│   ├── index.html            交互演示（单文件、零依赖、离线可跑）：义类漫游 / 词根拆解器 / 义类词卡
│   ├── pipeline.html         词源管线说明页
│   └── data/                 cards.json（义类词卡）、lookup.json（查词索引），由 data/ 下脚本产出
├── 大赛/                     AI+教育大赛：生成脚本与官方指南（**成果不落这里**）
│   ├── build_entry.py        参赛内容介绍生成脚本（只改顶部 C 列表）
│   ├── to_pdf.py             docx -> PDF（走本机 WPS 的 COM，顺带刷新目录域）
│   ├── to_html.py            docx 同源 -> 网页版（import build_entry.C，内容不另写一份）
│   └── *.pdf                 大赛官方指南原文
│
│   ★ 产物统一落 D:\AI+应用技能大赛\义符参赛\（那是参赛工作目录，按编号分桶）：
│     00_倒排期与策略.md  01_对照测试/  02_作品介绍文档/  03_演示视频/
└── data/
    ├── lazuli_raw.txt        原始词表（3897 行，词+音标+释义）
    ├── build_wordlist.py     解析原始词表 -> gaokao3500.json
    ├── gaokao3500.json       高考 3500 词结构化数据（词/音标/释义/词头/类型），3841 条
    ├── fetch_raw.py          从 kaikki.org 抓逐词词源页 HTML 切片 -> etym_raw/
    ├── etym_parse.py         离线解析 HTML：词性分段、词源树、内嵌 JSON 祖先链
    ├── analyze_etym.py       逐词定性（classical/romance/germanic/unknown）+ 派生回退
    ├── yilei_roots.py        义类词根表（ROOTS，54 个义类）；卡片生产与统计共用这一份
    ├── analyze_roots.py      按词根统计覆盖率（用上面的 ROOTS 表）
    ├── bucket_yilei.py       按义类分桶（启发式，精度约 70%，见上）
    ├── build_cards.py        产出义类词卡 -> docs/data/cards.json
    ├── build_lookup.py       产出查词索引 -> docs/data/lookup.json
    ├── check_data.py         数据卫生检查；退出码非 0 即有问题
    ├── etym_class.json       产出：词 -> 类别
    ├── etym_trees.json       产出：词 -> 祖先链节点（给演变时间轴用）
    ├── yilei_buckets.json    产出：义类 -> 词表
    ├── ielts_raw.txt         雅思词表源（3563 词，词|词性|释义|例句）
    ├── ielts_coverage.py     雅思词表跑同一条管线，实测义符命中率
    ├── ielts_class.json      产出：雅思词 -> 类别
    ├── ielts_trees.json      产出：雅思词 -> 祖先链
    ├── demo_etym_audit.md    演示 30 词的词源核对记录（含逐词出处）
    └── demo_etym_audit.tsv   同上，逐词原始记录
```

`data/etym_raw/`（约 90MB 的抓取缓存）不入库，随时可重抓。

## 跑起来

> **环境要求：Python 3.6+**。脚本只用标准库，唯一限制版本的是 f-string 语法（3.6 引入）；
> 本机实测 **3.13.15** 跑通。
> - 例外 1：`build_plan.py` 需先 `pip install python-docx`。
> - 例外 2：`fetch_raw.py`、`ielts_coverage.py` 需联网。

在线体验：**https://denghui1835.github.io/yifu-language/**

```bash
# 演示：双击 docs/index.html 即可，不需要服务器、不需要联网
python build_plan.py          # 重新生成规划书（输出到 D:\AI coding\规划书\）
python 大赛/build_entry.py    # 生成参赛内容介绍（输出到 D:\AI+应用技能大赛\义符参赛\02_作品介绍文档\）
python 大赛/to_pdf.py "D:/AI+应用技能大赛/义符参赛/02_作品介绍文档/义符_参赛内容介绍.docx"  # 转 PDF
python 大赛/to_html.py        # 同一份内容生成网页版（发链接给同学看，不必传 docx）

# 词源管线（重跑顺序）
python data/fetch_raw.py      # 抓词源页（需联网，kaikki.org 可直连）
python data/analyze_etym.py   # 定性
python data/analyze_etym.py --dump 30
python data/bucket_yilei.py   # 义类分桶
```

---

## 已完成 / 待办

**已完成**

- [x] 产品规划书 v1.1（12 章 + 4 附录，含义类映射表、词条数据模型、阶段零对照实验方案、风险与路线图）
- [x] 阶段零交互演示：3 义类（水／手／心）× 10 词 = 30 词
- [x] 高考 3500 词表入库并结构化（3841 条）
- [x] 词源管线：kaikki 逐词抓取 → 解析 → 定性（演示 30 词逐条核对，29/30 一致，修正 2 处）
- [x] 长度分层统计，拿到可对外用的真数
- [x] 义类分桶首轮（估算，精度约 70%）
- [x] AI+教育大赛参赛内容介绍（32 页 / 17 表，八章严格照报名系统的指定小标题）

**待办**

- [ ] 义类层人工校订：现有 54 义类只覆盖 335 词，需扩表并逐词定根（**这是数据主工程量**）
- [ ] 阶段零对照测试：义符对齐是否真的提高记忆保持率（**这是最高风险项**）
- [ ] 演示中的演变链逐条核对词源后再上线
- [ ] 大赛报名：官网注册 -> 选赛道 -> 下载申报表签字 -> 上传材料（**学生团队无需盖章**，只有负责人签字）
- [ ] 大赛演示视频（≤10 分钟，概述≤2min / 核心演示≤6min / 效果总结≤2min）

---

## 数据来源与致谢

- **高考 3500 词表**：来自
  [LazuliKao/brochure-of-vocabularies](https://github.com/LazuliKao/brochure-of-vocabularies)
  的 `raw.txt`。⚠️ 早期用的 [pluto0x0/word3500](https://github.com/pluto0x0/word3500)
  上游数据本身有截断错误（`acute` 成了 `acut`），已弃用。
- **词源数据**：来自 [kaikki.org](https://kaikki.org)（维基词典机器可读导出）。
- **字源**：参照《说文解字》等公开来源。

**入库铁律：词源和字源是硬知识，出处存疑的内容绝不入库。**
任何一条典故都必须能指回一个可信来源。宁可少，不可错。

演示中的演变链按词源学常识编写，**入库前须逐条核对**。

## 许可

暂未确定。词表与词源数据部分遵循上游许可（MIT / CC BY-SA）。