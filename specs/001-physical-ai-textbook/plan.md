# Implementation Plan: Physical AI & Humanoid Robotics Textbook

**Branch**: `001-physical-ai-textbook` | **Date**: 2025-12-19 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-physical-ai-textbook/spec.md`

**Note**: This template is filled in by the `/sp.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Build a comprehensive Physical AI & Humanoid Robotics educational platform using Docusaurus v3 for static content delivery with an embedded RAG chatbot powered by Google Gemini. The system provides 5 modules of educational content, selection-based Q&A, user progress tracking, and an AI assistant for contextual learning support. Backend uses FastAPI with Qdrant for vector search and Neon Postgres for user data persistence.

## Technical Context

### Frontend (Docusaurus v3)
**Framework/Version**: Docusaurus 3.x with React 18, TypeScript
**Build Tool**: Node.js 20+ with npm/yarn
**Deployment**: GitHub Pages (static hosting)
**Key Features**:
- MDX support for interactive React components in markdown
- Custom theme with embedded chatbot widget component
- Text Selection API integration for selection-based Q&A
- Progress tracking UI components with localStorage + API sync
- Responsive design for mobile/desktop browsers

### Backend (FastAPI)
**Language/Version**: Python 3.11+
**Framework**: FastAPI with Pydantic v2 for validation
**ASGI Server**: Uvicorn with auto-reload for development
**Key Dependencies**:
- `fastapi` - Web framework
- `google-generativeai` - Gemini SDK for chat and embeddings
- `qdrant-client` - Vector database client
- `asyncpg` - Async PostgreSQL driver
- `alembic` - Database migrations
- `python-jose` - JWT authentication
- `bcrypt` - Password hashing

### AI/LLM Stack (Google Gemini)
**SDK**: `google-generativeai` Python SDK
**Chat Model**: Gemini Pro (gemini-1.5-pro or gemini-pro)
**Embedding Model**: text-embedding-004
**RAG Pipeline**: Retrieved context injection with prompt templating
**API Key**: Environment variable (already configured)

### Vector Database (Qdrant Cloud)
**Service**: Qdrant Cloud free tier (already provisioned)
**Collection Strategy**: One collection per module for organized retrieval
**Vector Dimensions**: 768 (text-embedding-004 output)
**Distance Metric**: Cosine similarity

### SQL Database (Neon Postgres)
**Service**: Neon serverless Postgres (already provisioned)
**Driver**: asyncpg for async operations
**Migrations**: Alembic with async support
**Schema**: Users, progress, chat_history, sessions

### Testing
**Backend**: pytest with pytest-asyncio, httpx for API testing
**Frontend**: Jest + React Testing Library
**E2E**: Playwright for cross-browser testing
**Coverage Target**: 80% for core library code (per constitution)

### Platform & Deployment
**Target Platform**: Web (desktop and mobile browsers)
**Project Type**: Web application (frontend + backend)
**Frontend Deployment**: GitHub Pages (static)
**Backend Deployment**: Cloud provider (Railway, Render, or similar)

### Performance Goals
- Page load time: <3 seconds on standard broadband (SC-009)
- Chatbot response time: <5 seconds for standard queries (SC-006)
- Static content availability: 99% uptime (SC-013)
- Chatbot service availability: 95% during course hours (SC-014)

### Constraints
- Latency: <200ms p95 for API responses (excluding LLM streaming)
- Memory: <512MB backend container
- Rate limits: Respect Gemini API quotas
- Budget: Free tier services (Qdrant Cloud, Neon Postgres, GitHub Pages)

### Scale/Scope
- Users: ~500 students per semester (Panaversity course)
- Content: 5 modules, ~20+ chapters, ~100 exercises
- Vector storage: ~10,000 content chunks
- Concurrent users: ~50 peak during class hours

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### I. Accuracy & Scientific Rigor (NON-NEGOTIABLE) ✅
- **Gate**: All technical claims in textbook content verified against authoritative sources
- **Plan Alignment**: Content will reference official ROS 2, NVIDIA Isaac, and Gazebo documentation
- **Verification**: Code examples will be tested in documented environments before publication
- **Status**: PASS - Implementation includes test-driven content validation

### II. Practical Implementation Focus ✅
- **Gate**: Every theoretical concept accompanied by working code examples
- **Plan Alignment**: Each chapter includes executable code with syntax highlighting and copy functionality
- **FR Alignment**: FR-003 (code rendering), FR-004 (copy button, downloadable source)
- **Status**: PASS - Docusaurus MDX supports embedded runnable examples

### III. Clear Documentation & Progressive Learning ✅
- **Gate**: Content progresses logically with explicit prerequisites
- **Plan Alignment**: 5-module structure with FR-006 prerequisite tracking
- **FR Alignment**: FR-002 (learning objectives), FR-006 (prerequisites per chapter)
- **Status**: PASS - Module structure supports progressive learning path

### IV. Test-Driven Examples (NON-NEGOTIABLE) ✅
- **Gate**: All code examples include corresponding tests
- **Plan Alignment**: Backend uses pytest; frontend uses Jest; 80% coverage target
- **SC Alignment**: SC-003 (100% code examples have working tests)
- **Status**: PASS - Testing infrastructure planned for both stacks

### V. Safety & Ethics ✅
- **Gate**: Robotic systems include safety considerations
- **Plan Alignment**: Module 5 covers ethical implications of physical AI
- **Content Scope**: Safety considerations documented per chapter where applicable
- **Status**: PASS - Ethics explicitly in curriculum (FR-011)

### VI. Reproducibility & Version Control ✅
- **Gate**: Environments documented with exact versions, dependencies pinned
- **Plan Alignment**:
  - Backend: Python 3.11+, pinned requirements.txt
  - Frontend: Node 20+, package-lock.json
  - Docker containers for reproducible dev environments
- **Status**: PASS - Version specifications included in technical context

### Technical Standards Compliance
- **Code Quality**: PEP 8 for Python, ESLint/Prettier for TypeScript
- **Testing**: pytest + Jest + Playwright stack meets requirements
- **Performance**: Documented goals align with SC-006, SC-009

### Educational Standards Compliance
- **Pedagogical Approach**: Learning objectives (FR-002), exercises (FR-005)
- **Accessibility**: Mobile-responsive design (FR-024, SC-008)
- **Content Structure**: Modular chapters with prerequisites (FR-006)

## Project Structure

### Documentation (this feature)

```text
specs/001-physical-ai-textbook/
├── plan.md              # This file (/sp.plan command output)
├── research.md          # Phase 0 output (/sp.plan command)
├── data-model.md        # Phase 1 output (/sp.plan command)
├── quickstart.md        # Phase 1 output (/sp.plan command)
├── contracts/           # Phase 1 output (/sp.plan command)
│   ├── openapi.yaml     # REST API specification
│   └── schemas/         # Pydantic/TypeScript shared schemas
└── tasks.md             # Phase 2 output (/sp.tasks command - NOT created by /sp.plan)
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── api/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI app entry point
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py          # Authentication endpoints
│   │   │   ├── chat.py          # Chatbot API endpoints
│   │   │   ├── progress.py      # Progress tracking endpoints
│   │   │   └── health.py        # Health check endpoint
│   │   └── middleware/
│   │       ├── __init__.py
│   │       └── cors.py          # CORS configuration
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py              # User model (SQLAlchemy)
│   │   ├── progress.py          # Progress model
│   │   ├── chat.py              # Chat/conversation models
│   │   └── schemas.py           # Pydantic schemas
│   ├── services/
│   │   ├── __init__.py
│   │   ├── auth.py              # JWT authentication service
│   │   ├── gemini.py            # Gemini API wrapper
│   │   ├── rag.py               # RAG pipeline implementation
│   │   ├── embeddings.py        # Embedding generation service
│   │   └── qdrant.py            # Qdrant vector search service
│   ├── db/
│   │   ├── __init__.py
│   │   ├── connection.py        # AsyncPG connection pool
│   │   └── migrations/          # Alembic migrations
│   └── scripts/
│       ├── ingest_content.py    # Content ingestion pipeline
│       └── seed_db.py           # Database seeding
├── tests/
│   ├── conftest.py              # Pytest fixtures
│   ├── unit/
│   │   ├── test_gemini.py
│   │   ├── test_rag.py
│   │   └── test_embeddings.py
│   ├── integration/
│   │   ├── test_api_auth.py
│   │   ├── test_api_chat.py
│   │   └── test_api_progress.py
│   └── contract/
│       └── test_openapi.py      # Contract validation
├── requirements.txt             # Pinned dependencies
├── requirements-dev.txt         # Dev dependencies
├── pyproject.toml               # Project config
├── alembic.ini                  # Migration config
└── Dockerfile                   # Container definition

frontend/
├── docusaurus.config.ts         # Docusaurus configuration
├── sidebars.ts                  # Sidebar navigation
├── src/
│   ├── components/
│   │   ├── ChatWidget/
│   │   │   ├── index.tsx        # Main chatbot widget
│   │   │   ├── ChatMessage.tsx  # Message component
│   │   │   ├── ChatInput.tsx    # Input component
│   │   │   └── styles.module.css
│   │   ├── SelectionPopover/
│   │   │   ├── index.tsx        # Selection-based Q&A trigger
│   │   │   └── styles.module.css
│   │   ├── ProgressTracker/
│   │   │   ├── index.tsx        # Progress display component
│   │   │   └── ModuleProgress.tsx
│   │   └── CodeBlock/
│   │       └── CopyButton.tsx   # Enhanced copy functionality
│   ├── pages/
│   │   ├── index.tsx            # Homepage
│   │   └── dashboard.tsx        # User progress dashboard
│   ├── theme/
│   │   └── Root.tsx             # Custom theme wrapper
│   ├── services/
│   │   ├── api.ts               # API client
│   │   ├── auth.ts              # Auth service
│   │   └── progress.ts          # Progress sync service
│   └── hooks/
│       ├── useChat.ts           # Chatbot hook
│       ├── useSelection.ts      # Text selection hook
│       └── useProgress.ts       # Progress tracking hook
├── docs/                        # Textbook content (MDX files)
│   ├── module-1-intro/
│   │   ├── _category_.json
│   │   ├── 01-what-is-physical-ai.mdx
│   │   ├── 02-sensor-systems.mdx
│   │   ├── 03-embodied-intelligence.mdx
│   │   └── 04-humanoid-advantages.mdx
│   ├── module-2-ros2/
│   ├── module-3-simulation/
│   ├── module-4-isaac/
│   └── module-5-vla-systems/
├── static/
│   ├── img/                     # Diagrams and images
│   └── code/                    # Downloadable code examples
├── tests/
│   ├── components/
│   │   └── ChatWidget.test.tsx
│   └── e2e/
│       └── chat-flow.spec.ts    # Playwright tests
├── package.json
├── tsconfig.json
└── jest.config.js

scripts/
├── ingest-content.sh            # Content ingestion runner
├── setup-dev.sh                 # Development environment setup
└── deploy.sh                    # Deployment automation
```

**Structure Decision**: Web application structure selected with separate `frontend/` (Docusaurus) and `backend/` (FastAPI) directories. This separation enables:
- Independent deployment (static frontend to GitHub Pages, backend to cloud provider)
- Clear API boundary between React frontend and Python backend
- Distinct testing strategies per stack
- Content (MDX) lives in `frontend/docs/` following Docusaurus conventions

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | All constitution gates pass | N/A |

**Note**: No constitution violations identified. The architecture aligns with all six core principles.
