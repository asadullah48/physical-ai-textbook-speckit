---
id: "0001"
title: physical-ai-textbook-impl-plan
stage: plan
date: 2025-12-19
surface: cli
model: claude-opus-4-5-20251101
feature: 001-physical-ai-textbook
branch: 001-physical-ai-textbook
user: developer
command: /sp.plan
labels: [planning, architecture, rag, docusaurus, fastapi, gemini]
links:
  spec: specs/001-physical-ai-textbook/spec.md
  ticket: N/A
  adr: N/A
  pr: N/A
files:
  - specs/001-physical-ai-textbook/plan.md
  - specs/001-physical-ai-textbook/research.md
  - specs/001-physical-ai-textbook/data-model.md
  - specs/001-physical-ai-textbook/quickstart.md
  - specs/001-physical-ai-textbook/contracts/openapi.yaml
  - CLAUDE.md
tests:
  - N/A (planning phase, no code generated)
---

## Prompt

Create a technical implementation plan for the Physical AI textbook using the following architecture:

**Frontend - Docusaurus v3:**
- Static site generator for educational content
- React-based with MDX support for interactive components
- Custom theme with embedded chatbot widget
- Text selection API for selection-based Q&A
- Progress tracking UI components
- Deploy to GitHub Pages

**Backend - FastAPI (Python 3.11+):**
- RESTful API for chatbot interactions
- RAG (Retrieval-Augmented Generation) implementation
- User authentication and progress tracking
- Vector search integration
- CORS configured for Docusaurus frontend

**AI/LLM - Google Gemini (NOT OpenAI):**
- Use google-generativeai Python SDK
- Gemini Pro for chat completions
- Embedding model: text-embedding-004
- RAG pipeline with retrieved context injection
- API Key: Already configured in environment

**Vector Database - Qdrant Cloud:**
- Free tier cluster (already provisioned)
- Store textbook content embeddings
- Semantic search for relevant chunks
- Collection per module for organized retrieval

**SQL Database - Neon Postgres:**
- Serverless Postgres (already provisioned)
- Store user accounts, progress, chat history
- AsyncPG for async database operations
- Alembic for migrations

**Key Technical Requirements:**
1. Content ingestion pipeline to embed textbook into Qdrant
2. Text selection handler that captures context
3. RAG retrieval with Gemini (not OpenAI)
4. Real-time chat API with streaming responses
5. Progress persistence in Neon Postgres
6. Responsive chatbot widget in Docusaurus

## Response snapshot

Generated comprehensive implementation plan with:

1. **plan.md** - Complete technical context with:
   - Frontend stack (Docusaurus 3.x, React 18, TypeScript)
   - Backend stack (FastAPI, Python 3.11+, asyncpg)
   - AI/LLM stack (Gemini 1.5 Flash, text-embedding-004)
   - All 6 constitution gates passed

2. **research.md** - Consolidated research on:
   - Docusaurus chatbot integration (Root component pattern)
   - Gemini RAG implementation (SDK patterns, streaming)
   - Qdrant vector search (single collection with filters)
   - Neon Postgres async patterns (pooler endpoint)
   - Content chunking strategy (400-600 tokens, 15% overlap)

3. **data-model.md** - Complete schema design:
   - 6 PostgreSQL tables (users, tokens, progress, sessions, messages, context)
   - Qdrant collection schema for content chunks
   - Pydantic validation schemas
   - SQL migration scripts

4. **contracts/openapi.yaml** - Full API specification:
   - 15 endpoints across auth, chat, progress
   - Request/response schemas
   - JWT authentication
   - SSE streaming for chat

5. **quickstart.md** - Developer setup guide:
   - Prerequisites and environment setup
   - Step-by-step installation
   - Verification commands
   - Common tasks and troubleshooting

## Outcome

- ✅ Impact: Complete Phase 0-1 planning artifacts generated
- 🧪 Tests: N/A (planning phase)
- 📁 Files: 6 files created/modified
- 🔁 Next prompts: /sp.tasks to generate implementation tasks
- 🧠 Reflection: Research agents parallelized effectively, all 5 technology areas covered comprehensively

## Evaluation notes (flywheel)

- Failure modes observed: None - all research resolved
- Graders run and results (PASS/FAIL): N/A
- Prompt variant (if applicable): Standard /sp.plan
- Next experiment: Run /sp.tasks to validate task breakdown
