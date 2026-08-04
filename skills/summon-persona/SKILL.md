---
name: summon-persona
description: Summon a scapegoat profile to "possess" (夺舍) and answer/act in first person as that person. Asks who to summon (auto-scans for profile dirs if not given), checks the profile dir is complete (partial possession if not), narrates the summon, then runs one of two interaction styles over a single persona subagent — discrete Q&A (子智能体) or a transparent forwarding session where the main chat feels like talking directly to the person (主智能体附身/转发). Use when the user wants to roleplay/embody a profile, "let <profile> answer", become a profile, or talk as/with a profiled person. Triggers on "上身", "附身", "夺舍", "召唤画像", "请谁上身", "扮演这套画像", "以画像身份", "我要和 <某人> 聊", "summon persona", "let this profile answer".
---

# 召唤画像「夺舍」上身

把一套 scapegoat 画像请上身，让它以**第一人称**回应/产出。本 skill 负责编排：**确定请谁附体 → 识别画像是否完整 → 选夺舍对象 → 播报召唤 → 执行**。

只用内置工具（Glob / Read / Agent / SendMessage），**不依赖任何 MCP**。

**统一后端**：两种模式都只是 spawn **一个** `scapegoat:persona` 子智能体当"神"，区别只在交互方式——离散一问一答，还是主会话每轮自动转发、透明呈现。

## 两要素

开场凑齐两样，缺哪样补哪样：

1. **画像（请谁附体）** —— `profile_dir`（目录路径，可在 `profiles/` 内或外）或 `subject_id`（简写 = `profiles/<subject_id>/`）。
2. **夺舍对象（附体谁）**：
   - **子智能体**（默认）—— 离散一问一答；本会话保持中立；可并行召唤多个画像对比。
   - **主智能体附身（转发）** —— 本会话变成透明路由器，之后每轮自动转给同一个神，像直接在跟 TA 多轮对话。

## 第一步：确定请谁附体

- 给了 `profile_dir`/`subject_id` → 直接用；下文以 `<subject_id>`（目录名）称呼。
- **没给 → 自动扫描候选**：用 Glob 找 `profiles/*/profile.md`（若空，再扫当前目录 `*/profile.md`），列出目录名让用户选：

  > 没说请谁上身。当前可召唤：`zzl`、`zgh`、…… 选哪个？（或直接给我一个 `profile_dir`）

- 一个都没扫到 → 告知此处没有画像目录，请用户提供 `profile_dir`。

## 第二步：识别画像是否完整（不用 MCP）

用 Glob 列 `<profile_dir>/analyse/*.md`，并探 `<profile_dir>/profile.md` 是否在，与下面 **11 个标准维度**比对：

```
formation  worldview  personality  cognition  affect  drives_fears
defenses   narratives situational  execution  priorities
```

三种走向：

- **完整**（profile.md + 11 维度齐）→ 正常上身。
- **部分**（profile.md 在，缺若干维度）→ **部分上身**：可召唤，但**当场声明**缺了哪些、哪类判断会虚（缺 `priorities` → 冲突取舍把握低；缺 `situational` → 特定情境姿态把握低；缺 `formation`/`worldview` → 地基松、易出戏成泛泛的人）。
- **几乎为空**（连 profile.md 都没有）→ **无法召唤**：如实说该目录没有可用画像，请用户确认路径。不要硬编。

## 第三步：播报召唤（趣味、克制，2–3 行）

```
🔮 夺舍仪式启动 · 目标：<subject_id>
   装载维度 9/11（缺 narratives、execution）→ 部分上身
   夺舍对象：主智能体附身（转发）
   <subject_id> 上身中……
```

完整时显示 `装载维度 11/11`。

## 第四步：召唤神（两种模式公用）

用 Agent 工具 spawn **一个** `scapegoat:persona` 子智能体，画像位置与首个指令拼进 prompt（subagent 唯一输入通道），并**记住它返回的 `agentId`**：

```
Agent(subagent_type="scapegoat:persona",
      prompt="profile_dir: <目录>\n\n情境: <若有>\n指令: <要 TA 做的事>")
```

> 子智能体只响应**一次**就 idle；要继续同一个神，靠 `SendMessage(to=<agentId>, …)` 带上下文唤醒它。两种模式都建立在这条机制上。

## 第五步：按夺舍对象执行

### 子智能体模式（默认，离散一问一答）

- 把神返回的戏内交付物**原样转达**给用户。
- 用户接着追问同一角色 → `SendMessage(to=<agentId>, "<新指令>")`，转达回复。
- 换任务/换人 → 重新 spawn。一次性需求转达完即止，神退场。

### 主智能体附身（转发）

主会话从此当**透明路由器**，自己**不入戏、不读 profile**（神在子智能体里），逻辑：

1. 记住一条持久事实：「**当前 = `<subject_id>` 转发态，agentId = `<agentId>`**」，使其扛过上下文压缩。
2. 之后**每一轮**先看用户消息是不是**退场意图**（如"退下/不演了/退驾/变回 Claude/结束附身"）：
   - 是 → 停止转发，恢复 Claude 身份，报一句「（`<subject_id>` 已退场，我又是 Claude 了。）」+ 可选简短复盘。
   - 否 → `SendMessage(to=<agentId>, "<用户这一轮原话 + 必要情境>")`，把神的回复**原样呈现**给用户，不加 Claude 的旁白或元说明。
3. 一直维持到用户退场。用户之后可再召唤（同一或不同画像）。

> 转发态下保持透明：你只是把话传进传出，让用户感觉在直接跟 `<subject_id>` 对话。

## 备注

- 这是 scapegoat 研究项目的人设模拟，忠于画像证据；缺失处只做保守外推并标注，不凭空编造。
- 不要把此能力用于现实中冒充、欺骗或骚扰具体个人。
