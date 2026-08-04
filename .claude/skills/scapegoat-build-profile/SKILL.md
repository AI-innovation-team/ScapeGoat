---
name: scapegoat-build-profile
description: Build or update a subject profile through interactive Q&A — either an informant interview (user describes a third person, 11-dimension structured probing) or a psychometric-style assessment (the subject answers situational/behavioral items themselves). Triggers on "建画像", "构建画像", "访谈建档", "心理测评", "测评建档", "给我做测评", "build profile", "profile interview".
---

# Build a profile through interactive Q&A

交互问答建档，两种模式。开场先判断（不确定就问一句）：

| 模式 | 画像对象 | 适用 | 协议文件 |
|---|---|---|---|
| **A. 知情人访谈** | 用户描述的**第三者** | "帮我分析某人"、用户提供对他人的观察 | `src/scapegoat/prompts/profile/init.md` |
| **B. 心理测评** | **作答者本人** | "给我做个测评"、画像对象自己在场作答 | `src/scapegoat/prompts/profile/assessment.md` |

## Required reading

1. `src/scapegoat/prompts/profile/merge_rules.md` — 写入契约，两种模式共用。
2. 所选模式的协议文件（上表）。**严格按协议执行**：模式 A 的反转解读、逐维度追问；模式 B 的行为采样、间接测防御、一次一题。
3. 若画像已存在：先读 `profiles/<subject_id>/profile.md`，问答会转为**补充/更新**模式——优先追问已有画像中证据薄弱和标注低置信度的维度。

## Procedure

1. 目标对齐：确认 subject_id、画像用途、模式 A/B。
2. 按协议执行问答（A 约 10–15 轮；B 约 25–35 题，自适应跳题）。
3. 写入：新画像生成 12 个文件；已有画像按 merge_rules 逐维合并（整合改写，禁纯追加）。
4. 校验：`scapegoat profile budget <subject_id> --base-dir <base_dir> --strict`（或 MCP `profile_budget`），超预算压缩至通过。
5. 汇报更新内容与预算结果；提示需要时重新 freeze。

## Notes

- 模式 B 的自陈证据置信度默认低于行为语料，写入时标注 `来源: 测评自陈`；与语料证据冲突时，冲突本身按 narratives/defenses 证据处理。
- 两种模式可与 scapegoat-ingest-corpus 混用：同一画像可以先语料后测评，持续累积，合并契约保证不膨胀。
