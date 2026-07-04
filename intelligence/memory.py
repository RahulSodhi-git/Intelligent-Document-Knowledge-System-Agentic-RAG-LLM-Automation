"""
memory.py - REASONING IN MEMORY (RIM): the episodic experience store.

The agent keeps a diary. Every build attempt (canonical, adhoc, or live-agent) is stored
as one experience: what was asked, what happened, the verify score, and a short REFLECTION
explaining WHY it went the way it did. Failures are stored too - research (ReasoningBank,
ExpeL) shows failure memories help as much as successes. Before acting on a new task, the
agent retrieves its most similar past experiences and reads them, so it starts from what
it already learned instead of from zero.

Grounding rule (non-negotiable, from the self-correction literature): a reflection is only
generated FROM the verify report / gate result - never free-form "think again". And only
HIGH-CONFIDENCE outcomes (verify.high_confidence) are eligible for lesson distillation, so
a shaky judge can never teach the system wrong lessons.

Stores (all human-readable JSON under output/):
  experience.json   - the episodic diary (capped, oldest evicted)
  chat_memory.json  - lasting user facts extracted from chat (consolidated ADD/UPDATE/DELETE)
"""
import json, re, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "output"
STORE = OUT / "experience.json"
CHAT_STORE = OUT / "chat_memory.json"
MAX_EXPERIENCES = 400      # diary cap: oldest evicted first (bounded memory, no bloat)
MAX_CHAT_FACTS = 12


# ── store I/O ─────────────────────────────────────────────────────────────────
def _load():
    try:
        return json.loads(STORE.read_text(encoding="utf-8"))
    except Exception:
        return {"experiences": []}


def _save(d):
    OUT.mkdir(parents=True, exist_ok=True)
    d["experiences"] = d["experiences"][-MAX_EXPERIENCES:]
    STORE.write_text(json.dumps(d, indent=2), encoding="utf-8")


# ── reflection (grounded in the verify report, never free-form) ───────────────
def _heuristic_reflection(outcome, verify_report):
    """No-model fallback: summarise the verify report's concrete findings."""
    if not verify_report:
        return "No verify report available for this run."
    bits = []
    for s in verify_report.get("steps", []):
        if s.get("status") != "ok" and s.get("issues"):
            bits.append("step %s: %s" % (s.get("step"), "; ".join(s["issues"])[:80]))
        if len(bits) >= 4:
            break
    if outcome == "success" and not bits:
        return "All steps passed self-check (score %s)." % verify_report.get("score")
    return ("Score %s. Problems: %s" % (verify_report.get("score"), " | ".join(bits))
            if bits else "Score %s, no step-level issues recorded." % verify_report.get("score"))


def _reflect(task, outcome, verify_report, gate_result):
    """One-paragraph lesson for the diary. Model-written when available, but ONLY from the
    verify report's real findings (grounded); heuristic summary otherwise."""
    from . import llm
    if not llm.available() or not verify_report:
        return _heuristic_reflection(outcome, verify_report)
    findings = [{"step": s.get("step"), "status": s.get("status"),
                 "issues": s.get("issues", []), "vision": s.get("vision", "")}
                for s in verify_report.get("steps", []) if s.get("status") != "ok"][:8]
    prompt = (
        "You are writing one diary entry for a documentation-automation agent.\n"
        "TASK: %s\nOUTCOME: %s (score %s, gate: %s)\n"
        "VERIFIED FINDINGS (the only evidence you may use - do not invent anything):\n%s\n\n"
        "Write 1-3 short sentences: what went right/wrong and the practical lesson for next "
        "time. Base every statement strictly on the findings above."
        % (task, outcome, verify_report.get("score"),
           (gate_result or {}).get("decision", "?"),
           json.dumps(findings) if findings else "(no step-level issues; everything passed)"))
    ans = llm.ask_text(prompt, max_tokens=160)
    return (ans or _heuristic_reflection(outcome, verify_report)).strip()[:500]


# ── writing experiences ────────────────────────────────────────────────────────
def record_build(qid, task, section, verify_report, gate_result, kind="build", details=None):
    """Store one build attempt as an experience. Failures are stored too - they are the
    most useful memories. Returns the entry."""
    score = (verify_report or {}).get("score")
    decision = (gate_result or {}).get("decision", "")
    outcome = "success" if decision == "publish" else ("failure" if (score or 0) < 60 else "review")
    entry = {
        "ts": int(time.time()), "kind": kind, "qid": qid, "task": (task or "")[:200],
        "section": section or "", "outcome": outcome, "score": score,
        "gate": decision,
        "high_confidence": bool((verify_report or {}).get("high_confidence")),
        "reflection": _reflect(task, outcome, verify_report, gate_result),
    }
    if details:
        entry["details"] = details
    d = _load()
    d["experiences"].append(entry)
    _save(d)
    print("MEMORY: recorded %s experience for %s (score %s, %s)"
          % (outcome, ("Q%02d" % qid) if isinstance(qid, int) else qid, score,
             "high-conf" if entry["high_confidence"] else "low-conf"))
    return entry


def record_event(kind, task, note, qid=None, section=None):
    """Lightweight experience for non-build events (e.g. a healed selector)."""
    d = _load()
    entry = {"ts": int(time.time()), "kind": kind, "qid": qid, "task": (task or "")[:200],
             "section": section or "", "outcome": "event", "score": None,
             "high_confidence": True, "reflection": (note or "")[:300]}
    d["experiences"].append(entry)
    _save(d)
    return entry


# ── retrieving experiences (the "reasoning in" part of RIM) ───────────────────
_STOP = set("a an the to of for and or in on with how do i my is are set up add new".split())


def _tokens(s):
    return {w for w in re.findall(r"[a-z]{3,}", (s or "").lower()) if w not in _STOP}


def retrieve(task, k=3, kinds=None):
    """Most similar past experiences for a task (token overlap + recency tiebreak).
    Dependency-free on purpose: works with or without chromadb/models."""
    q = _tokens(task)
    if not q:
        return []
    scored = []
    for e in _load()["experiences"]:
        if kinds and e.get("kind") not in kinds:
            continue
        t = _tokens(e.get("task", "") + " " + e.get("reflection", ""))
        overlap = len(q & t)
        if overlap:
            scored.append((overlap, e.get("ts", 0), e))
    scored.sort(key=lambda x: (-x[0], -x[1]))
    return [e for _, _, e in scored[:k]]


def context_for(task, k=3):
    """Prompt-ready block: relevant past experiences + the distilled lessons. This is what
    gets injected before the agent acts, so it reasons WITH its memory."""
    parts = []
    past = retrieve(task, k=k)
    if past:
        lines = []
        for e in past:
            lines.append("- [%s/%s score=%s] %s -> %s"
                         % (e.get("kind"), e.get("outcome"), e.get("score"),
                            e.get("task", "")[:70], e.get("reflection", "")[:160]))
        parts.append("PAST EXPERIENCE (your own diary; learn from it):\n" + "\n".join(lines))
    try:
        from . import distill
        les = distill.lessons()
        if les:
            parts.append("DISTILLED LESSONS (rules learned across many runs):\n" + les)
    except Exception:
        pass
    return "\n\n".join(parts)


# ── chat facts memory (lasting user context, Mem0-style consolidation) ────────
def _chat_load():
    try:
        return json.loads(CHAT_STORE.read_text(encoding="utf-8"))
    except Exception:
        return {"facts": []}


def remember_chat(msg):
    """Extract lasting facts from a chat message and consolidate them against what is
    already known (ADD / UPDATE / DELETE / NOOP). Needs a model; silently no-ops without."""
    from . import llm
    if not llm.available() or len((msg or "").strip()) < 8:
        return None
    known = _chat_load()["facts"]
    prompt = (
        "You maintain long-term memory for a restaurant-software help assistant.\n"
        "KNOWN FACTS about this user (may be empty):\n%s\n\n"
        "NEW USER MESSAGE: \"%s\"\n\n"
        "Update the fact list: keep facts that still hold, update changed ones, drop "
        "contradicted ones, add NEW lasting facts (restaurant setup, preferences, recurring "
        "products - NOT one-off requests). Max %d short facts. Reply with a STRICT JSON "
        "array of strings only. If nothing lasting is learned, return the list unchanged."
        % (json.dumps(known), msg[:300], MAX_CHAT_FACTS))
    ans = llm.ask_text(prompt, max_tokens=300)
    m = re.search(r"\[.*\]", ans or "", re.S)
    if not m:
        return None
    try:
        facts = [str(f)[:120] for f in json.loads(m.group(0))][:MAX_CHAT_FACTS]
    except Exception:
        return None
    CHAT_STORE.write_text(json.dumps({"facts": facts, "updated": int(time.time())},
                                     indent=2), encoding="utf-8")
    return facts


def chat_context():
    """Remembered user facts, formatted for the answer tiers' history."""
    facts = _chat_load()["facts"]
    return ["(remembered about this user) %s" % f for f in facts[:6]]


# ── status ────────────────────────────────────────────────────────────────────
def stats():
    d = _load()["experiences"]
    per = {}
    for e in d:
        per[e.get("outcome", "?")] = per.get(e.get("outcome", "?"), 0) + 1
    return {"experiences": len(d), "by_outcome": per,
            "high_confidence": sum(1 for e in d if e.get("high_confidence")),
            "chat_facts": len(_chat_load()["facts"])}


if __name__ == "__main__":
    print(json.dumps(stats(), indent=2))
