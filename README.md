# Physical AI & Humanoid Robotics — an open textbook with a grounded AI tutor

[![CI](https://github.com/asadullah48/physical-ai-textbook-speckit/actions/workflows/ci.yml/badge.svg)](https://github.com/asadullah48/physical-ai-textbook-speckit/actions/workflows/ci.yml)

**▶ Read it: [asadullah48.github.io/physical-ai-textbook-speckit](https://asadullah48.github.io/physical-ai-textbook-speckit/)**

A 13-week course, written as a Docusaurus textbook, with a retrieval-augmented tutor that answers **from the book and cites the section it used**. The tutor works with no server: the site ships a search index of every chapter and answers in the reader's browser. When the FastAPI + Gemini + Qdrant backend is deployed and healthy, the same chat widget switches to generated answers over the same passages.

Built for the Panaversity Physical AI hackathon with Spec-Kit Plus (spec → plan → tasks → implementation; see `specs/` and `history/`).

## What's in the book

| Module | Weeks | Chapters |
|---|---|---|
| 1. Introduction to Physical AI | 1–2 | What is Physical AI · Sensor systems · Embodied intelligence · Humanoid advantages |
| 2. ROS 2 Fundamentals | 3–5 | ROS 2 architecture (DDS, QoS, nodes, topics) · Services, actions & parameters · URDF, TF2 & launch files |
| 3. Simulation | 6–7 | Gazebo (Harmonic) fundamentals · Sensor simulation & `ros_gz_bridge` · Sim-to-real transfer |
| 4. NVIDIA Isaac | 8–10 | Isaac Sim & USD · Isaac ROS perception (cuVSLAM, nvblox) · Nav2 & bipedal locomotion |
| 5. Vision-Language-Action | 11–13 | VLA architecture · Voice-to-action pipelines · LLM task planning + capstone |

Plus an instructor guide with a week-by-week schedule. Every chapter has learning objectives, runnable code, a common-pitfalls section and graded exercises. Version assumptions (ROS 2 Humble/Jazzy, Gazebo Harmonic, Isaac Sim 4.x) are stated in each chapter.

## The AI tutor

```
Reader asks  ─►  ChatWidget
                   │ GET /api/health (once, 3.5 s timeout)
                   ├─ backend healthy (DB + vector store) ─► FastAPI RAG: Gemini embeddings → Qdrant → Gemini answer
                   └─ otherwise ─────────────────────────► in-browser: BM25 over static/search-index.json
                                                            → extractive answer made only of book sentences
Both paths return numbered citations that link to the exact section (heading anchor).
```

- **Grounded by construction (browser mode).** The answer is assembled from sentences that exist in the cited passages; a test checks this against the real index. Out-of-scope questions get "I couldn't find that in the textbook", not a guess.
- **Highlight-to-ask.** Select any text on a page to ask about it; the selection becomes retrieval context.
- **Honest labelling.** Every answer says which engine produced it.
- **Index built at build time** by `frontend/scripts/build-search-index.mjs`: chapters are split by H2/H3 into ~300 chunks carrying their Docusaurus route and heading anchor.

## Backend (optional, for generated answers and accounts)

FastAPI · SQLAlchemy async + Alembic on Neon Postgres · Qdrant · Gemini via the `google-genai` SDK · JWT auth with refresh tokens · rate limiting · SSE streaming.

```bash
cd backend
pip install -r requirements-dev.txt
cp .env.example .env                                   # DATABASE_URL, QDRANT_*, GOOGLE_API_KEY, JWT_SECRET_KEY
alembic upgrade head
python -m src.scripts.ingest.ingest_content --docs-path ../frontend/docs   # embed the book into Qdrant
uvicorn src.api.main:app --reload
```

`/api/health` reports `healthy` only when **both** Postgres and Qdrant answer, which is what the site uses to decide between the two answer paths. Gemini model names are configuration (`GEMINI_MODEL`, `EMBEDDING_MODEL`), since Google retires models over time.

## Run the site

```bash
cd frontend
npm ci
npm start          # builds the search index, then serves http://localhost:3000/physical-ai-textbook-speckit/
npm test           # retrieval tests against the real book index
npm run build      # fails on any broken link
```

Pushing to `main` runs CI (backend tests, typecheck, lint, retrieval tests, build) and publishes the site to GitHub Pages.

## Status — verified vs not

| | Status |
|---|---|
| 5 modules, 16 chapters, instructor guide | Complete, builds with broken-link checking on |
| In-browser tutor with citations | Live on GitHub Pages; 17 tests on the real index |
| Backend | 31 tests (RAG pipeline, auth, embeddings, ingestion parser, health, rate limiting) with Gemini, Qdrant and Postgres faked. **Not verified against live Gemini/Qdrant/Neon** in this repo's CI |
| Hosted backend | The Hugging Face Space referenced in the site currently reports `degraded`, so the live site answers in browser mode |
| Accounts & synced progress | Need the backend; progress falls back to `localStorage` without it |

## Author

Asadullah Shafique · [portfolio](https://asadullahshafique-devunity.vercel.app) · [GitHub](https://github.com/asadullah48)
