# 替罪羊 ｜ ScapeGoat

**中文** | [English](README.en.md)

[![CI](https://github.com/AI-innovation-team/ScapeGoat/actions/workflows/ci.yml/badge.svg)](https://github.com/AI-innovation-team/ScapeGoat/actions/workflows/ci.yml)
[![CodeQL](https://github.com/AI-innovation-team/ScapeGoat/actions/workflows/codeql.yml/badge.svg)](https://github.com/AI-innovation-team/ScapeGoat/actions/workflows/codeql.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Claude Code plugin](https://img.shields.io/badge/Claude%20Code-plugin-d97757)](#安装)

> 以心理动力学视角，训练一份能预测某人行为的 Profile，并让智能体成为他。

## 简介

时下的智能体，如 Claude Code，已经可以给出不错的交付物，难的是对上某个具体的人的品味。
那么，智能体要怎么学会像一个具体的人那样判断与行动？
我们从心理动力学的视角搭了一个 toy model，ScapeGoat：把关于某人的材料—— 一段对话、一份访谈、一次心理测评 ——像机器学习那样，训练并评估出一份心理学合理、有行为预测效力的 Profile，供智能体使用。

Profile 大概长这样（由某位公共人物的网络语料训练得到）：

> ...
> 冲突时他的排序是：**对具体的人的亏欠 > 自我叙事的完整性 > 自主权 > 长期事业 > 金钱 > 一时之气**。金钱排在很后面，有大额真实决策支撑；"一时之气"排最后，但常常在别人拦住之前就已经支出了。
> ...

装载此 Profile 之后，智能体就会尝试以他的身份思考和行动：

- **让他本人回答** —— 「以我导师的身份回复这封邮件」
- **让他先挑一遍刺** —— 交付物送到真人面前之前，先过一遍他的 Profile
- **预测他会怎么选** —— 面对具体两难，他会牺牲什么保什么

如果你的某份工作需要与某人（甚至你自己）持续迭代，不妨用 ScapeGoat 把他训练出来，附体在 Claude Code 身上自动打磨这份交付物。

## 安装

```
/plugin marketplace add AI-innovation-team/ScapeGoat
```

```
/plugin install scapegoat@scapegoat
```

## 用法

自带三份示例 Profile（`luoyonghao`、`mentor`、`student`），装完即可试：

> 「请luoyonghao上身」　　「让 mentor 挑刺我的开题报告」

其余自然语言触发：

| 想做什么 | 说什么 |
|---|---|
| 从语料训练 | 「用这些聊天记录训练老王的 Profile」 |
| 访谈训练 | 「帮我给我导师训练一份 Profile」（11 维逐维追问，约 10–15 轮） |
| 测评训练 | 「给我做个测评，训练我的 Profile」（本人作答，约 25–35 题） |
| 召唤 | 「召唤老王」「以老王的身份写封邮件推掉这个会」 |
| 对抗打磨 | 「让老王挑刺我的开题报告，跑个 rollout」 |
| 持续学习 | 「用这批新语料继续训练老王的 Profile」 |

Profile 落在 `profiles/<id>/`：`profile.md` 总览 + `analyse/` 下 11 个维度文件。材料不足的维度标注置信度，不编造。

<details>
<summary>本地开发安装</summary>

```bash
git clone https://github.com/AI-innovation-team/ScapeGoat.git && cd ScapeGoat
uv tool install --editable .           # CLI 与 MCP server
uv tool install --editable ".[audio]"  # 可选：语音语料转写（会拉 PyTorch）
uv tool install --editable ".[claude]" # 可选：脱离会话的自动化跑批

claude --plugin-dir .                  # 以本地目录加载 plugin 调试
```

</details>

## 机制

```mermaid
flowchart LR
    SRC[/"语料 · 访谈 · 测评"/] -. 抽取 · 持续学习 .-> A
    X(["情境 X<br/>他遇到了什么"]) ==> A
    subgraph A[" Claude 装载的 Profile "]
        direction TB
        L1["根源层　formation · worldview · drives_fears"]
        L2["特质层　personality · cognition · affect · narratives · defenses"]
        L3["行为层　situational · execution · priorities"]
        L1 --> L2 --> L3
    end
    A ==> Y(["行为 Y<br/>他会怎么做"])
```

Profile 内部的 11 个维度不是平列的标签，而是三层因果链：**底层约束上层**——一个人在冲突时保什么（priorities），要能追溯到他怕什么（drives_fears）和他早年学到的生存策略（formation）。预测从这条链上推出来，而不是从"他是个什么样的人"直接猜。理论底子是 McAdams 三层人格模型、Mischel 的认知-情感系统（CAPS）与精神分析的防御/叙事视角。

虚线是持续学习：同一个入口再跑一次，新证据支持旧规则就不加字，更精确就改写原句，冲突就并成带条件的规则。**禁止纯追加**——信息增加、字节持平才算成功。

五条约束让 Profile 可预测，而不只是可描述：

1. **分层因果模型，不是标签集合。** 标签（"他很强势"）不能预测，结构能。根源层解释他为什么变成这样，行为层给出预测，两者必须对得上。
2. **每条洞见必须能转成「情境 X → 行为 Y」。** 写不出 X 和 Y 的句子（"他比较复杂"）一律不许进 Profile。这条决定了 Profile 可证伪还是废话。
3. **强制反转解读。** 每个有情感色彩的事件都走两遍——字面一遍，更不温和的结构性解释再一遍。中性化是模型的默认偏见，不主动对抗，Profile 就会系统性偏软。
4. **稳定性分析。** 预测的基础不是"他现在什么样"，而是"他不会变成什么样"。每个维度都要回答这一层为何不会自然改变。
5. **最小字节原则。** 不为省 token，是防稀释：每句都要挣回自己的字节，否则有预测力的规则会被淹没在正确但无用的描述里。有硬校验，超预算不通过。

## 评测

仓库里有一套行为预测 benchmark：用真人在**特定日期之后**的真实言行做留出集，让 Profile 去预测，对照模型裸先验（只给名字）和人口学标签两个基线；核心指标是 **Profile 相对裸先验的增量**。四类任务：选择预测、言论生成、风格判别、批评对齐。

**这套 benchmark 仍在积极构建中。** 当前每任务 10–15 条 case，在观察到的方差下只能可靠检出 ±0.14 以上的效应，而 Profile 迭代的真实增益常在 ±0.05–0.10 量级——大部分方向性差异还无法与噪声区分，现有数字只够诊断改进方向，不足以支撑对方法效果的结论。

接下来除了扩大规模，更关键的一步是**对 Profile 的构成做消融**：逐个维度、逐条约束地拿掉，看预测力掉在哪里。这既是为了搞清楚机制——究竟是分层结构、反转解读还是最小字节在起作用、各自贡献多少——也是继续优化方法的依据。

## 隐私与边界

这个工具会对真实的人做心理分析，多数情况下对方并不知情。

- **数据留在本地。** `profiles/`、`database/` 已在 `.gitignore` 中；不要把 Profile 或原始语料提交到任何仓库。
- **Profile 里不要写凭证类信息**（账号、密码、住址），它会被完整读进模型上下文。
- **这是理解工具，不是操控工具。** 合理用途是自我认知、沟通准备、交付物预演。
- **Profile 会犯错，而且错得很自信。** 输出是基于有限证据的推断，不是事实。

## 开发

```bash
uv sync --group dev
.venv/bin/python -m pytest -q     # 120 tests
just qa                            # format + lint + typecheck + test
```

MIT © 2026 Guohao Zhang
