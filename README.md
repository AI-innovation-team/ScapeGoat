# scapegoat

用心理动力学框架给一个人建立可预测其行为的 profile，然后让 Claude 以这个 profile 的身份思考和行动。

画像不是标签堆砌，而是一套分层模型：**根源层**（早年经历如何凝固成生存策略）→ **特质层**（认知与情感的质地）→ **行为层**（情境规则、执行方式、冲突时的优先级）。理论底子是 McAdams 三层人格、Mischel CAPS 与精神分析的防御/叙事视角。

核心约束有三条：每个洞见必须能转成「情境 X → 行为 Y」的预测；每个事件都要走一遍反转解读以对抗中性化偏见；每一层都要回答「这层为什么不会自然改变」。

## 安装

在 Claude Code 里两条命令：

```
/plugin marketplace add colehank/scapegoat
/plugin install scapegoat@scapegoat
```

装完即可用，**不需要预先安装 Python 或任何依赖**。建画像、附身、持续学习这些主线功能是纯 markdown，零依赖运行；需要 CLI 的部分（freeze、rollout、benchmark、字节预算校验）由 [uv](https://docs.astral.sh/uv/) 的 `uvx` 按需拉起，首次调用自动建环境，之后走缓存。

装在哪由你决定：`/plugin install` 默认写入 `~/.claude/settings.json`（所有项目可用）；想只在当前项目启用就写进项目的 `.claude/settings.json`。

**唯一前提**：机器上有 `uv`（`curl -LsSf https://astral.sh/uv/install.sh | sh`）。没有也不影响建画像和附身，只是 CLI 相关步骤会跳过并给出提示。

**日常使用不需要 API key。** 对抗迭代默认由 Claude Code 自己扮演双方角色。只有想脱离会话批量自动跑时才需要 `ANTHROPIC_API_KEY`。

<details>
<summary>本地开发安装</summary>

```bash
git clone git@github.com:colehank/scapegoat.git && cd scapegoat
uv tool install --editable .          # 装 CLI 与 MCP server
uv tool install --editable ".[audio]" # 额外：语音语料转写（会拉 PyTorch，数 GB）
uv tool install --editable ".[claude]" # 额外：脱离会话的自动化跑批

claude --plugin-dir .                  # 以本地目录加载 plugin 调试
```

</details>

## 怎么用

全部通过在 Claude Code 里说话触发，不用记命令。

### 1. 建画像

三种方式，产出格式相同，可以叠加使用。

**从语料建** —— 有聊天记录、访谈稿、文档时：

> 「用这些文件给老王建画像」（附上文件）

支持任意文档和 JSON 对话（兼容常见导出格式）。对话语料会先确认哪个说话人是画像对象，再走三遍抽取：证据扫描 → 反转校验 → 生成预测规则。

**访谈建** —— 你了解某人，但没有现成材料：

> 「帮我给我导师建画像」

按 11 个维度逐维追问约 10–15 轮，每个关键事件给出字面解读和反转解读让你表态。

**测评建** —— 画像对象本人在场作答：

> 「给我做个测评建画像」

约 25–35 道题，行为采样 + 情境判断 + 强制二选一，防御机制走间接投射题。

产出在 `profiles/<id>/`：`profile.md`（索引式总览）+ `analyse/` 下 11 个维度文件。素材不足的维度会如实标注置信度，不编造。

### 2. 用画像

**附身** —— 让画像本人回答：

> 「召唤老王」
> 「以老王的身份写封邮件推掉这个会」
> 「老王看到这个方案会怎么想」

支持两种交互：离散问答，或整个会话像在直接跟他对话。

**对抗打磨** —— 让画像当批评者反复挑刺你的交付物：

> 「让老王挑刺我的开题报告，跑个 rollout」

生成器出稿、判别器批评、循环迭代，直到判别器认为达标或到步数上限。全过程可导出 markdown。

### 3. 持续学习

来了新数据，**同样的话再说一遍**即可：

> 「用这批新的聊天记录继续训练老王的画像」

已有画像时自动转为合并模式：新证据支持旧规则就不加字，更精确就改写原句，冲突就并成带条件的规则。**禁止纯追加**——信息增加、字节持平才算成功。合并后如需用于 rollout，重新 freeze 一次。

## 最小字节原则

画像要「用准确不冗余的语言表达清楚」，这条是硬约束不是口号：

- 句子准入三标准：可预测、有证据、不重复
- 合并四规则：重合不加字 / 细化改写原句 / 冲突并成条件规则 / 全新才新增
- 字节预算硬校验：`scapegoat profile budget <id> --strict`，超了不通过

默认 `profile.md` ≤ 6KB、每个维度文件 ≤ 10KB。已有画像可在其目录放 `budget.json` 认定当前尺寸为上限（语义是「禁止膨胀」）。

## 命令行（可选）

skill 会自动调用，一般不用手敲。没装包时可用 `uvx --from git+https://github.com/colehank/scapegoat scapegoat ...` 代替 `scapegoat ...`：

```bash
scapegoat profile inspect <id>          # 检查画像完整性
scapegoat profile budget <id> --strict  # 字节预算校验
scapegoat profile corpus <files...>     # 语料归一化
scapegoat profile freeze <id> --role discriminator --out d.json
scapegoat rollout run --generator-profile g.json --discriminator-profile d.json --task-file t.json
scapegoat benchmark validate <cases.json>
```

## 评测（可选）

`benchmark/` 下有一套行为预测评测，用真实事件检验画像准不准：选择预测、言论生成、风格判别、批评对齐四类任务，每条 case 都对照 bare（模型裸先验）/ tags（人口学标签）/ profile 三个条件作答，核心指标是 **profile 相对裸先验的增量**——只有这个增量才是画像本身的贡献。

> 「跑 benchmark」

注意样本量：每任务 10–15 条 case、评分方差较大时，只能可靠检出 ±0.14 以上的效应。用于诊断改进方向足够，用于精细比较需要先把 case 扩到每任务 30 条左右——否则容易把噪声当成信号。

## 开发

```bash
uv sync --group dev
.venv/bin/python -m pytest -q     # 108 tests
just qa                            # format + lint + typecheck + test
```

## License

MIT © 2026 Guohao Zhang
