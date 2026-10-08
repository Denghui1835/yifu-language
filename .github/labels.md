# 标签说明

> 这份文件解释仓库里每个标签：**什么时候用、谁负责贴、贴完之后状态怎么流转。**
>
> 标签分两大类：
> - **流程状态**——一个 Issue 从创建到合并走的路。**同一时间只贴一个**，状态一变就换。
> - **归类标签**（来源 / 领域 / 类型）——可叠加，说明这条任务是什么、归谁管。

---

## 一、流程状态（一个 Issue 的生命线）

```
backlog ──→ ready ──→ in_progress ──→ needs-review ──→ approved ──→ done
                          │   ↑
                          │   └── needs-clarification（退回 Planner）
                          └──────→ blocked（被别的事挡住，暂时推不动）
```

| 标签 | 什么时候用 | 谁贴 | 贴完之后怎么流转 |
|---|---|---|---|
| `backlog` | 任务刚建、还没排期 | 任务模板自动 | 写清后由 Planner 换成 `ready` |
| `ready` | 已写清、可以被人认领 | Planner／维护者 | 有人评论「我领这个」→ 换成 `in_progress` |
| `in_progress` | 已被认领、正在做 | 机器人（认领时自动） | 交了 PR → `needs-review`；做不下去 → `blocked` |
| `needs-review` | 已交 PR、等审核 | 交活的人／机器人 | 通过 → `approved`；打回 → 退回 `in_progress` |
| `approved` | 已批准，待合并 | 审核人 | 合并后 → `done`，Issue 自动关闭 |
| `done` | 已完成并合并（main 验证通过） | 集成者／机器人 | 终态 |
| `blocked` | 被别的事挡住，暂时推不动 | 做的人／机器人 | 阻塞解除 → 回到 `in_progress` |
| `needs-clarification` | 验收标准不清，做的人判断不了「什么算做完」 | **认领的人自己** | 退回 Planner；澄清后 Planner 重新给 `ready` |
| `needs-research` | 动手前需要先调研 | Planner／维护者 | 调研完 → `ready` |

**新人只要认两个：** `good first issue`（可以领）、`in_progress`（有人了，别抢）。

---

## 二、来源（这条任务是谁提的）

| 标签 | 什么时候用 | 谁贴 | 说明 |
|---|---|---|---|
| `source:human` | 需求来自**真人** | 任务模板／维护者 | 由真人认领、交付、验收 |
| `source:ai` | 是给 **AI 节点**跑的工程任务 | Planner | 由 Agent 认领、交叉审核 |

---

## 三、需要谁来做（权限 / 上报）

| 标签 | 什么时候用 | 谁贴 | 说明 |
|---|---|---|---|
| `human-only` | 整件事必须真人做，机器不能独自完成 | Planner | — |
| `needs-human` | 某一步需**真人决定**（花钱／对外承诺／法律权限／业务方向） | 任何人 | 做到那一步停下来，找人拍板 |
| `needs-lead` | 需**总负责人裁决**（规格／优先级／方案分歧） | 任何人／机器人 | 分歧上升到 lead |
| `help wanted` | 需要额外人手关注 | 维护者 | — |

---

## 四、领域（改的是哪一层）

| 标签 | 什么时候用 | 谁贴 | 对应目录 |
|---|---|---|---|
| `area:data` | 改数据层 | Planner／维护者 | `data/` |
| `area:frontend` | 改前端／演示页 | Planner／维护者 | `docs/` |
| `area:docs` | 改文档 | Planner／维护者 | `README.md`、`CONTRIBUTING.md`、`.github/` |
| `area:pilot` | 试点／实地测试相关 | Planner／维护者 | — |
| `content` | 生产内容资产（如义符卡） | Planner／维护者 | `data/` 的产出物 |

---

## 五、类型

| 标签 | 什么时候用 | 谁贴 | 说明 |
|---|---|---|---|
| `enhancement` | 新功能或改进 | 提出者／Planner | — |
| `bug` | 有东西坏了 | 任何人 | — |
| `documentation` | 文档的改进或补充 | 任何人 | — |
| `accessibility` | 无障碍相关问题 | 任何人 | — |
| `good first issue` | 适合第一次参与 | 维护者 | 通常同时带 `ready` |

---

## 六、GitHub 通用标签（多为自动或维护者手动）

| 标签 | 含义 |
|---|---|
| `duplicate` | 已有相同的 Issue / PR |
| `invalid` | 这个提法不成立 |
| `wontfix` | 不会做 |
| `question` | 需要更多信息 |

---

## 七、特殊：`意见箱`

| 标签 | 什么时候用 | 谁贴 | 说明 |
|---|---|---|---|
| `意见箱` | 从「意见箱」模板开的 Issue | 模板自动 | **不进任务队列**，也不派活；由维护者分流 |

---

## 一句话总结

- **想做活**：认 `good first issue` + `ready`，避开 `in_progress`。
- **看进度**：顺着第一节「流程状态」那一列走。
- **别的标签**：多半是给机器人和维护者用的，看不懂也不影响你干活。
