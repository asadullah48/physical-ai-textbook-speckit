---
id: 0008
title: Complete book and browser tutor
stage: green
date: 2026-09-30
surface: agent
model: claude-opus-5-5
feature: 001-physical-ai-textbook
branch: feat/complete-book-and-tutor
user: asadullah48
command: none
labels: ["content", "rag", "testing", "ci", "deployment"]
links:
  spec: specs/001-physical-ai-textbook/spec.md
  ticket: null
  adr: null
  pr: null
files:
 - frontend/docs/module-2-ros2/*.mdx
 - frontend/docs/module-3-simulation/*.mdx
 - frontend/docs/module-4-isaac/*.mdx
 - frontend/docs/module-5-vla/*.mdx
 - frontend/sidebars.ts
 - frontend/scripts/build-search-index.mjs
 - frontend/src/lib/bookAssistant.ts
 - frontend/src/context/ChatContext.tsx
 - frontend/src/hooks/useChat.ts
 - frontend/src/components/ChatWidget/*
 - frontend/tests/*
 - backend/src/services/embeddings.py
 - backend/src/services/gemini.py
 - backend/src/services/auth.py
 - backend/src/api/routes/health.py
 - backend/src/api/config.py
 - backend/src/scripts/ingest/*
 - backend/tests/*
 - .github/workflows/ci.yml
 - README.md
tests:
 - frontend: jest tests/bookAssistant.test.ts (17)
 - backend: pytest tests/ (31)
---

## Prompt

RAG Textbook Platform
AI-powered textbook chatbot with RAG architecture

Comprehensive textbook platform with RAG chatbot built during Panaversity Hackathon (H1) using specification-first development and Spec-Kit Plus methodology.
enhance/polish this project, find in my GitHub:asadullah48, if no such repo create it as it reflect in my portfolio

check this one : https://github.com/asadullah48/physical-ai-textbook-speckit

check this as well: https://github.com/asadullah48/physical-ai-textbook

## Response snapshot

Chose physical-ai-textbook-speckit as the canonical project (physical-ai-textbook is an earlier Next.js prototype). Wrote 12 chapters completing modules 2-5 against the instructor guide. Added a build-time section index and an in-browser BM25 tutor that answers extractively with section citations, used whenever the backend is not healthy. Repaired the backend: missing embedding functions (ImportError), passlib crash with bcrypt 5, health check ignoring the vector store, chapter ids not matching Docusaurus routes, and migrated from the unsupported google-generativeai SDK to google-genai. Added tests and CI that deploys GitHub Pages.

## Outcome

- ✅ Impact: book complete (5 modules, 16 chapters); tutor works with no server; backend imports and passes tests
- 🧪 Tests: 17 frontend (real index), 31 backend (external services faked)
- 📁 Files: see list above
- 🔁 Next prompts: deploy backend with fresh Gemini/Qdrant credentials and run ingestion; verify live Gemini path
- 🧠 Reflection: the portfolio claimed a working RAG chatbot while the committed backend could not import; a zero-cost path makes the claim true regardless of hosting

## Evaluation notes (flywheel)

- Failure modes observed: agent-written chapters needed MDX-safety rules (bare `<` and braces) to build first time
- Graders run and results (PASS/FAIL): docusaurus build with onBrokenLinks=throw PASS; jest PASS; pytest PASS
- Prompt variant (if applicable): none
- Next experiment (smallest change to try): add hybrid scoring (BM25 + backend embeddings) when the backend is healthy
