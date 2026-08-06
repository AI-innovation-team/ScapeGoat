# 替罪羊 ｜ ScapeGoat

[中文](README.md) | **English**

[![CI](https://github.com/AI-innovation-team/ScapeGoat/actions/workflows/ci.yml/badge.svg)](https://github.com/AI-innovation-team/ScapeGoat/actions/workflows/ci.yml)
[![CodeQL](https://github.com/AI-innovation-team/ScapeGoat/actions/workflows/codeql.yml/badge.svg)](https://github.com/AI-innovation-team/ScapeGoat/actions/workflows/codeql.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Claude Code plugin](https://img.shields.io/badge/Claude%20Code-plugin-d97757)](#install)

> Train a profile that predicts how one person behaves, from a psychodynamic angle, and let an agent become them.

## Introduction

Agents like Claude Code already turn out decent deliverables; the hard part is matching one particular person's taste.
So how does an agent learn to judge and act the way one specific person does?
We built a toy model from a psychodynamic angle, ScapeGoat: material about someone — a conversation, an interview, a psychometric assessment — goes through the machine-learning loop of training and evaluation, and comes out as a profile that is psychologically coherent and predictive of behavior, for an agent to use.

A profile looks roughly like this (trained from one public figure's online corpus):

> ...
> Under conflict his ordering is: **debt to specific people > integrity of his self-narrative > autonomy > the long-term venture > money > venting**. Money sits far down, backed by large real decisions; venting ranks last but is usually already spent before anyone can stop him.
> ...

Once this profile is loaded, the agent will try to think and act as them:

- **Let them answer** — "reply to this email as my advisor"
- **Let them tear it apart first** — a deliverable goes through their profile before it reaches the real person
- **Predict what they'd choose** — facing a concrete dilemma, what do they sacrifice and what do they protect?

If some piece of your work needs round after round with a particular person — or with yourself — it may be worth training them with ScapeGoat and letting them possess Claude Code to polish that deliverable for you.

## Install

```
/plugin marketplace add AI-innovation-team/ScapeGoat
```

```
/plugin install scapegoat@scapegoat
```

## Usage

Three example profiles ship with it (`luoyonghao`, `mentor`, `student`), ready to try once installed:

> "let luoyonghao possess this session"　　"have mentor critique my proposal"

Everything else is plain language:

| Goal | What to say |
|---|---|
| Train from corpus | "train a profile of Wang from these chat logs" |
| Train by interview | "help me train a profile of my advisor" (11 dimensions, ~10–15 rounds) |
| Train by assessment | "give me an assessment to train my profile" (~25–35 items, answered by the subject) |
| Summon | "summon Wang", "write an email declining this meeting as Wang" |
| Adversarial polish | "have Wang critique my proposal, run a rollout" |
| Continuous learning | "keep training Wang's profile with this new corpus" |

Profiles land in `profiles/<id>/`: `profile.md` as an overview plus 11 dimension files under `analyse/`. Dimensions with thin material carry their confidence rather than invented detail.

<details>
<summary>Local development install</summary>

```bash
git clone https://github.com/AI-innovation-team/ScapeGoat.git && cd ScapeGoat
uv tool install --editable .           # CLI and MCP server
uv tool install --editable ".[audio]"  # optional: speech corpus transcription (pulls PyTorch)
uv tool install --editable ".[claude]" # optional: unattended batch runs

claude --plugin-dir .                  # load the plugin from this directory
```

</details>

## Mechanism

```mermaid
flowchart LR
    SRC[/"corpus · interview · assessment"/] -. extract · keep learning .-> A
    X(["situation X<br/>what he runs into"]) ==> A
    subgraph A[" the profile Claude loads "]
        direction TB
        L1["foundation　formation · worldview · drives_fears"]
        L2["traits　personality · cognition · affect · narratives · defenses"]
        L3["behavior　situational · execution · priorities"]
        L1 --> L2 --> L3
    end
    A ==> Y(["behavior Y<br/>what he does"])
```

Inside the profile, the 11 dimensions are not a flat list of labels but a three-layer causal chain: **lower layers constrain upper ones** — what someone protects under conflict (`priorities`) has to trace back to what they fear (`drives_fears`) and the survival strategy they learned early (`formation`). Predictions come off that chain rather than off a guess about "what sort of person he is". The theory is McAdams' three-level personality model, Mischel's cognitive-affective system (CAPS), and the psychoanalytic view of defenses and life narrative.

The dashed arrow is continuous learning: the same entry point run again, where evidence supporting an existing rule adds no words, evidence that sharpens it rewrites the sentence, and conflicting evidence merges into a conditional rule. **Appending is forbidden** — success means more information at roughly the same byte count.

Five constraints make a profile predictive rather than merely descriptive:

1. **A layered causal model, not a bag of labels.** A label ("he's forceful") predicts nothing; a structure does. The foundation layer explains why this person became who they are, the behavior layer produces the predictions, and the two have to line up.
2. **Every insight must reduce to "situation X → behavior Y".** Sentences that cannot name an X and a Y ("he's complicated") are barred. This is what makes a profile falsifiable rather than decorative.
3. **Reversed readings are mandatory.** Every emotionally loaded event is read twice — once literally, once through a less charitable structural lens. Neutralizing is the model's default bias; uncountered, the profile comes out systematically soft.
4. **Stability analysis.** Prediction rests less on "what he is like now" than on "what he will not turn into". Every dimension says why that layer will not drift on its own.
5. **A minimal-bytes rule.** Not to save tokens — to prevent dilution. Every sentence has to earn its bytes, or the predictive rules drown in observations that are true but useless. Enforced by a hard budget check.

## Benchmark

The repo carries a behavior-prediction benchmark: real behavior from **after a cutoff date** is held out, the profile predicts it, and two baselines run alongside — the model's bare prior (name only) and demographic tags. The headline metric is the **profile's gain over the bare prior**. Four task types: choice prediction, statement generation, style discrimination, critique alignment.

**This benchmark is still under active construction.** With 10–15 cases per task and the variance observed, it can only reliably detect effects above ±0.14, while real profile improvements often land in the ±0.05–0.10 range — most directional differences cannot yet be told from noise, so the current numbers are good for diagnosing what to fix and not for concluding anything about how well the method works.

Beyond scale, the more important next step is **ablating what a profile is made of**: removing one dimension, one constraint at a time and seeing where predictive power drops. That is how to learn the mechanism — whether it is the layering, the reversed readings, or the byte budget doing the work, and how much each contributes — and what the next round of improvements will be based on.

## Privacy and limits

This tool analyses real individuals psychologically, usually without their knowledge.

- **Data stays local.** `profiles/` and `database/` are in `.gitignore`; do not commit profiles or raw corpus to any repository.
- **Never put credentials in a profile** (accounts, passwords, addresses) — the whole thing gets read into a model context.
- **This is a tool for understanding, not for manipulation.** Reasonable uses are self-understanding, preparing for a conversation, rehearsing a deliverable.
- **Profiles are wrong sometimes, and confidently so.** The output is inference from limited evidence, not fact.

## Development

```bash
uv sync --group dev
.venv/bin/python -m pytest -q     # 120 tests
just qa                            # format + lint + typecheck + test
```

MIT © 2026 Guohao Zhang
