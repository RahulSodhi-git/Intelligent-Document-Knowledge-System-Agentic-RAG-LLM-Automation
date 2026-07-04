# Intelligence Upgrade Plan for dish_doc_automation

*Maps the verified research (see RESEARCH_SUMMARY.md) onto the existing codebase. Ordered by impact-per-effort. July 2026.*

## Where the project already stands

The codebase already has the skeleton the research recommends — which is why these upgrades are incremental, not rewrites:

| Research concept | Existing counterpart | Gap |
|---|---|---|
| Skill library (Voyager/AWM) | `recipes/QNN_capture.json` | Recipes are hand-written and static; nothing is learned back into them |
| Self-healing selectors | `intelligence/resolver.py` + `resolver_cache.json` | Heuristic ranking only; no DOM-diff repair, no vision fallback |
| Verification (Reflexion signal) | `intelligence/verify.py` 0–100 score | Heuristic checks; can't *see* the screenshots |
| Feedback memory | `intelligence/feedback.py` (`feedback.json`) | Stored but never distilled into lessons |
| Retrieval | chromadb RAG (`rag/`) | Indexes guide text only, not experiences or reasoning |
| Live agent loop | `intelligence/live_agent.py` | Starts from zero every run; no memory of past attempts |

## Phase 1 — Grounded verification (the foundation, do first)

**Research basis:** Huang et al. (self-correction without external feedback backfires); Reflexion (external signal makes it work); LLM-as-judge (>80% human agreement, usable as a gate).

**Why first:** every later phase writes to memory, and memory is only as good as the signal that labels an attempt "success" or "failure." Get the judge right before you let anything learn.

**Changes:**
- `verify.py`: add vision verification. For each captured frame, send screenshot + expected caption to the vision model (`config/intelligence.json` already has the hook): "Does this screenshot show X? Is the highlight on the right control? yes/no + reason." Blend into the existing 0–100 score.
- Keep the deterministic checks (blank/duplicate frame, `assert_found`) — they're the cheap, unbiased part of the signal.
- Add a confidence field to `verify_qNN.json`: only HIGH-confidence outcomes may later be written to memory (protects against judge errors polluting memory — the ReasoningBank failure mode).

**Effort:** small (the plumbing exists). **Payoff:** every guide gets real eyes; everything downstream becomes trustworthy.

## Phase 2 — Episodic memory + reflection (the RIM core)

**Research basis:** ReasoningBank (store strategies from successes AND failures, +34% relative); ExpeL (insights + trajectories, no training needed); Reflexion (verbal reflections in episodic memory).

**Changes:**
- New module `intelligence/memory.py` with one store, `output/experience.json` (later chromadb): one entry per build/attempt: `{task, qid, screen, actions_tried, outcome, verify_score, reflection}`.
- After every build, generate the reflection with the LLM — grounded in Phase 1's verify report, never free-form: "Step 4 failed because the dropdown needed a settle; selector B worked after waiting."
- **Write failures too** — ReasoningBank's key finding is that failure memories are as valuable as successes.
- Retrieval hook in `live_agent.py` and the build path in `server.py`: before acting, pull the 3 most similar past experiences (embed on task + screen, reuse the existing chromadb) and inject into the prompt.

**Effort:** medium. **Payoff:** the agent stops re-solving solved problems; each failure becomes fuel.

## Phase 3 — Distillation into lessons (compressed wisdom)

**Research basis:** ExpeL insights; Generative Agents reflection (ablating it degrades behavior); Buffer of Thoughts templates; AutoManual rule book.

**Changes:**
- New `intelligence/distill.py`, run manually or nightly: LLM reads recent `experience.json` entries and updates `output/lessons.md` — max ~30 rules, each tagged by section/screen ("Self-service pages: wait for the table before clicking rows").
- Every agent prompt (`live_agent.py`, `resolver.py` vision path, chat polish in `agent.py`) loads `lessons.md` — small, so it always fits in context.
- Consolidation à la Mem0: distill decides ADD / UPDATE / DELETE / NOOP per rule; rules that stop being confirmed decay out (MemoryBank forgetting). This prevents memory bloat and stale lessons.

**Effort:** small once Phase 2 exists. **Payoff:** raw episodes become a curated instruction manual the whole system shares — AutoManual showed this alone reaches ~97% on ALFWorld.

## Phase 4 — Self-healing recipes (workflow memory that acts)

**Research basis:** AWM (+51% relative on WebArena from induced workflows); Voyager skill library (verified successes become retrievable, composable skills); Healenium/Playwright-Healer (DOM-diff locator repair); SeeAct (rank real DOM candidates — the engine's `_CANDS_JS` already does exactly this, which SeeAct found beats set-of-marks).

**Changes:**
- `resolver.py`: on selector failure, don't abort — (a) diff the stored last-known-good element context vs. the current DOM candidates from `_CANDS_JS`, (b) let the vision/text model pick the equivalent element, (c) execute, and on verified success **write the healed selector back into the recipe JSON** and log it to `experience.json`.
- Quarantine rule (AWM's online-mode risk): a healed selector or new auto-recipe stays "provisional" until it succeeds twice with a passing verify score; only then is it promoted (extend the existing `promote.py`).
- `autorecipe.py`: when the live agent completes a novel task with a high verify score, induce a proper `QNN_capture.json` from its trajectory — Voyager-style: verified successes become permanent skills.

**Effort:** medium-large. **Payoff:** UI drift stops breaking builds; the recipe library grows itself.

## Phase 5 — Memory-aware chat + richer RAG

**Research basis:** Mem0 (extract-consolidate-retrieve for chat, 26% quality gain, >90% token savings); HippoRAG (graph retrieval for multi-hop questions); Synapse (trajectories as retrievable exemplars).

**Changes:**
- `server.py` chat: replace the 6-message deque with extract-and-consolidate memory (Mem0 pattern): after each chat, extract salient facts ("user's restaurant uses Italian regime settings"), consolidate against existing ones, retrieve at answer time.
- `rag/`: index screen-content descriptions from the enriched manifests (what's actually visible on each screen), so "where do I find allergens?" is answered from UI reality, not just guide titles. Graph-style linking (screen → guide → section) is the later HippoRAG-flavored step if multi-hop questions show up.

**Effort:** medium. **Payoff:** the chatbot personalizes and answers "where is X" questions it currently can't.

## Order and safeguards

Order: **1 → 2 → 3 → 4 → 5.** Each phase makes the next one safer: grounded verification (1) labels experiences (2), which distill into lessons (3), which guide healing and skill growth (4), all surfaced through smarter chat (5).

Design-in the documented failure modes from day one:

- **No ungrounded self-critique** — every reflection cites a verify report or screenshot (Huang et al.).
- **High-confidence writes only** — uncertain outcomes never enter memory (ReasoningBank).
- **Quarantine before promotion** — new workflows/selectors must succeed twice (AWM online risk).
- **Bounded memory** — lessons capped and decaying; episodes consolidated (Mem0/MemoryBank).
- Existing safety stays non-negotiable: sandbox-only, destructive-click blocklist, step caps in `live_agent.py`.

## Success metrics

Track per phase, using infrastructure that already exists: average verify score across all 44 questions; % of builds needing manual .bat rework; selector failures auto-healed vs. aborted; live-agent steps-per-task (ReasoningBank saw 16% fewer steps once memory kicked in); chat answer 👍 rate from `feedback.json`.
