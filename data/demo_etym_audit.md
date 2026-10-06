# 演示演变链词源核对（2026-10-07）

依据：kaikki.org（维基词典机器可读导出，CC BY-SA）。
逐词原始记录见同目录 `demo_etym_audit.tsv`（含祖先链与正文原文）。
核对对象：`docs/index.html` 阶段零演示的全部 30 词。

**结论：29/30 与维基词典一致，发现并修正 2 处。**

---

## 修正 1（事实错误）——`maritime`

- **原演示说法**：「同样来自拉丁 mare，只是走了一条更长的路：maritimus 直接进了英语，
  **没经过法语**。」
- **kaikki 原文**：`Borrowed from Middle French maritime, from Latin maritimus.`
- **判**：错。maritime 恰恰是**经中古法语**进来的；而且 marine 也经法语
  （`Middle English marin, borrowed from Middle French marin, from Latin marinus`）。
  所以「一个经法语、一个不经法语」的对立不成立。
- **已改为**：真正的区别是拉丁语本就有两个「海的」形容词——
  `marinus`（海里的）→ marine，`maritimus`（海边、沿海的）→ maritime，两条路都经中古法语。

## 修正 2（表述不严）——`hydrogen` / `hydrate` 条下的历史陈述

- **原演示说法**：「希腊词根是**文艺复兴时期**大批涌进学术圈的。」
- **判**：作为一般趋势成立，但 hydrogen 是 1783 年拉瓦锡新造的词，
  hydrate 亦属近代科学造词，直接归到「文艺复兴时期」不准。
- **已改为**：「希腊词根从文艺复兴起大批涌进学术圈，到近代给新发现的东西命名时，
  用希腊词根几乎成了规矩（hydrogen 是 1783 年拉瓦锡照这个规矩造的）。」

---

## 逐词判定

| 词 | 演示说法 | 核对 |
|---|---|---|
| aquarium | 拉丁 aqua + -arium | ✓ `Latin aquārium, from aqua + -arium` |
| aquatic | aqua | ✓ `Latin aquaticus, from aqua`（经中古法语 aquatique） |
| aqueduct | aqua + duct(ducere) | ✓ `Latin aquaeductus, aqua + dūcō` |
| hydrate | 希腊 hydor | ✓ `Ancient Greek ὕδωρ → ὑδρο-` |
| hydrogen | hydro + gen(genos) | ✓ 同上（经法语 hydro-） |
| dehydrate | de + hydr | ✓ |
| marine | 拉丁 mare | ✓ `Middle French marin ← Latin marinus ← mare` |
| maritime | 拉丁 maritimus | ⚠️ 见修正 1 |
| submarine | sub + marine | ✓ `sub- + marine` |
| aquamarine | aqua marina | ✓ `From Latin aqua marīna ("sea water")` |
| manual | 拉丁 manus | ✓ `Latin manuālis, from manus` |
| manufacture | manu + fact(facere) | ✓ `Medieval Latin manūfactūra, manū + factus` |
| manuscript | manu + script(scribere) | ✓ `Medieval Latin manūscrīptus, manū + scrīptus` |
| manicure | mani + cure(cura) | ✓ `French manucure ← Latin manus + cūra` |
| manipulate | 拉丁 manipulus(manus+ple) | ✓ `French manipulation ← Latin manipulus`；拉丁 `manipulus` 释作 `manus + root of pleō（填满）`，即「一把」 |
| emancipate | e- + mancipium(manus) | ✓ `Latin ēmancipātus`；manceps ← manus + capere |
| chiropractor | 希腊 cheir + praktikos | ✓ `Ancient Greek χείρ + πρᾶξις` |
| chirography | chiro + graphy | ✓ `Ancient Greek χειρόγραφος` |
| surgeon | 希腊 cheirourgos(cheir+ergon) | ✓ `Vulgar Latin *chīrurgiānus ← Latin chīrūrgia ← Greek` |
| manage | 意 maneggiare ← 拉丁 manus | ✓ `Vulgar Latin *manizāre, Old Italian maneggiare` |
| courage | 古法 cuer + -age ← 拉丁 cor | ✓ `Old French corage ← Vulgar Latin *corāticum ← Latin cor` |
| cordial | 拉丁 cor | ✓ `Medieval Latin cordiālis, from cor` |
| record | 拉丁 cor (cord-) | ✓ `[Verb] Old French recorder ← Latin recordārī ("remember, call to mind"), from re- + cor ("heart; mind")` |
| accord | 拉丁 cor (cord-) | ✓ `[Verb] Old French acorder ← Vulgar Latin *accordāre ← Latin concordāre（ad- 替换了 con-），远亲英语 heart` |
| discord | 拉丁 discordia (dis+cor) | ✓ `Latin discordia ← discors` |
| concord | 拉丁 concordia (con+cor) | ✓ `Latin concordia ← concors ← con- + cor` |
| psychology | 希腊 psyche + logia | ✓ `Renaissance Latin psychologia ← Greek ψυχή + -λογία` |
| psychiatrist | psych + iatros | ✓ `psychiatry + -ist`；kaikki 对 psychiatry 只记到 `Borrowed from French psychiatrie（1846 年首见）`，再往前（ψυχή「灵魂」+ ἰατρός「医者」）是通行词源书所载，kaikki 英文本页未展开 |
| sympathy | 希腊 sympatheia(sym+pathos) | ✓ `Late Latin sympathīa ← Greek σῠμπᾰ́θειᾰ` |
| empathy | 希腊 empatheia(en+pathos) | ✓ `Ancient Greek ἐμπάθεια (ἐν + πάθος)` |

## 复核方法

演示词多不在高考 3500 表内，故单独抓取：复用 `fetch_raw.py` 的抓取与缓存，
用 `etym_parse.py` 解析 kaikki 页面。需要复核时重跑本文档开头所述脚本即可。