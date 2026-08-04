---
name: run-rollout
description: Run an adversarial generator/discriminator rollout between two frozen scapegoat profiles. Use when the user wants to iterate a deliverable against a critic until convergence or max steps. Supports an in-session mode where Claude Code itself plays the roles (no API key needed). Triggers on "run rollout", "跑 rollout", "对抗迭代", "生成-判别", "模拟 zzl".
---

# Run a scapegoat rollout

A rollout is the adversarial loop: a generator profile produces a deliverable, a
discriminator profile critiques it with a 1–10 dissatisfaction score, and the
loop repeats until convergence or `max_steps`.

There are two ways to run it. Pick based on what the user asked for.

## Mode A — in-session (default; no API key)

Claude Code runs the loop itself: the **main conversation plays the generator**
(e.g. zgh) and a **spawned subagent plays the discriminator** (e.g. zzl). Python
only renders prompts and persists state — it never calls an LLM. Use this when
the user wants Claude Code to "simulate zzl" / "展开一个智能体模拟 zzl", or when
there is no Anthropic API key available.

### Procedure
1. Ensure both profiles are frozen (use **scapegoat:freeze-profile** if not).
   Load them and the TaskSpec. A small driver in Python manages state:
   - `from scapegoat.runtime import in_session`
   - `from scapegoat.runtime.persistence import load_model`
   - `from scapegoat.profile.schema import FrozenProfile`
   - `from scapegoat.runtime.schema import TaskSpec`
2. `state = in_session.start_state(generator, discriminator, task)`
3. Loop while `not in_session.is_finished(state)`:
   a. **Play the generator yourself**: read the task, the last critique
      (`in_session.latest_feedback(state)`), and the current best deliverable,
      then write the next deliverable *in zgh's voice*. Record it:
      `deliverable = in_session.record_generator_step(state, content)`.
   b. **Render the critic prompt**:
      `prompt = in_session.build_discriminator_prompt(discriminator, state)`.
   c. **Spawn the discriminator subagent** with the `scapegoat:discriminator`
      agent type, passing `prompt` verbatim as the task. It returns one JSON object.
   d. **Record the critique**: `in_session.record_discriminator_step(state, response)`.
   e. Decide whether to stop early: if the critic's `dissatisfaction_score` is low
      AND it raises no new core objection, you may stop before `max_steps`.
4. Persist: `in_session.save_session(state, gen_path, disc_path, session_out, result_out)`.
5. Optionally export a step-by-step doc (see **scapegoat-export-doc** flow /
   `rollout export-doc`). Report `final_dissatisfaction_score`, `total_rounds`,
   and a short summary.

### Notes for Mode A
- The subagent must return ONLY the JSON object; `record_discriminator_step`
  tolerates fenced/wrapped JSON but the cleaner the better.
- Keep the generator genuinely in zgh's voice — the point is a realistic loop,
  not a generic draft reviewed by zzl.
- One subagent per round keeps token use bounded; don't batch rounds.

## Mode B — Claude SDK backend (needs credentials)

Use the MCP tool `run_rollout(..., backend="claude", ...)` when the user has
Anthropic credentials and wants a fully automated, non-interactive run. The
deterministic `local` backend (`backend="local"`) is only an MVP placeholder and
will NOT sound like the real persona — never present it as a faithful simulation.

## When to use which
- "let Claude Code simulate zzl" / no API key  → **Mode A**.
- "run it headless with the API" / batch automation → **Mode B** (`claude`).
- quick smoke test of the plumbing only → `local`, and say so explicitly.
