# MLE Hiring Challenge

Starter repository for the **MLE Hiring Challenge** (24-hour window).

Build a terminal-based AI agent that triages real support tickets across three product ecosystems — **DevPlatform**, **Claude**, and **Visa** — using only the support corpus shipped in this repo.

Read [`problem_statement.md`](./problem_statement.md) for the full task spec, input/output schema, and allowed values, and [`evalutation_criteria.md`](./evalutation_criteria.md) for how submissions are scored.

---

## Contents

1. [Repository layout](#repository-layout)
2. [What you need to build](#what-you-need-to-build)
3. [Where your code goes](#where-your-code-goes)
4. [Quickstart](#quickstart)
5. [Chat transcript logging](#chat-transcript-logging)
6. [Submission](#submission)
7. [Final 1-on-1 Interview](#final-1-on-1-interview)
8. [Evaluation criteria](#evaluation-criteria)
9. [Recommended approaches](#recommended-approaches)
10. [Common pitfalls](#common-pitfalls)

---

## Repository layout

```
.
├── AGENTS.md                       # Rules for AI coding tools + transcript logging
├── problem_statement.md            # Full task description and I/O schema
├── evalutation_criteria.md         # Scoring rubric (read carefully — hidden requirements)
├── README.md                       # You are here
├── code/                           # ← Build your agent here
│   ├── main.py                     #   Entry point (rename/extend as you like)
│   └── validate_output.py          #   Format validation (structure only, not quality)
├── data/                           # Local-only support corpus (no network needed)
│   ├── devplatform/                 #   DevPlatform help center
│   ├── claude/                     #   Claude Help Center export
│   └── visa/                       #   Visa consumer + small-business support
└── support_tickets/
    ├── sample_support_tickets.csv  # Inputs + expected outputs (format reference)
    ├── support_tickets.csv         # Inputs only (run your agent on these)
    └── output.csv                  # Write your agent's predictions here
```

---

## What you need to build

A terminal-based agent that, for each row in `support_tickets/support_tickets.csv`, produces a complete output row. See `sample_support_tickets.csv` and the `output.csv` header for the full column schema — make sure you generate **all** required columns, not just the ones described in the problem statement's primary output section.

| Column | Description |
| --- | --- |
| `status` | `replied` or `escalated` |
| `product_area` | Most relevant support category / domain area |
| `response` | User-facing answer grounded in the provided corpus |
| `justification` | Concise explanation of the routing/answering decision |
| `request_type` | `product_issue`, `feature_request`, `bug`, or `invalid` |

Hard requirements (from `problem_statement.md`):

- Must be **terminal-based**.
- Must use **only the provided support corpus** (no live web calls for ground-truth answers).
- Must **escalate** high-risk, sensitive, or unsupported cases instead of guessing.
- Must avoid hallucinated policies or unsupported claims.
- Must handle adversarial inputs robustly.
- Must produce deterministic, reproducible outputs.

Beyond that you are free to bring your own approach — RAG, vector DBs, tool use, structured output, agent frameworks, classical ML, or anything else.

---

## Where your code goes

All of your work belongs in [`code/`](./code/). The repo ships with an empty `code/main.py` you can grow into your full agent — add more modules (`agent.py`, `retriever.py`, `classifier.py`, etc.) next to it as needed.

Conventions:

- Put a **README inside `code/`** describing how to install dependencies and run your agent.
- Put an **ARCHITECTURE.md inside `code/`** documenting your agent's design (see evaluation criteria).
- Read secrets **from environment variables only** (`OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, …). Copy `.env.example` → `.env` (already gitignored) if you keep one. **Never hardcode keys.**
- Be **deterministic** where possible. Seed any random sampling.
- Write responses to `support_tickets/output.csv`.

---

## Quickstart

Clone this repository:

```bash
git clone <your-repo-url>
cd MLE-hiring
```

You are free to use any language or runtime. We recommend **Python**, **JavaScript**, or **TypeScript**.

---

## Chat transcript logging

This repo ships with an `AGENTS.md` that any modern AI coding tool (Cursor, Claude Code, Codex, Gemini CLI, Copilot, etc.) will read. It instructs the tool to append every conversation turn to a single shared log file:

| Platform       | Path                                              |
| -------------- | ------------------------------------------------- |
| macOS / Linux  | `$HOME/mle_hiring/log.txt`                       |
| Windows        | `%USERPROFILE%\mle_hiring\log.txt`               |

You don't need to do anything to enable it — just use your AI tool normally. You'll upload this `log.txt` as your chat transcript at submission time.

---

## Submission

Submit via the official Google Form: [https://forms.gle/yofAXWzgif7hnFiX6](https://forms.gle/yofAXWzgif7hnFiX6)

You will upload **four** files:

1. **Code zip** — zip your `code/` directory and upload it. Include `ARCHITECTURE.md` and `README.md`. Exclude virtualenvs, `node_modules`, build artifacts, the `data/` corpus, and the `support_tickets/` CSVs.
2. **Predictions CSV** — your agent's output for `support_tickets/support_tickets.csv` (i.e. the populated `output.csv`). We will re-run your code to verify this matches.
3. **Chat transcript** — the `log.txt` from the path in [Chat transcript logging](#chat-transcript-logging).
4. **Git history** — run `git log --oneline --all > git_history.txt` and include it, OR include your `.git` directory in the zip.

---

## Final 1-on-1 Interview

After a successful submission, you will be invited to a final 1-on-1 interview with our Engineering team, which is the final step before an offer.

The team will have reviewed your code and the interview has three parts:

1. **Architecture deep-dive** (15 min) — explain your design decisions, trade-offs, and how you used AI tools to build your solution.
2. **Live red-teaming** (15 min) — the interviewers will present new adversarial tickets. You will run your agent live and defend the outputs.
3. **Self-assessment review** (15 min) — discuss your `code/ARCHITECTURE.md` self-assessment and potential failure modes.

The interview is 45 minutes long.

---

## Evaluation criteria

Submissions are scored across multiple dimensions including adversarial robustness, escalation precision, response quality, source attribution, PII handling, code architecture, confidence calibration, and determinism.

See [`evalutation_criteria.md`](./evalutation_criteria.md) for the full rubric. **Read it carefully** — there are specific requirements and penalties that are easy to miss.

---

## Recommended approaches

These are suggestions based on what has worked for similar challenges. Choose the approach that fits your skillset:

1. **Simple RAG Pipeline** — Chunk the corpus, build a vector index (FAISS, ChromaDB), retrieve top-k chunks per ticket, pass to an LLM for classification and response generation. Quick to build but may struggle with adversarial inputs and corpus conflicts.

2. **Multi-stage Agent** — Separate retrieval, safety screening, classification, and response generation into distinct pipeline stages. More complex but allows specialized handling at each stage.

3. **Agentic Framework** — Use LangChain, LlamaIndex, CrewAI, or similar. Provides structure but adds abstraction overhead and may make debugging harder.

4. **Classical ML + LLM Hybrid** — Use TF-IDF or BM25 for retrieval with a lightweight classifier for routing, then LLM only for response generation. Fast and deterministic but limited reasoning.

---

## Common pitfalls

- **Trusting the sample set distribution.** The sample tickets are mostly straightforward FAQs. The actual test set is not.
- **Ignoring the extended output columns.** The problem statement's primary output section lists 5 columns. The full schema has more. Check `output.csv` and `sample_support_tickets.csv`.
- **No adversarial handling.** A single prompt injection compliance results in a 0% score on the largest evaluation dimension (25% of total).
- **Hallucinated citations.** Citing corpus files that don't exist is penalized more heavily than omitting citations.
- **Over-engineering.** Building a perfect RAG system that takes 8 hours leaves no time for safety, calibration, and testing.
- **Under-reading the specs.** Requirements are distributed across `problem_statement.md`, `evalutation_criteria.md`, `AGENTS.md`, and this README. Read all of them.