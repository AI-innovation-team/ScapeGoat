---
name: train-profile
description: Update frozen scapegoat profiles from an offline training record that compares real vs simulated critic feedback. Use when the user wants to align the discriminator/generator to real feedback. Triggers on "train profile", "训练画像", "对齐反馈", "更新画像".
---

# Train (update) scapegoat profiles

Use this skill to evolve frozen profiles using one offline training record. The
record captures a real critic's feedback (and optionally a simulated one); the
update nudges the discriminator toward the real feedback's focus and adjusts the
generator's revision strategy.

## When to use
- The user has real discriminator feedback they want the profiles to learn from.
- The user wants a new profile version reflecting that alignment signal.

## Tools
Drive the `scapegoat` MCP server:
- `create_training_record(task_file, deliverable_file, real_feedback_file, out, simulated_feedback_file)`
- `render_training_loss_prompt(record_file)`
- `train_profiles(generator_profile_path, discriminator_profile_path, record_file, generator_out, discriminator_out, report_out, loss_response, history_file)`

## Procedure
1. If no training record exists yet, call `create_training_record` from the task,
   the deliverable text, and the real feedback text. Save it to a JSON path.
2. Call `render_training_loss_prompt` on that record, **answer the returned prompt
   yourself** (it asks for transferable discrimination dimensions as JSON), and keep
   the raw JSON reply.
3. Call `train_profiles` with the current frozen profiles, that record, the reply as
   `loss_response`, and a stable `history_file` path per subject pair.
4. Report: `new_generator_version`, `new_discriminator_version`, `loss_magnitude`,
   `rolled_back`, and the `loss` summary. Note the saved paths.

## Notes
- Step 2 is not optional. Skipping `loss_response` falls back to a sentence-level
  text diff, which on two pieces of free-form prose copies the real feedback into
  the profile verbatim — that measurably *degraded* discriminator profiles.
- The induced dimensions must survive being applied to a different deliverable.
  If a dimension only makes sense for this case (contains a name, a project, a
  number), rewrite it before passing it on.
- `history_file` enables delayed verification: a loss larger than last round's
  means the previous update was harmful, so it is rolled back before this round's
  patches land. Reuse the same path across sessions or the check never fires.
- Each call bumps the profile `version`; keep old versions if the user wants to compare.
- `behavior_rules` are capped (24) with training-added rules evicted oldest-first,
  so a long training history cannot inflate the frozen profile.
