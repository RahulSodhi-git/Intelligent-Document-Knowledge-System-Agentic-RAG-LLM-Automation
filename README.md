# Intelligent Document & Knowledge System — Agentic RAG + LLM Automation

An **agentic documentation-automation platform** that watches how a task is done in
a web application, turns it into a **step-by-step SOP with screenshots, a PDF, and a
video**, indexes everything into a **RAG knowledge base**, and answers colleagues'
questions through a chat assistant — with a self-improving agent loop that heals
itself when the target application's UI changes.

It runs on heuristics out of the box; add an LLM API key and the vision, planning,
and memory capabilities switch on.

---

## What it does

Three layers work together:

**1. Capture → Generate (the "doer")**
- A **Playwright** agent drives the target web app and records each step
  (`capture/`).
- A document generator turns the capture into a branded **PDF + video walkthrough**
  and per-question recipes (`generate/`, `recipes/`).

**2. Intelligence (the self-improving brain)** — `intelligence/`

```
 SEE ─► PLAN ─► CAPTURE ─► BUILD ─► VERIFY ─► REMEMBER ─► DISTILL ─┐
  ▲                ▲ (self-heal)              (diary)    (lessons) │
  └────────────────┴──── feedback + drift monitor ◄───────────────┘
```

| Stage | Role |
|-------|------|
| **SEE** (`resolver.py`) | Finds UI elements by *meaning* and ranks selector strategies by what worked before — self-healing selectors held in quarantine until proven. |
| **PLAN** (`autorecipe.py`) | Turns an official PDF/HTML into a step script + capture plan automatically. |
| **HEAL** | When selectors fail (UI drift), the model picks the intended control from the live page and clicks its real geometry — never onto destructive controls. |
| **VERIFY** (`verify.py`) | Self-checks every generated frame, scores it 0–100, and only lets grounded results teach the system. |
| **REMEMBER** (`memory.py`) | An experience diary of every build (success and failure) with reflections; agents retrieve similar past experiences before acting. |
| **DISTILL** (`distill.py`) | Compresses the diary into a compact `lessons.md` that every future run reads. |
| **LEARN / DRIFT / BRAIN** | Feedback reinforcement, screen-drift detection, and the single pluggable LLM entry point (`llm.py`). |

**3. Serve → Answer (the "teacher")**
- A **RAG engine** (`rag/`) indexes the generated docs (ChromaDB + sentence
  embeddings) for grounded, question-aware answers.
- A **Flask** server (`server.py`) exposes a chat API + an embeddable widget, and a
  **desktop app** (`desktop.py`) opens it as a native window for colleagues on the
  same network.

---

## Repository layout

```
capture/         # Playwright capture agent
generate/        # PDF + video + document generation
intelligence/    # self-improving agent loop (see table above)
rag/             # RAG engine, indexing, smart answers
recipes/         # per-question step scripts + capture plans
research/        # design notes and implementation write-ups
config/          # settings + example config (real config is git-ignored)
ui/              # chat widget templates/static
tools/           # evaluation, inspection and recipe-generation utilities
server.py        # Flask chat backend
desktop.py       # native desktop launcher
run_pipeline.py  # one command: capture → PDF/video → ingest into RAG
```

---

## Getting started

```bash
pip install -r requirements.txt
playwright install chromium

# End-to-end for one task: capture → generate → ingest
python run_pipeline.py                 # headed (watch the browser)
python run_pipeline.py --headless

# Serve the chat assistant
python server.py                       # → http://localhost:5000
python desktop.py                      # native desktop window
```

**Enabling the LLM layer:** add your API key to a local config (see
`config/intelligence.example.json`). Without a key the system falls back to
heuristics. Real config files, secrets, and generated `output/` are git-ignored —
keep credentials out of the repo.

---

## Tech stack

**Python** · **Playwright** · **Flask** · **ChromaDB + sentence-transformers**
(RAG) · **LLM-agnostic intelligence layer** · **PDF/video generation** ·
**pywebview** (desktop)
