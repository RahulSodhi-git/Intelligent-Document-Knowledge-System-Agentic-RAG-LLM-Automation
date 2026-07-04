# The intelligence layer

This makes the documentation automation **adaptive and self-improving** instead of a fixed
script. It runs today on heuristics; add a model key and the vision/planning/memory parts
switch on.

## The loop (now with Reasoning-In-Memory)

```
 SEE ──► PLAN ──► CAPTURE ──► BUILD ──► VERIFY ──► REMEMBER ──► DISTILL ─┐
  ▲                  ▲ (self-heal)                  (diary)   (lessons)  │
  └──────────────────┴───── feedback + drift monitor ◄───────────────────┘
```

| Stage | File | What it does |
|-------|------|--------------|
| SEE | `resolver.py` | Finds elements by *meaning* (`edit_pencil`, `save_button`). Ranks selector strategies by what worked before → self-healing. Learned/healed selectors sit in **quarantine** until they succeed twice. |
| PLAN | `autorecipe.py` | Turns an official PDF/HTML into a step script **and** a capture plan automatically. |
| HEAL | `engine._heal_click` | When every recipe selector fails (UI drift), the model picks the intended control from the page's REAL elements, clicks its true geometry, and quarantines the healed selector (`output/heals.json`). Never heals onto destructive controls. |
| VERIFY | `verify.py` | After each build, self-checks every frame (blank / duplicate / wrong box / caption mismatch), prints a 0–100 score, and marks the report `high_confidence` — only grounded outcomes are allowed to teach. |
| REMEMBER | `memory.py` | **RIM — the experience diary** (`output/experience.json`). Every build attempt (success AND failure) is stored with a reflection grounded in the verify report. Before acting, agents retrieve their most similar past experiences. Also keeps lasting chat facts (`output/chat_memory.json`). |
| DISTILL | `distill.py` | Compresses the diary into `output/lessons.md` (max ~30 rules, consolidation + decay). Every agent prompt reads it — one lesson improves every future run. |
| LEARN | `feedback.py` | Stores 👍/👎, reinforces good selectors, flags weak steps for rebuild. |
| DRIFT | `monitor.py` | Diffs fresh frames vs a baseline; detects when DISH changes a screen. |
| BRAIN | `llm.py` | The one place to add a model key. No key → heuristics. |
| RUN | `orchestrator.py` | `make_from_pdf(qid, pdf)` = plan → capture → build → verify → report. |

## Use it

```
smart_build.bat 11 "C:\path\to\official_Q11.pdf"   # auto plan+capture+build+self-check
verify_all.bat                                     # score every built question
python -m intelligence.orchestrator health         # status (now incl. memory + lessons)
python -m intelligence.monitor                     # drift report
python -m intelligence.memory                      # diary stats
python -m intelligence.distill                     # distill the diary into lessons.md
```

HTTP: `GET /api/memory/status` (diary/lessons/heals at a glance), `POST /api/distill`.

## How the memory stays trustworthy (research-backed design rules)

* **Grounded reflections only** — a diary reflection is written FROM the verify report,
  never free-form "think again" (intrinsic self-correction demonstrably backfires).
* **High-confidence gate** — only `verify.high_confidence` outcomes may teach lessons.
* **Failures are stored too** — failure memories help as much as successes (ReasoningBank).
* **Quarantine** — a healed/learned selector needs 2 verified wins before it outranks the
  hand-written library (stops one lucky hit compounding into every run).
* **Bounded memory** — diary capped at 400 entries, lessons capped at ~30 rules and
  re-consolidated each distill (forgetting is a feature, not a bug).

## Upgrading the "neural network"

1. Put a key in `config/intelligence.json` and set `provider` to `openai` or `anthropic`.
   Vision verification, LLM reflections, chat-fact memory, lesson distillation, live-agent
   memory context, and selector healing all activate automatically.
2. As you collect 👍/👎 and experiences, `output/feedback.json` + `output/resolver_cache.json`
   + `output/experience.json` become a training set: page state → target → what worked →
   rating. Fine-tune a small model on that and point `text_model`/`vision_model` at it.

No "consciousness" required — see → plan → verify → remember → distill → learn, getting
more reliable every run.
