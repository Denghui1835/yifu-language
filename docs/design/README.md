# 产品概念图（`docs/design/`）

这个目录放**产品概念图**——一眼能看懂「义符」在干嘛的图：

> 汉语侧一个义符（如 氵），和英语侧一串词根（如 aqua- / hydr- / mar-），
> 底下连到同一个义类节点（水 · 液体·流动）。

一共三张，对应数据层里的三个义类：

| 文件 | 义类 | 汉语义符 | 英语词根 |
|---|---|---|---|
| `concept_water.png` | 水 · 液体·流动 | 氵 / 水 | aqua- · hydr- · mar- |
| `concept_hand.png`  | 手 · 操作·拿取 | 扌 / 手 | manu- · chiro- |
| `concept_heart.png` | 心 · 情感·心念 | 忄 / 心 | cord- · psych- · path- |

## 为什么是「代码绘制」而不是 AI 生图

凡图上**必须带可读文字**的图，都不能用 SD1.5 之类生图模型——它写字必乱码。
正解是用代码画：字是真的、零乱码、能重跑、结果可复现。

## 红线

1. **图上每个字、每个词全部来自仓库既有数据**，无一处杜撰。
   数据源是 `data/yifu_cards.json`（由 `docs/index.html` 的 `const DATA` 生成，
   并经 Issue #25 裁定）。脚本**只读**它，不改。
2. **配色只用 `docs/DESIGN.md` 的令牌**，且守三条铁律：
   朱砂（`--zhu`）只给汉语侧，靛青（`--dian`）只给英语侧，金（`--jin`）只给中枢。
3. 本脚本**不改任何页面、不改任何数据**，产物只落在这个目录。

## 怎么重跑

```bash
pip install pillow
python data/build_concept.py            # 产出到 docs/design/
python data/build_concept.py --out D:/x  # 换落点
```

生成器在 `data/build_concept.py`。它只用标准库 + Pillow，字体走本机已装字
（楷体写汉字/义符，宋体写中文说明，Georgia 写英文），按候选表逐个找，
全找不到才报错（不静默降级成方块）。
