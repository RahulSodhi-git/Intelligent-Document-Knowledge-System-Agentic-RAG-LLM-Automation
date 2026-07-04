# Making LLM Agents Smarter with Memory: A Research Summary

*Deep-research report, July 2026. All benchmark numbers below were verified against the primary arXiv sources.*

## The big picture

There is no paper literally called "RIM / Reasoning in Memory," but the idea behind it — **an agent that stores its reasoning and experiences, then retrieves and reuses them instead of thinking from scratch every time** — is one of the most active and best-evidenced research threads of 2023–2026. The field converges on a clear conclusion: agents improve dramatically when they (1) keep memories of what worked and why, (2) distill those memories into reusable lessons or workflows, and (3) verify their own work using an **external** signal rather than pure self-reflection.

The research splits into five families, summarized below.

## 1. Reasoning-in-memory: storing and reusing thinking

This family is the closest match to "RIM."

**ReasoningBank** (Google, 2025) is the state of the art. The agent distills *reasoning strategies* — from both its self-judged successes **and failures** — into structured memory items. Before each new task it retrieves relevant strategies, acts, then writes new learnings back, forming a closed loop. Results: up to **34.2% relative improvement and 16% fewer steps** on web-agent benchmarks, and it explicitly beats workflow-only memory. Key insight: *failures are as valuable as successes* for memory. Limitation: it depends on the agent judging its own success, so judge errors can pollute memory. ([arXiv:2509.25140](https://arxiv.org/abs/2509.25140))

**ExpeL** (AAAI 2024) gathers experiences on practice tasks, then extracts two kinds of memory: natural-language *insights* (rules distilled from comparing successful vs. failed attempts) and *successful trajectories* retrieved as examples at inference time. Performance rises steadily as experience accumulates — with **no model training at all**. Insights even transfer across task types. ([arXiv:2308.10144](https://arxiv.org/abs/2308.10144))

**Buffer of Thoughts** (NeurIPS 2024 Spotlight) keeps a buffer of high-level "thought templates" distilled from past problem-solving and instantiates the best-matching template for each new problem: **+11% to +51%** on reasoning benchmarks at ~12% of the cost of tree-of-thought-style methods. ([arXiv:2406.04271](https://arxiv.org/abs/2406.04271))

**Memory-of-Thought** (EMNLP 2023) has the model "pre-think" over unlabeled data, keep its high-confidence reasoning paths, and recall them as demonstrations at answer time. ([arXiv:2305.05181](https://arxiv.org/abs/2305.05181))

## 2. Workflow and skill libraries: storing reusable procedures

Where family 1 stores *thinking*, this family stores *procedures* — directly relevant to UI automation.

**Agent Workflow Memory (AWM)** (CMU/MIT, 2024) induces reusable sub-routines ("workflows") from past agent trajectories and injects the relevant ones into the prompt for new tasks. Verified results: **+24.6% relative success on Mind2Web, +51.1% on WebArena**, while *reducing* steps per task. Its online mode learns from the agent's own test-time experience and beats baselines by **8.9–14.0 absolute points** when new tasks differ from training ones. ([arXiv:2409.07429](https://arxiv.org/abs/2409.07429))

**Voyager** (2023) pioneered the *skill library*: every verified success is stored as executable code, indexed by an embedding of its description, and retrieved by similarity for new tasks. Skills compose into bigger skills. Results in Minecraft: **3.3× more items discovered, milestones up to 15.3× faster** than prior methods. ([arXiv:2305.16291](https://arxiv.org/abs/2305.16291))

**Synapse** (ICLR 2024) stores complete successful trajectories as retrievable few-shot examples (with page-content filtering to fit context): **99.2% success on MiniWoB++**. ([arXiv:2306.07863](https://arxiv.org/abs/2306.07863))

**AutoManual** (NeurIPS 2024) has one agent act while another maintains a structured *rule book* updated from outcomes, compiled into a readable manual: **97.4% on ALFWorld** from a single demonstration. ([arXiv:2405.16247](https://arxiv.org/abs/2405.16247))

## 3. Memory architectures: how to store, score, and forget

**Generative Agents** (Stanford, 2023) introduced the memory stream: every event is a record, retrieved by a weighted mix of **recency + importance + relevance**, and periodically *reflected* into higher-level abstract memories. Ablations show removing reflection degrades behavior. ([arXiv:2304.03442](https://arxiv.org/abs/2304.03442))

**MemGPT/Letta** (2023) treats the context window like RAM and external storage like disk; the LLM itself pages memories in and out via function calls, with recursive summarization on overflow. ([arXiv:2310.08560](https://arxiv.org/abs/2310.08560))

**Mem0** (2025) is the production-oriented pipeline: extract salient facts → LLM decides ADD/UPDATE/DELETE/NOOP against existing memories (consolidation and contradiction-resolution) → vector retrieval. Verified: **26% relative quality improvement over OpenAI's memory, 91% lower p95 latency, >90% token savings** vs. stuffing full history in context. ([arXiv:2504.19413](https://arxiv.org/abs/2504.19413))

**HippoRAG** (NeurIPS 2024) builds a knowledge graph over content and retrieves via Personalized PageRank — **up to +20% on multi-hop QA, 10–30× cheaper** than iterative retrieval. ([arXiv:2405.14831](https://arxiv.org/abs/2405.14831))

**A-Mem** (NeurIPS 2025) stores Zettelkasten-style linked notes where new memories can update old ones. **MemoryBank** (2023) adds Ebbinghaus-style forgetting: memories decay unless re-used. ([arXiv:2502.12110](https://arxiv.org/abs/2502.12110), [arXiv:2305.10250](https://arxiv.org/abs/2305.10250))

## 4. Self-improvement loops: the critical caveat

**Reflexion** (NeurIPS 2023): act → get *external* feedback (tests, environment signal) → verbally reflect on the failure → store the reflection in episodic memory → retry. Verified: **91% on HumanEval vs. 80% GPT-4 baseline**. ([arXiv:2303.11366](https://arxiv.org/abs/2303.11366))

**The warning that shapes everything:** Huang et al. (ICLR 2024), *"Large Language Models Cannot Self-Correct Reasoning Yet"* — verified finding: **without external feedback, self-correction often makes performance WORSE** (e.g., GPT-3.5 fell from 75.8% to 38.1% on CommonSenseQA after one "fix your answer" round). If a model could spot its own error, it usually wouldn't have made it. ([arXiv:2310.01798](https://arxiv.org/abs/2310.01798))

**CRITIC** (ICLR 2024) confirms the flip side: self-correction *grounded in tools* (search, interpreter) works (+7 points on QA/math), and its own ablation shows gains largely vanish when tools are removed. ([arXiv:2305.11738](https://arxiv.org/abs/2305.11738))

**LLM-as-judge** (NeurIPS 2023): GPT-4-grade judges agree with humans **>80%** — usable as a quality gate — but carry position, verbosity, and self-preference biases. ([arXiv:2306.05685](https://arxiv.org/abs/2306.05685))

**Rule:** reflection loops must be anchored to something external — a screenshot, a DOM assertion, a test — never pure "think again."

## 5. Vision-grounded, self-healing UI automation

**SeeAct** (ICML 2024): GPT-4V can *plan* web tasks well (51.1% success with perfect grounding) but *grounding* — mapping the plan to the right element — is the bottleneck, costing 20–25% of actions. Notably, set-of-marks overlays were **not** effective on dense web pages; ranking real DOM candidates worked better. ([arXiv:2401.01614](https://arxiv.org/abs/2401.01614))

**WebVoyager** (ACL 2024): screenshot + numbered interactive elements → **59.1%** end-to-end success on live websites, far above text-only agents; its GPT-4V auto-evaluator agreed with humans 85.3% of the time. ([arXiv:2401.13919](https://arxiv.org/abs/2401.13919))

**UGround** (ICLR 2025 Oral): a dedicated visual grounding model (trained on 10M GUI elements) maps element *descriptions* to pixel coordinates — selector-free, so DOM churn can't break it; vision-only agents with UGround beat agents that also read HTML. ([arXiv:2410.05243](https://arxiv.org/abs/2410.05243))

**Industry self-healing** (Healenium; Playwright v1.56 "Healer" agent): store the last-known-good DOM; when a selector breaks, diff old vs. new DOM, score candidates, substitute the best match, and report the healed locator. Simple, no ML required. ([healenium.io](https://healenium.io/))

## What combines well (the synthesis)

The families are complementary, not competing, and the strongest published systems stack them:

1. **External verification first** (family 4's caveat): every learning signal must come from something real — a DOM assertion, a screenshot check, a vision-model judgment — because ungrounded self-critique backfires.
2. **Episodic memory of attempts** (Reflexion/ReasoningBank): store what was tried, what happened, and the reflection — including failures.
3. **Distillation** (ExpeL/Generative Agents reflection): periodically compress raw episodes into a small set of high-value lessons and reusable workflows; retrieval quality beats memory quantity.
4. **Procedure library** (Voyager/AWM): successful action sequences become retrievable, composable recipes — memory that *acts*.
5. **Vision grounding as the fallback** (SeeAct/UGround/Healenium): when selectors drift, describe the element and find it visually or by DOM diff, then write the fix back to memory.

Known failure modes to design against: memory bloat (fix: consolidation + forgetting curves, Mem0/MemoryBank), wrong-lesson retrieval (fix: score memories by later usefulness, ReasoningBank), judge errors polluting memory (fix: only high-confidence outcomes get written), and compounding errors in online learning (fix: quarantine new workflows until they succeed twice).

## Sources

ReasoningBank [arXiv:2509.25140](https://arxiv.org/abs/2509.25140) · ExpeL [arXiv:2308.10144](https://arxiv.org/abs/2308.10144) · Buffer of Thoughts [arXiv:2406.04271](https://arxiv.org/abs/2406.04271) · Memory-of-Thought [arXiv:2305.05181](https://arxiv.org/abs/2305.05181) · AWM [arXiv:2409.07429](https://arxiv.org/abs/2409.07429) · Voyager [arXiv:2305.16291](https://arxiv.org/abs/2305.16291) · Synapse [arXiv:2306.07863](https://arxiv.org/abs/2306.07863) · AutoManual [arXiv:2405.16247](https://arxiv.org/abs/2405.16247) · Generative Agents [arXiv:2304.03442](https://arxiv.org/abs/2304.03442) · MemGPT [arXiv:2310.08560](https://arxiv.org/abs/2310.08560) · Mem0 [arXiv:2504.19413](https://arxiv.org/abs/2504.19413) · HippoRAG [arXiv:2405.14831](https://arxiv.org/abs/2405.14831) · A-Mem [arXiv:2502.12110](https://arxiv.org/abs/2502.12110) · MemoryBank [arXiv:2305.10250](https://arxiv.org/abs/2305.10250) · Reflexion [arXiv:2303.11366](https://arxiv.org/abs/2303.11366) · Huang et al. [arXiv:2310.01798](https://arxiv.org/abs/2310.01798) · CRITIC [arXiv:2305.11738](https://arxiv.org/abs/2305.11738) · LLM-as-judge [arXiv:2306.05685](https://arxiv.org/abs/2306.05685) · SeeAct [arXiv:2401.01614](https://arxiv.org/abs/2401.01614) · WebVoyager [arXiv:2401.13919](https://arxiv.org/abs/2401.13919) · UGround [arXiv:2410.05243](https://arxiv.org/abs/2410.05243) · Healenium [healenium.io](https://healenium.io/)
