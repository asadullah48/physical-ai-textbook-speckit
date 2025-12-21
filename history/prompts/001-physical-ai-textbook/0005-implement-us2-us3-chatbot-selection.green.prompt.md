---
id: "0005"
title: implement-us2-us3-chatbot-selection
stage: green
date: 2025-12-21
surface: cli
model: claude-opus-4-5
feature: 001-physical-ai-textbook
branch: 001-physical-ai-textbook
user: developer
command: /sp.implement
labels: [implementation, chatbot, rag, selection-qa, exercises]
links:
  spec: specs/001-physical-ai-textbook/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - backend/src/services/rag.py
  - backend/src/services/gemini.py
  - backend/src/services/prompts.py
  - backend/src/models/chat.py
  - backend/src/models/schemas.py
  - backend/src/api/routes/chat.py
  - backend/alembic/versions/20241219_0002_chat_sessions_and_messages.py
  - frontend/src/components/ChatWidget/index.tsx
  - frontend/src/components/ChatWidget/ChatMessage.tsx
  - frontend/src/components/ChatWidget/ChatInput.tsx
  - frontend/src/components/ChatWidget/styles.module.css
  - frontend/src/components/SelectionPopover/index.tsx
  - frontend/src/components/SelectionPopover/styles.module.css
  - frontend/src/components/Exercise/index.tsx
  - frontend/src/components/Exercise/DifficultyBadge.tsx
  - frontend/src/hooks/useChat.ts
  - frontend/src/hooks/useSelection.ts
  - frontend/src/context/ChatContext.tsx
  - frontend/src/theme/Root.tsx
tests:
  - null
---

## Prompt

/sp.implement - Execute implementation plan for Physical AI Textbook, continuing from Phase 4 (User Story 2 - Chatbot) onwards.

## Response snapshot

Implemented Phase 4, 5, and partial Phase 6:

**Phase 4 - User Story 2 (RAG Chatbot):**
- Created RAG pipeline (`rag.py`) with context injection and streaming support
- Implemented Gemini API wrapper (`gemini.py`) with streaming responses
- Built prompt templates for educational Q&A (`prompts.py`)
- Created ChatSession and ChatMessage SQLAlchemy models
- Added Alembic migration for chat tables
- Implemented all chat API endpoints (/query, /query/stream, /sessions, /feedback)
- Built ChatWidget frontend component with floating button UI
- Created ChatMessage and ChatInput sub-components
- Implemented SSE streaming hook for real-time responses

**Phase 5 - User Story 3 (Selection-Based Q&A):**
- Created useTextSelection hook for detecting text selection
- Built SelectionPopover component with "Ask AI" button
- Integrated selection context with ChatContext provider
- Updated Root.tsx to include SelectionPopover

**Phase 6 - User Story 4 (Exercises) - Partial:**
- Created Exercise component with structured display
- Built DifficultyBadge component (beginner/intermediate/advanced)
- Updated first chapter with Exercise component examples

## Outcome

- Impact: Major - Completed core interactive learning features (chatbot + selection Q&A)
- Tests: Not executed (infrastructure only)
- Files: 19 files created/modified
- Next prompts: Continue with T073-T074 (exercise tracking), Phase 7-10
- Reflection: Backend RAG pipeline and frontend chatbot UI work together; selection-based Q&A provides contextual help

## Evaluation notes (flywheel)

- Failure modes observed: None
- Graders run and results (PASS/FAIL): Not applicable
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): Add streaming UI updates for real-time response display
