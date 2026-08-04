---
name: ingest-corpus
description: Build or incrementally update a subject profile from corpus material — arbitrary documents or JSON conversations. This is the continuous-learning entry point; each new batch of data merges into the markdown profile under the minimal-bytes contract. Triggers on "ingest corpus", "导入语料", "从文档建画像", "从聊天记录更新画像", "语料训练画像", "继续训练画像".
---

# Ingest corpus into a profile

从语料（任意文档 / JSON 对话）抽取证据，生成或**增量更新**画像目录。可重复执行：新数据到达就再跑一遍，这就是画像的持续学习。

## Required reading (in order, before anything else)

1. `${CLAUDE_PLUGIN_ROOT}/src/scapegoat/prompts/profile/merge_rules.md` — 写入契约（最小字节原则）。
2. `${CLAUDE_PLUGIN_ROOT}/src/scapegoat/prompts/profile/ingest.md` — 抽取流程。
3. 若画像已存在：`profiles/<subject_id>/profile.md`（了解现状后再合并）。

## Procedure

1. **确认输入**：subject_id（或画像目录）、语料文件列表。缺哪个问哪个。
2. **归一化语料**：
   - JSON 对话 → `scapegoat profile corpus <files...> --out <staging.md>`（或 MCP 工具 `normalize_corpus`）。产出 `speaker: text` 转写。
   - 纯文本/markdown 文档 → 直接 Read。
   - 其他格式（pdf/docx）→ 先用可用工具转成文本再继续。
3. **确认说话人映射**：对话语料必须先向用户确认哪个 speaker 是画像对象。不确认不抽取。
4. **执行 ingest.md 的三遍流程**：证据扫描 → 反转校验（单证据取字面、重复模式才上升为结构断言）→ 生成 `情境 → 行为` 预测规则。
5. **写入**：
   - 新画像 → 按 `init.md` 结构生成 12 个文件（无证据的维度如实标注，不编造）。
   - 已有画像 → 逐维度按 merge_rules 合并：整合改写，**禁止纯追加**。
6. **校验**：`scapegoat profile budget <subject_id> --base-dir <base_dir> --strict`（或 MCP `profile_budget`）。超预算按契约压缩后重跑，直到通过。命令不可用时见 [cli-invocation.md](../cli-invocation.md)。
7. **汇报**：更新了哪些维度的哪些规则、冲突及处理、预算结果；提示"如需用于 rollout/persona，请重新 freeze（scapegoat:freeze-profile）"。

## Notes

- 语料只提供"此人说的话/做的事"；他人转述仅作待验证线索。
- 合并后信息增加、字节持平是成功标准；字节显著增长说明在追加而不是整合。
- 本 skill 更新的是 **markdown 源画像**（知识库本体）；冻结 JSON 是它的编译产物，更新源后需重新 freeze 才会生效于 rollout。
