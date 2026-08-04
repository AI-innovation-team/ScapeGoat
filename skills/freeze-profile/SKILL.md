---
name: freeze-profile
description: Compile a subject's markdown profile assets into a frozen runtime profile. Use when the user wants to check profile completeness or freeze a generator/discriminator profile for scapegoat rollout. Triggers on "freeze profile", "冻结画像", "检查画像", "编译画像".
---

# Freeze a scapegoat profile

Use this skill to turn human-readable markdown profile assets under `profiles/<subject_id>/`
into one compact frozen runtime profile JSON, via the scapegoat MCP tools.

## When to use
- The user wants to verify a subject's profile assets are complete.
- The user wants to freeze a profile for a given role before running a rollout.

## Tools
This skill drives the `scapegoat` MCP server. Prefer these tools over raw shell:
- `inspect_profile(subject_id, base_dir)`
- `freeze_profile(subject_id, role, base_dir, out)`
- `freeze_profile_pair(generator_subject, discriminator_subject, out_dir, base_dir)`

## Procedure
1. Call `inspect_profile` for each subject. If `is_complete` is false, stop and
   report the `missing_files` — do not try to freeze an incomplete profile.
2. Once complete, call `freeze_profile` (single role) or `freeze_profile_pair`
   (both roles at once). Pass `out`/`out_dir` only if the user wants files saved.
3. Report back: `subject_id`, `role`, `version`, `profile_signature`, the
   `summary`, and the save path if any.

## Notes
- `base_dir` defaults to `profiles`. Two other places to look before telling the
  user a subject does not exist: their own assets may sit elsewhere, and the
  plugin ships example profiles at `${CLAUDE_PLUGIN_ROOT}/personas/`
  (`luoyonghao`, `mentor`, `student`) — pass that as `base_dir` to freeze one of
  those. A subject present in both wins from `profiles/`.
- Do not reimplement the markdown→profile compilation in prompt logic; the tool owns it.
