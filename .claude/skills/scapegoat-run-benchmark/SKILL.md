---
name: scapegoat-run-benchmark
description: Run the behavior-prediction benchmark for a subject profile — answer sourced real-behavior cases under bare/tags/profile conditions, judge with independent subagents, and report per-task scores plus the profile-vs-prior delta. Triggers on "run benchmark", "跑 benchmark", "评测画像", "测画像效果", "benchmark 罗永浩".
---

# Run the behavior-prediction benchmark

评测"画像能否预测真人行为"。核心指标不是绝对分，而是 **profile_delta = profile 条件 − bare 条件**：画像相对模型裸先验的增量。

## Inputs

- `cases.json`：`benchmark/<subject_id>/cases.json`（BenchmarkSet schema）。先跑 `scapegoat benchmark validate <file>` 确认合法并看任务构成。
- 画像目录：`profiles/<subject_id>/` 或用户指定。
- 条件集合：默认三条件 `bare / tags / profile`；用户可指定只跑部分（快速迭代时常只跑 bare+profile）。

## Per-case procedure

对每个 (condition × case)：

1. **构造作答 prompt**：用 `scapegoat.benchmark.prompts` 的 `render_condition_context(bench, condition, profile_prompt)` + `render_case_prompt(case)` 拼接。
   - `bare` / `tags` 条件：起一个普通子智能体（Agent tool, general-purpose），prompt = 条件上下文 + 题目。子智能体**只拿到名字/标签**，禁止在 prompt 里夹带任何画像信息。
   - `profile` 条件：起 `scapegoat-persona` 子智能体，传 `profile_dir` + 题目（这是画像的真实使用方式）。若要做压缩消融，可另跑一轮"嵌入冻结画像渲染文本的普通子智能体"作对照。
2. **收集回答**（style 任务收正文，其余收 JSON 字符串）。
3. **评分**：
   - `choice`：直接 `score_choice(case, response)`，无需 judge。
   - `statement` / `critique`：起**独立 judge 子智能体**（不得复用作答智能体），prompt 用 `render_statement_judge_prompt` / `render_critique_judge_prompt`，回来后 `score_statement` / `score_critique`。
   - `style`：`render_style_judge_prompt(case, generated)` 返回 (prompt, real_label)——A/B 已按 case_id 确定性乱序；judge 盲选哪段是真文，`score_style` 判 judge 是否被骗过。
4. 把每条 `CaseRun` 的 `condition` 字段改成实际条件后收集起来。

**并行**：同一条件下各 case 相互独立，作答子智能体可批量并行（一条消息发多个 Agent 调用）；judge 也可并行。但同一 case 的"作答→评分"有先后依赖。

## Finish

1. 汇总为 `BenchmarkRun`（subject_id, profile_dir, runs），用 python 保存到 `benchmark/<subject_id>/runs/<日期>-<条件>.json`（`scapegoat.runtime.persistence.save_model`）。
2. `scapegoat benchmark report <run_file>` 输出每 (task × condition) 均分和 profile_delta。
3. 汇报要点：各任务 delta、post_cutoff 子集单独看一眼（那部分最不受模型先验污染）、judge 给出的典型误判线索（style 任务的 `cue` 字段能直接指导画像改进哪个维度）。

## Ablations（优化循环用）

- **语料量消融**：用 25%/50%/100% 语料各建一版画像，各跑一遍 → 持续学习曲线。
- **压缩消融**：同一画像压到不同字节数各跑一遍 → 找预算拐点。
- 消融轮次多时只跑 `profile` 条件 + 复用一次 `bare` 基线即可。

## Honesty rules

- 作答子智能体的 prompt 里绝不能出现 case 的 `answer` / `answer_source`。
- judge 绝不能知道哪个条件生成了被评文本。
- 分数低不修 case 不改 judge 标准来"提分"；修的是画像和管线。
