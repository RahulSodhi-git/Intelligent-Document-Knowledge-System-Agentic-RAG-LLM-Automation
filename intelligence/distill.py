"""
distill.py - turn the raw experience diary into a small book of LESSONS.

Raw episodic memories pile up; wisdom should not. This module periodically reads the
diary (output/experience.json) and rewrites output/lessons.md - a capped list of short,
practical rules ("Self-service pages: wait for the table before clicking rows"). Every
agent prompt loads lessons.md, so one distilled rule improves EVERY future run.

Consolidation, not accumulation (the Mem0/ExpeL pattern):
  - only HIGH-CONFIDENCE experiences may teach (verify.high_confidence gate);
  - the model decides ADD / UPDATE / DELETE per rule against the current lessons;
  - hard cap on rule count -> stale rules get pushed out (forgetting is a feature);
  - without a model, a heuristic aggregates recurring verified issues into rules, and
    regenerates from scratch each run so dead lessons decay away automatically.

Run:  python -m intelligence.distill        (or POST /api/distill from the chatbot UI)
"""
import json, re, time
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "output"
LESSONS = OUT / "lessons.md"
MAX_RULES = 30
MAX_CHARS = 4000     # what lessons() will ever inject into a prompt


def lessons():
    """The current lesson book (prompt-ready), or '' if none distilled yet."""
    try:
        return LESSONS.read_text(encoding="utf-8").strip()[:MAX_CHARS]
    except Exception:
        return ""


def _experiences(limit=200):
    try:
        d = json.loads((OUT / "experience.json").read_text(encoding="utf-8"))
    except Exception:
        return []
    # only high-confidence outcomes may teach; most recent first
    exps = [e for e in d.get("experiences", []) if e.get("high_confidence")]
    return exps[-limit:]


def _heuristic(exps):
    """No-model fallback: count recurring problems across verified runs and write the
    repeat offenders as rules. Regenerated from scratch each time = built-in decay."""
    fail_bits = Counter()
    for e in exps:
        r = (e.get("reflection") or "").lower()
        for pat, rule in (
            ("blank", "Some steps captured blank frames - add/lengthen a settle before the snap."),
            ("not rendered", "Frames missing for some steps - check the snap numbering matches the script."),
            ("no screenshot", "Steps ran without a screenshot - every step needs a snap action."),
            ("wrong element", "Highlight boxes landed on the wrong element - prefer more specific selectors or a vhint."),
            ("screen mismatch", "Screenshots showed the wrong screen - add a wait/settle after navigation before snapping."),
            ("not found", "A named product was missing from the catalogue - assert_found before editing rows."),
            ("timeout", "Selectors timed out - the page needed more settle time or the selector has drifted."),
        ):
            if pat in r:
                fail_bits[rule] += 1
    good = sum(1 for e in exps if e.get("outcome") == "success")
    lines = ["# Lessons (auto-distilled, heuristic mode)",
             "", "_%d verified experiences read; %d successes. Rules seen 2+ times:_" % (len(exps), good), ""]
    rules = [r for r, n in fail_bits.most_common(MAX_RULES) if n >= 2]
    if not rules:
        lines.append("- No recurring problems detected across verified runs yet.")
    for r in rules:
        lines.append("- %s (seen %dx)" % (r, fail_bits[r]))
    return "\n".join(lines)


def run(limit=200):
    """Distill the diary into lessons.md. Returns the new text."""
    exps = _experiences(limit)
    if not exps:
        print("DISTILL: no high-confidence experiences yet - nothing to learn from.")
        return lessons()
    from . import llm
    text = None
    if llm.available():
        diary = "\n".join("- [%s/%s score=%s%s] %s :: %s"
                          % (e.get("kind"), e.get("outcome"), e.get("score"),
                             (" " + e.get("section")) if e.get("section") else "",
                             e.get("task", "")[:70], e.get("reflection", "")[:160])
                          for e in exps[-120:])
        cur = lessons() or "(no lessons yet)"
        prompt = (
            "You maintain the lesson book of a documentation-automation agent for the DISH "
            "POS Backoffice (a web app driven with Playwright).\n\n"
            "CURRENT LESSON BOOK:\n%s\n\n"
            "RECENT VERIFIED EXPERIENCES (its diary - the only evidence):\n%s\n\n"
            "Rewrite the complete lesson book in markdown. Rules: max %d bullet lessons; "
            "each ONE short imperative sentence, prefixed with its scope in brackets like "
            "[Self-service] or [all screens]; KEEP lessons still supported by evidence, "
            "UPDATE ones the new evidence refines, DELETE ones nothing recent supports; "
            "never invent a lesson the diary does not show. A lesson must be ACTIONABLE - "
            "something that would change future behaviour (a pitfall, a timing rule, a "
            "selector quirk). Do NOT write restatements of tasks that simply succeeded; "
            "if the diary shows no problems, write NO lessons and say so in one line. "
            "Start with the heading '# Lessons (auto-distilled)'. Output only raw markdown "
            "with NO code fences."
            % (cur, diary, MAX_RULES))
        text = llm.ask_text(prompt, max_tokens=1200)
        if text:
            # models love wrapping output in ``` fences - strip them so lessons.md is clean
            text = re.sub(r"^\s*```[a-zA-Z]*\s*", "", text.strip())
            text = re.sub(r"\s*```\s*$", "", text)
        if text and "# Lessons" not in text:
            text = "# Lessons (auto-distilled)\n\n" + text
    if not text:
        text = _heuristic(exps)
    text = text.strip()[:MAX_CHARS + 2000]
    LESSONS.write_text(text + "\n\n_Distilled %s from %d experiences._\n"
                       % (time.strftime("%Y-%m-%d %H:%M"), len(exps)), encoding="utf-8")
    n = len(re.findall(r"^- ", text, re.M))
    print("DISTILL: wrote %d lessons -> output/lessons.md" % n)
    return text


def stats():
    return {"lessons_exist": LESSONS.exists(),
            "rules": len(re.findall(r"^- ", lessons(), re.M)),
            "teachable_experiences": len(_experiences())}


if __name__ == "__main__":
    run()
