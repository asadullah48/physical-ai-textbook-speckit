# Tasks: Physical AI & Humanoid Robotics Textbook

**Input**: Design documents from `/specs/001-physical-ai-textbook/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/openapi.yaml

**Tests**: Tests are NOT explicitly requested in the specification. Test tasks are included only for constitution-mandated code example validation (SC-003).

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `backend/` (FastAPI Python) and `frontend/` (Docusaurus TypeScript)
- Paths follow plan.md structure

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure for both backend and frontend

- [x] T001 Create project directory structure per plan.md (backend/, frontend/, scripts/)
- [x] T002 [P] Initialize Python backend with pyproject.toml and requirements.txt in backend/
- [x] T003 [P] Initialize Docusaurus frontend with npm in frontend/
- [x] T004 [P] Configure Python linting (ruff) and formatting (black) in backend/pyproject.toml
- [x] T005 [P] Configure TypeScript linting (ESLint) and formatting (Prettier) in frontend/
- [x] T006 [P] Create backend/.env.example with all required environment variables
- [x] T007 [P] Create frontend/.env.example with DOCUSAURUS_API_URL
- [x] T008 [P] Create backend/Dockerfile for containerized development
- [x] T009 Create scripts/setup-dev.sh for one-command development setup

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**CRITICAL**: No user story work can begin until this phase is complete

### Backend Foundation

- [x] T010 Create FastAPI application entry point in backend/src/api/main.py
- [x] T011 [P] Configure CORS middleware in backend/src/api/middleware/cors.py
- [x] T012 [P] Create Pydantic settings model in backend/src/api/config.py
- [x] T013 Setup asyncpg connection pool in backend/src/db/connection.py
- [x] T014 Configure Alembic for async migrations in backend/alembic.ini and backend/alembic/env.py
- [x] T015 [P] Create User SQLAlchemy model in backend/src/models/user.py
- [x] T016 [P] Create RefreshToken model in backend/src/models/refresh_token.py
- [x] T017 Create initial Alembic migration for users and refresh_tokens tables in backend/alembic/versions/
- [x] T018 Implement JWT authentication service in backend/src/services/auth.py
- [x] T019 [P] Create auth dependency for route protection in backend/src/api/dependencies.py
- [x] T020 Create health check endpoint in backend/src/api/routes/health.py
- [x] T021 [P] Create Pydantic schemas for User, Token, Error in backend/src/models/schemas.py

### Vector Database Foundation

- [x] T022 Create Qdrant async client wrapper in backend/src/services/qdrant.py
- [x] T023 Create embedding generation service using text-embedding-004 in backend/src/services/embeddings.py
- [x] T024 Implement ContentChunk dataclass and collection setup in backend/src/services/qdrant.py

### Frontend Foundation

- [x] T025 Create Docusaurus configuration in frontend/docusaurus.config.ts
- [x] T026 [P] Setup custom theme wrapper in frontend/src/theme/Root.tsx
- [x] T027 [P] Create ChatContext provider in frontend/src/context/ChatContext.tsx
- [x] T028 [P] Create API client service in frontend/src/services/api.ts
- [x] T029 [P] Create auth service with token storage in frontend/src/services/auth.ts
- [x] T030 Configure sidebar navigation in frontend/sidebars.ts

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - Student Learning Core Concepts (Priority: P1) MVP

**Goal**: Students can access the textbook, navigate modules, read chapters with code examples, and see learning objectives

**Independent Test**: Navigate to any chapter, read content, view code examples, verify learning objectives are displayed. No backend required except for static content serving.

### Implementation for User Story 1

#### Content Structure (Frontend)

- [x] T031 [P] [US1] Create module category files in frontend/docs/module-1-intro/_category_.json
- [x] T032 [P] [US1] Create module category files in frontend/docs/module-2-ros2/_category_.json
- [x] T033 [P] [US1] Create module category files in frontend/docs/module-3-simulation/_category_.json
- [x] T034 [P] [US1] Create module category files in frontend/docs/module-4-isaac/_category_.json
- [x] T035 [P] [US1] Create module category files in frontend/docs/module-5-vla/_category_.json
- [x] T036 [US1] Create sample chapter MDX with frontmatter in frontend/docs/module-1-intro/01-what-is-physical-ai.mdx
- [x] T037 [P] [US1] Create sample chapter in frontend/docs/module-1-intro/02-sensor-systems.mdx
- [x] T038 [P] [US1] Create sample chapter in frontend/docs/module-1-intro/03-embodied-intelligence.mdx
- [x] T039 [P] [US1] Create sample chapter in frontend/docs/module-1-intro/04-humanoid-advantages.mdx

#### Code Block Enhancement (Frontend)

- [x] T040 [US1] Create enhanced CodeBlock component with copy button in frontend/src/components/CodeBlock/CopyButton.tsx
- [x] T041 [US1] Create downloadable code example directory in frontend/static/code/

#### Progress Display (Frontend - Basic)

- [x] T042 [P] [US1] Create ProgressTracker component placeholder in frontend/src/components/ProgressTracker/index.tsx
- [x] T043 [P] [US1] Create ModuleProgress component in frontend/src/components/ProgressTracker/ModuleProgress.tsx
- [x] T044 [US1] Create useProgress hook with localStorage fallback in frontend/src/hooks/useProgress.ts

#### Homepage and Navigation

- [x] T045 [US1] Create homepage with module overview in frontend/src/pages/index.tsx
- [x] T046 [US1] Add custom CSS for textbook styling in frontend/src/css/custom.css

**Checkpoint**: User Story 1 complete - Students can navigate and read textbook content with code examples

---

## Phase 4: User Story 2 - Interactive Learning with Chatbot (Priority: P2)

**Goal**: Students can ask questions via chatbot widget and receive RAG-powered answers from textbook content

**Independent Test**: Open chatbot on any page, ask a question about textbook content, verify response cites sources accurately

### Backend Implementation for User Story 2

#### RAG Pipeline

- [x] T047 [US2] Implement RAG pipeline with context injection in backend/src/services/rag.py
- [x] T048 [US2] Create Gemini API wrapper for chat in backend/src/services/gemini.py
- [x] T049 [US2] Create prompt templates for educational Q&A in backend/src/services/prompts.py

#### Chat Models and Schemas

- [x] T050 [P] [US2] Create ChatSession model in backend/src/models/chat.py
- [x] T051 [P] [US2] Create ChatMessage model in backend/src/models/chat.py
- [x] T052 [US2] Add Alembic migration for chat_sessions and chat_messages tables in backend/alembic/versions/
- [x] T053 [P] [US2] Create ChatQuery, ChatResponse, ChatSource schemas in backend/src/models/schemas.py

#### Chat API Endpoints

- [x] T054 [US2] Implement /api/chat/query endpoint in backend/src/api/routes/chat.py
- [x] T055 [US2] Implement /api/chat/query/stream SSE endpoint in backend/src/api/routes/chat.py
- [x] T056 [US2] Implement /api/chat/sessions list endpoint in backend/src/api/routes/chat.py
- [x] T057 [US2] Implement /api/chat/sessions/{id} detail endpoint in backend/src/api/routes/chat.py
- [x] T058 [US2] Implement /api/chat/messages/{id}/feedback endpoint in backend/src/api/routes/chat.py

### Frontend Implementation for User Story 2

#### Chatbot Widget

- [x] T059 [US2] Create ChatWidget main component in frontend/src/components/ChatWidget/index.tsx
- [x] T060 [P] [US2] Create ChatMessage component in frontend/src/components/ChatWidget/ChatMessage.tsx
- [x] T061 [P] [US2] Create ChatInput component in frontend/src/components/ChatWidget/ChatInput.tsx
- [x] T062 [P] [US2] Create ChatWidget styles in frontend/src/components/ChatWidget/styles.module.css
- [x] T063 [US2] Create useChat hook for SSE streaming in frontend/src/hooks/useChat.ts
- [x] T064 [US2] Integrate ChatWidget into Root.tsx theme wrapper in frontend/src/theme/Root.tsx

**Checkpoint**: User Story 2 complete - Students can interact with RAG chatbot on any page

---

## Phase 5: User Story 3 - Selection-Based Q&A (Priority: P2)

**Goal**: Students can select/highlight text and ask questions specifically about that selection

**Independent Test**: Select any paragraph, trigger Q&A interface, ask question, verify response addresses selected content

### Frontend Implementation for User Story 3

- [x] T065 [US3] Create useTextSelection hook in frontend/src/hooks/useSelection.ts
- [x] T066 [US3] Create SelectionPopover component in frontend/src/components/SelectionPopover/index.tsx
- [x] T067 [P] [US3] Create SelectionPopover styles in frontend/src/components/SelectionPopover/styles.module.css
- [x] T068 [US3] Integrate SelectionPopover with ChatContext in frontend/src/theme/Root.tsx
- [x] T069 [US3] Update ChatWidget to display selection context in chat in frontend/src/components/ChatWidget/index.tsx

**Checkpoint**: User Story 3 complete - Selection-based Q&A functional alongside regular chatbot

---

## Phase 6: User Story 4 - Completing Exercises (Priority: P3)

**Goal**: Students can access exercises at end of chapters with difficulty levels and attempt them

**Independent Test**: Navigate to any chapter's exercise section, view exercises with difficulty levels, see clear instructions

### Content Implementation for User Story 4

- [x] T070 [P] [US4] Add exercises section to sample chapter in frontend/docs/module-1-intro/01-what-is-physical-ai.mdx
- [x] T071 [P] [US4] Create Exercise component for structured exercise display in frontend/src/components/Exercise/index.tsx
- [x] T072 [P] [US4] Create DifficultyBadge component in frontend/src/components/Exercise/DifficultyBadge.tsx

### Exercise Progress Tracking

- [x] T073 [US4] Add exercise attempts tracking to UserProgress model in backend/src/models/progress.py
- [x] T074 [US4] Add exercises to progress schemas in backend/src/models/schemas.py

**Checkpoint**: User Story 4 complete - Exercise framework in place for content authors

---

## Phase 7: User Story 5 - Instructor Content Review (Priority: P4)

**Goal**: Instructors can review content structure, see learning objectives across modules, and plan course alignment

**Independent Test**: Navigate full content structure, review all learning objectives, verify week assignments are documented

### Implementation for User Story 5

- [x] T075 [US5] Add week assignments to chapter frontmatter schema in frontend/docs/
- [x] T076 [US5] Create instructor overview section in frontend/docs/intro.mdx
- [x] T077 [P] [US5] Document 13-week course breakdown in frontend/docs/instructor-guide/

**Checkpoint**: User Story 5 complete - Instructors can plan course around textbook content

---

## Phase 8: User Story 6 - Student Progress Persistence (Priority: P4)

**Goal**: Returning students can continue from where they left off with persisted progress

**Independent Test**: Create account, read chapters, logout, login again, verify progress preserved and resume works

### Backend Implementation for User Story 6

#### Auth Endpoints

- [x] T078 [US6] Implement /api/auth/register endpoint in backend/src/api/routes/auth.py
- [x] T079 [US6] Implement /api/auth/login endpoint in backend/src/api/routes/auth.py
- [x] T080 [US6] Implement /api/auth/refresh endpoint in backend/src/api/routes/auth.py
- [x] T081 [US6] Implement /api/auth/logout endpoint in backend/src/api/routes/auth.py
- [x] T082 [US6] Implement /api/auth/me endpoint in backend/src/api/routes/auth.py

#### Progress Models and Endpoints

- [x] T083 [US6] Create UserProgress model in backend/src/models/progress.py
- [x] T084 [US6] Add Alembic migration for user_progress table in backend/alembic/versions/
- [x] T085 [P] [US6] Create progress Pydantic schemas in backend/src/models/schemas.py
- [x] T086 [US6] Implement /api/progress GET summary endpoint in backend/src/api/routes/progress.py
- [x] T087 [US6] Implement /api/progress/resume endpoint in backend/src/api/routes/progress.py
- [x] T088 [US6] Implement /api/progress/modules endpoint in backend/src/api/routes/progress.py
- [x] T089 [US6] Implement /api/progress/{content_id} GET/PATCH endpoints in backend/src/api/routes/progress.py

### Frontend Implementation for User Story 6

- [x] T090 [US6] Create dashboard page in frontend/src/pages/dashboard.tsx
- [x] T091 [US6] Update useProgress hook to sync with API in frontend/src/hooks/useProgress.ts
- [x] T092 [US6] Add login/register UI components in frontend/src/components/Auth/
- [x] T093 [US6] Add "Continue where you left off" feature to homepage in frontend/src/pages/index.tsx

**Checkpoint**: User Story 6 complete - Full progress persistence with user accounts

---

## Phase 9: Content Ingestion Pipeline

**Purpose**: Index textbook content into Qdrant for RAG retrieval

- [x] T094 Create content ingestion script in backend/src/scripts/ingest/ingest_content.py
- [x] T095 [P] Create MDX parser for extracting content chunks in backend/src/scripts/ingest/mdx_parser.py
- [ ] T096 [P] Create ingestion verification script in backend/src/scripts/verify_ingestion.py
- [ ] T097 Create database seeding script in backend/src/scripts/seed_db.py
- [ ] T098 Create ingestion shell wrapper in scripts/ingest-content.sh

---

## Phase 10: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [x] T099 [P] Add error handling middleware in backend/src/api/middleware/error_handler.py
- [x] T100 [P] Add request logging middleware in backend/src/api/middleware/logging.py
- [x] T101 [P] Add rate limiting for chat endpoints in backend/src/api/middleware/rate_limit.py
- [ ] T102 Implement token usage tracking for Gemini calls in backend/src/services/gemini.py
- [ ] T103 [P] Add mobile-responsive styles in frontend/src/css/custom.css
- [x] T104 Create deployment configuration (docker-compose.yml, Dockerfiles)
- [ ] T105 Validate quickstart.md instructions work end-to-end
- [ ] T106 Security review: validate JWT implementation, CORS config, input sanitization

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phases 3-8)**: All depend on Foundational phase completion
  - US1 (Phase 3): Can start immediately after Phase 2
  - US2 (Phase 4): Can start after Phase 2 (parallel with US1)
  - US3 (Phase 5): Depends on US2 (chatbot infrastructure)
  - US4 (Phase 6): Can start after Phase 2 (parallel with US1/US2)
  - US5 (Phase 7): Can start after US1 (content structure)
  - US6 (Phase 8): Can start after Phase 2 (parallel with US1/US2)
- **Content Ingestion (Phase 9)**: Depends on US1 (content) and US2 (Qdrant service)
- **Polish (Phase 10)**: Depends on core user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Independent after Phase 2 - MVP content delivery
- **User Story 2 (P2)**: Independent after Phase 2 - Chatbot infrastructure
- **User Story 3 (P2)**: Depends on US2 (uses chatbot infrastructure)
- **User Story 4 (P3)**: Independent after Phase 2 - Exercise framework
- **User Story 5 (P4)**: Light dependency on US1 (content structure exists)
- **User Story 6 (P4)**: Independent after Phase 2 - User accounts and progress

### Within Each User Story

- Models before services
- Services before endpoints
- Backend before frontend (for API-dependent features)
- Core implementation before integration

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- After Phase 2: US1, US2, US4, US6 can all start in parallel
- Within each story, tasks marked [P] can run in parallel

---

## Parallel Example: Foundation Phase

```bash
# Launch all parallel foundation tasks:
Task: "Configure CORS middleware" - backend/src/api/middleware/cors.py
Task: "Create Pydantic settings model" - backend/src/api/config.py
Task: "Create User model" - backend/src/models/user.py
Task: "Create RefreshToken model" - backend/src/models/refresh_token.py
Task: "Setup theme wrapper" - frontend/src/theme/Root.tsx
Task: "Create ChatContext" - frontend/src/context/ChatContext.tsx
Task: "Create API client" - frontend/src/services/api.ts
```

## Parallel Example: User Story 1 Content Creation

```bash
# Launch all module category files in parallel:
Task: "Create module-1-intro/_category_.json"
Task: "Create module-2-ros2/_category_.json"
Task: "Create module-3-simulation/_category_.json"
Task: "Create module-4-isaac/_category_.json"
Task: "Create module-5-vla/_category_.json"

# Then launch chapter content in parallel:
Task: "Create 02-sensor-systems.mdx"
Task: "Create 03-embodied-intelligence.mdx"
Task: "Create 04-humanoid-advantages.mdx"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL)
3. Complete Phase 3: User Story 1 (Core Content)
4. **STOP and VALIDATE**: Test navigation, code examples, learning objectives
5. Deploy static content to GitHub Pages

### Incremental Delivery

1. **MVP**: Setup + Foundational + US1 = Students can read textbook
2. **+Chatbot**: Add US2 + Ingestion = Interactive Q&A
3. **+Selection**: Add US3 = Context-aware help
4. **+Exercises**: Add US4 = Practice problems
5. **+Accounts**: Add US6 = Progress persistence
6. **+Instructor**: Add US5 = Course alignment tools

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (Content) + User Story 5 (Instructor)
   - Developer B: User Story 2 (Chatbot) + User Story 3 (Selection)
   - Developer C: User Story 4 (Exercises) + User Story 6 (Accounts)
3. All integrate for Ingestion Pipeline and Polish

---

## Task Summary

| Phase | User Story | Task Count | Parallel Tasks |
|-------|------------|------------|----------------|
| 1 | Setup | 9 | 6 |
| 2 | Foundational | 21 | 11 |
| 3 | US1 - Core Content | 16 | 9 |
| 4 | US2 - Chatbot | 18 | 6 |
| 5 | US3 - Selection Q&A | 5 | 1 |
| 6 | US4 - Exercises | 5 | 3 |
| 7 | US5 - Instructor | 3 | 1 |
| 8 | US6 - Progress | 16 | 1 |
| 9 | Ingestion | 5 | 2 |
| 10 | Polish | 8 | 4 |
| **Total** | | **106** | **44** |

### MVP Scope (Recommended First Delivery)

- Phase 1: Setup (9 tasks)
- Phase 2: Foundational (21 tasks)
- Phase 3: User Story 1 (16 tasks)
- **MVP Total**: 46 tasks

### Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story is independently testable after completion
- Content ingestion (Phase 9) requires both content (US1) and Qdrant (Phase 2)
- Commit after each task or logical group
