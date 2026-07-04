"""
intelligence/ - the self-improving layer for the DISH documentation automation.

The system follows a SEE -> PLAN -> VERIFY -> REMEMBER -> LEARN loop:

  resolver.py     SEE      - find on-screen elements by *meaning* ("the edit pencil"),
                             try ranked strategies, remember what worked (self-healing,
                             with quarantine: a learned selector needs 2 wins to be trusted).
  autorecipe.py   PLAN     - turn an official PDF/HTML into a step script automatically.
  verify.py       VERIFY   - after capture, self-check every frame and flag failures;
                             marks reports high_confidence so only grounded outcomes teach.
  memory.py       REMEMBER - REASONING IN MEMORY (RIM): the experience diary. Every build
                             attempt (success AND failure) is stored with a grounded
                             reflection; agents retrieve similar past experiences before
                             acting. Also holds lasting chat facts about the user.
  distill.py      LEARN    - compress the diary into output/lessons.md (max ~30 rules with
                             consolidation + decay); every agent prompt reads it.
  feedback.py     LEARN    - collect thumbs up/down, promote good selectors, flag bad steps.
  monitor.py               - detect UI drift by diffing fresh screenshots vs the last good build.
  llm.py                   - the pluggable "brain": add a model key and the vision/planning
                             parts switch on automatically. No key => graceful heuristics.
  orchestrator.py          - one entry point: PDF -> build -> verify -> report.

Nothing here needs a model to run; adding one in config/intelligence.json upgrades it.
"""
__all__ = ["resolver", "verify", "autorecipe", "feedback", "monitor", "llm",
           "orchestrator", "memory", "distill"]
