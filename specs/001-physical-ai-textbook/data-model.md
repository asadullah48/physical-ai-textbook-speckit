# Data Model: Physical AI & Humanoid Robotics Textbook

**Date**: 2025-12-19
**Branch**: `001-physical-ai-textbook`
**Spec Reference**: [spec.md](./spec.md)

---

## Overview

This document defines the data entities, relationships, and validation rules for the Physical AI textbook platform. The model supports user authentication, progress tracking, chat history, and content indexing.

---

## Entity Relationship Diagram

```
┌─────────────┐       ┌─────────────────┐       ┌───────────────┐
│    User     │──1:N──│  RefreshToken   │       │ ChatSession   │
├─────────────┤       ├─────────────────┤       ├───────────────┤
│ id (UUID)   │       │ id (UUID)       │       │ id (UUID)     │
│ email       │       │ token_hash      │       │ user_id (FK)  │
│ password    │       │ user_id (FK)    │       │ title         │
│ display_name│       │ expires_at      │       │ is_active     │
│ role        │       │ device_info     │       │ message_count │
│ is_active   │       │ is_revoked      │       │ created_at    │
│ created_at  │       └─────────────────┘       └───────┬───────┘
└──────┬──────┘                                         │
       │                                                │
       │ 1:N                                         1:N│
       │                                                │
       ▼                                                ▼
┌───────────────┐                              ┌───────────────┐
│ UserProgress  │                              │ ChatMessage   │
├───────────────┤                              ├───────────────┤
│ id (UUID)     │                              │ id (UUID)     │
│ user_id (FK)  │                              │ session_id(FK)│
│ content_type  │                              │ sequence_num  │
│ content_id    │                              │ role          │
│ status        │                              │ content       │
│ progress_%    │                              │ retrieved_    │
│ reading_time  │                              │   chunks      │
│ scroll_pos    │                              │ selection_ctx │
│ completed_at  │                              │ created_at    │
└───────────────┘                              └───────────────┘

┌─────────────────────────────────────────────────────────────┐
│                    Qdrant Vector Store                       │
├─────────────────────────────────────────────────────────────┤
│ ContentChunk                                                 │
│ ├── id: string                                               │
│ ├── vector: float[768]                                       │
│ └── payload:                                                 │
│     ├── text: string                                         │
│     ├── module_id: string                                    │
│     ├── chapter_id: string                                   │
│     ├── section_title: string                                │
│     ├── content_type: enum                                   │
│     ├── position: int                                        │
│     └── metadata: object                                     │
└─────────────────────────────────────────────────────────────┘
```

---

## Entities

### User

Represents a student or instructor accessing the textbook.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | UUID | PK, auto-generated | Unique identifier |
| `email` | VARCHAR(255) | UNIQUE, NOT NULL | Login email |
| `hashed_password` | VARCHAR(255) | NOT NULL | Bcrypt hash |
| `display_name` | VARCHAR(100) | NULL | Optional display name |
| `role` | VARCHAR(20) | NOT NULL, DEFAULT 'student' | Enum: student, instructor, admin |
| `is_active` | BOOLEAN | NOT NULL, DEFAULT true | Account active status |
| `is_verified` | BOOLEAN | NOT NULL, DEFAULT false | Email verified |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT now() | Account creation |
| `updated_at` | TIMESTAMPTZ | NOT NULL, auto-update | Last modification |
| `last_login_at` | TIMESTAMPTZ | NULL | Last successful login |

**Indexes:**
- `ix_users_email` (UNIQUE) on `email`
- `ix_users_email_active` on `(email, is_active)`

**Validation Rules:**
- Email must be valid format (regex validation)
- Password must be minimum 8 characters before hashing
- Role must be one of: 'student', 'instructor', 'admin'

---

### RefreshToken

Stores hashed refresh tokens for JWT rotation.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | UUID | PK, auto-generated | Unique identifier |
| `token_hash` | VARCHAR(255) | UNIQUE, NOT NULL | SHA-256 hash of token |
| `user_id` | UUID | FK → users.id (CASCADE) | Token owner |
| `device_info` | VARCHAR(255) | NULL | User agent / device |
| `ip_address` | VARCHAR(45) | NULL | Client IP (IPv4/IPv6) |
| `expires_at` | TIMESTAMPTZ | NOT NULL | Expiration timestamp |
| `is_revoked` | BOOLEAN | NOT NULL, DEFAULT false | Revocation status |
| `revoked_at` | TIMESTAMPTZ | NULL | When revoked |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT now() | Token creation |

**Indexes:**
- `ix_refresh_tokens_hash` (UNIQUE) on `token_hash`
- `ix_refresh_tokens_user_active` on `(user_id, is_revoked)`
- `ix_refresh_tokens_expires` on `expires_at`

**Validation Rules:**
- Token hash must be 64 characters (SHA-256)
- expires_at must be future timestamp at creation
- is_revoked and revoked_at must be consistent

---

### UserProgress

Tracks user progress through educational content.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | UUID | PK, auto-generated | Unique identifier |
| `user_id` | UUID | FK → users.id (CASCADE) | Progress owner |
| `content_type` | VARCHAR(20) | NOT NULL | Enum: module, chapter, exercise |
| `content_id` | VARCHAR(100) | NOT NULL | Content path (e.g., "module-1/chapter-2") |
| `status` | VARCHAR(20) | NOT NULL, DEFAULT 'not_started' | Enum: not_started, in_progress, completed |
| `progress_percent` | FLOAT | NOT NULL, DEFAULT 0.0, CHECK 0-100 | Completion percentage |
| `scroll_position` | FLOAT | NULL | Last scroll position (0.0-1.0) |
| `reading_time_seconds` | INTEGER | NOT NULL, DEFAULT 0 | Cumulative reading time |
| `attempts` | INTEGER | NOT NULL, DEFAULT 0 | Exercise attempt count |
| `best_score` | FLOAT | NULL, CHECK 0-100 | Best exercise score |
| `last_answer` | TEXT | NULL | Last submitted answer |
| `started_at` | TIMESTAMPTZ | NULL | First access |
| `completed_at` | TIMESTAMPTZ | NULL | Completion timestamp |
| `last_accessed_at` | TIMESTAMPTZ | NOT NULL, auto-update | Last access |

**Indexes:**
- `uq_user_content` (UNIQUE) on `(user_id, content_id)`
- `ix_progress_user_type` on `(user_id, content_type)`
- `ix_progress_user_recent` on `(user_id, last_accessed_at)`

**Validation Rules:**
- progress_percent must be between 0.0 and 100.0
- scroll_position must be between 0.0 and 1.0 if set
- content_type must be one of: 'module', 'chapter', 'exercise'
- status must be one of: 'not_started', 'in_progress', 'completed'
- completed_at must be NULL if status != 'completed'

**State Transitions:**
```
not_started → in_progress (on first access)
in_progress → completed (when progress_percent = 100)
completed → in_progress (if re-opened, optional)
```

---

### ModuleProgress

Aggregated progress per module (materialized view).

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | UUID | PK, auto-generated | Unique identifier |
| `user_id` | UUID | FK → users.id (CASCADE) | Progress owner |
| `module_id` | VARCHAR(50) | NOT NULL | Module identifier |
| `total_chapters` | INTEGER | NOT NULL | Chapters in module |
| `completed_chapters` | INTEGER | NOT NULL, DEFAULT 0 | Completed count |
| `total_exercises` | INTEGER | NOT NULL | Exercises in module |
| `completed_exercises` | INTEGER | NOT NULL, DEFAULT 0 | Completed count |
| `overall_progress` | FLOAT | NOT NULL, DEFAULT 0.0 | Weighted average |
| `first_accessed_at` | TIMESTAMPTZ | NOT NULL | First module access |
| `last_accessed_at` | TIMESTAMPTZ | NOT NULL | Last activity |
| `completed_at` | TIMESTAMPTZ | NULL | Module completion |

**Indexes:**
- `uq_user_module` (UNIQUE) on `(user_id, module_id)`
- `ix_module_progress_user` on `user_id`

---

### ChatSession

A conversation container for chat interactions.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | UUID | PK, auto-generated | Unique identifier |
| `user_id` | UUID | FK → users.id (SET NULL) | Session owner (NULL for anonymous) |
| `title` | VARCHAR(255) | NULL | Auto-generated from first message |
| `initial_context` | JSONB | NULL | Context: page_url, chapter_id, etc. |
| `is_active` | BOOLEAN | NOT NULL, DEFAULT true | Session active status |
| `message_count` | INTEGER | NOT NULL, DEFAULT 0 | Message counter |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT now() | Session start |
| `updated_at` | TIMESTAMPTZ | NOT NULL, auto-update | Last activity |

**Indexes:**
- `ix_sessions_user_active` on `(user_id, is_active)`
- `ix_sessions_user_updated` on `(user_id, updated_at)`

**initial_context Schema:**
```json
{
  "page_url": "/docs/module-2/chapter-1",
  "chapter_id": "module-2/chapter-1",
  "selected_text": "optional initial selection"
}
```

---

### ChatMessage

Individual messages within a chat session.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | UUID | PK, auto-generated | Unique identifier |
| `session_id` | UUID | FK → chat_sessions.id (CASCADE) | Parent session |
| `sequence_number` | INTEGER | NOT NULL | Order within session |
| `role` | VARCHAR(20) | NOT NULL | Enum: user, assistant, system |
| `content` | TEXT | NOT NULL | Message content |
| `retrieved_chunks` | JSONB | NULL | RAG context for assistant |
| `selection_context` | JSONB | NULL | Selection-based Q&A context |
| `input_tokens` | INTEGER | NULL | Token usage (input) |
| `output_tokens` | INTEGER | NULL | Token usage (output) |
| `feedback_rating` | INTEGER | NULL, CHECK 1-5 | User feedback |
| `feedback_text` | TEXT | NULL | Feedback comments |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT now() | Message timestamp |

**Indexes:**
- `ix_messages_session_seq` on `(session_id, sequence_number)`
- `ix_messages_session_created` on `(session_id, created_at)`

**retrieved_chunks Schema:**
```json
[
  {
    "chunk_id": "mod2-ch1-sec3-p2",
    "score": 0.95,
    "source": "Module 2 / Chapter 1 / Publishing Messages",
    "text": "The publisher node creates..."
  }
]
```

**selection_context Schema:**
```json
{
  "selected_text": "The publisher node creates messages...",
  "chapter_id": "module-2/chapter-1",
  "position": { "start": 1234, "end": 1289 }
}
```

---

### ChatContext (Optional Cache)

Cached sliding window for fast LLM context retrieval.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `session_id` | UUID | PK, FK → chat_sessions.id (CASCADE) | Session reference |
| `context_window` | JSONB | NOT NULL, DEFAULT '[]' | Last N messages |
| `context_tokens` | INTEGER | NOT NULL, DEFAULT 0 | Token count |
| `updated_at` | TIMESTAMPTZ | NOT NULL, auto-update | Last update |

---

### ContentChunk (Qdrant)

Vector-indexed content chunks for RAG retrieval.

| Field | Type | Description |
|-------|------|-------------|
| `id` | STRING | Unique chunk ID (e.g., "mod2-ch1-sec3-p2") |
| `vector` | FLOAT[768] | text-embedding-004 embedding |
| `payload.text` | STRING | Chunk text content |
| `payload.module_id` | STRING | Module identifier (indexed) |
| `payload.chapter_id` | STRING | Chapter identifier (indexed) |
| `payload.section_title` | STRING | Section heading |
| `payload.content_type` | STRING | Enum: explanation, code, exercise, summary (indexed) |
| `payload.position` | INTEGER | Order within chapter |
| `payload.token_count` | INTEGER | Token count |
| `payload.metadata` | OBJECT | Additional metadata (language, prerequisites) |

**Payload Indexes:**
- `module_id` (keyword)
- `chapter_id` (keyword)
- `content_type` (keyword)

---

## Relationships

| Relationship | Cardinality | Description |
|--------------|-------------|-------------|
| User → RefreshToken | 1:N | User has many refresh tokens |
| User → UserProgress | 1:N | User has progress records per content |
| User → ChatSession | 1:N | User has many chat sessions |
| ChatSession → ChatMessage | 1:N | Session contains ordered messages |
| ChatSession → ChatContext | 1:1 | Session has one cached context |

---

## Pydantic Schemas

### User Schemas

```python
from pydantic import BaseModel, EmailStr, Field
from uuid import UUID
from datetime import datetime
from typing import Optional

class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    display_name: Optional[str] = Field(None, max_length=100)

class UserResponse(BaseModel):
    id: UUID
    email: EmailStr
    display_name: Optional[str]
    role: str
    is_active: bool
    created_at: datetime

class UserLogin(BaseModel):
    email: EmailStr
    password: str
```

### Auth Schemas

```python
class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds

class TokenRefresh(BaseModel):
    refresh_token: str
```

### Progress Schemas

```python
class ProgressUpdate(BaseModel):
    content_id: str = Field(..., max_length=100)
    content_type: str = Field(..., pattern="^(module|chapter|exercise)$")
    progress_percent: float = Field(..., ge=0, le=100)
    scroll_position: Optional[float] = Field(None, ge=0, le=1)
    reading_time_delta: int = Field(0, ge=0)

class ProgressResponse(BaseModel):
    id: UUID
    content_id: str
    content_type: str
    status: str
    progress_percent: float
    completed_at: Optional[datetime]

class ProgressSummary(BaseModel):
    user_id: UUID
    modules_started: int
    modules_completed: int
    chapters_completed: int
    exercises_completed: int
    total_reading_time_seconds: int
    last_content_id: Optional[str]
```

### Chat Schemas

```python
class ChatQuery(BaseModel):
    query: str = Field(..., min_length=1, max_length=2000)
    selected_text: Optional[str] = Field(None, max_length=5000)
    module_id: Optional[str] = None
    chapter_id: Optional[str] = None
    session_id: Optional[UUID] = None
    chat_history: Optional[list[dict]] = None

class ChatResponse(BaseModel):
    answer: str
    sources: list[dict]
    session_id: UUID

class ChatSource(BaseModel):
    module_id: str
    chapter_id: str
    section: str
    score: float
```

---

## Database Migrations

### Initial Migration

```sql
-- Create users table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    display_name VARCHAR(100),
    role VARCHAR(20) NOT NULL DEFAULT 'student',
    is_active BOOLEAN NOT NULL DEFAULT true,
    is_verified BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_login_at TIMESTAMPTZ
);

CREATE INDEX ix_users_email ON users(email);
CREATE INDEX ix_users_email_active ON users(email, is_active);

-- Create refresh_tokens table
CREATE TABLE refresh_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    token_hash VARCHAR(255) UNIQUE NOT NULL,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    device_info VARCHAR(255),
    ip_address VARCHAR(45),
    expires_at TIMESTAMPTZ NOT NULL,
    is_revoked BOOLEAN NOT NULL DEFAULT false,
    revoked_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX ix_refresh_tokens_hash ON refresh_tokens(token_hash);
CREATE INDEX ix_refresh_tokens_user_active ON refresh_tokens(user_id, is_revoked);
CREATE INDEX ix_refresh_tokens_expires ON refresh_tokens(expires_at);

-- Create user_progress table
CREATE TABLE user_progress (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    content_type VARCHAR(20) NOT NULL,
    content_id VARCHAR(100) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'not_started',
    progress_percent FLOAT NOT NULL DEFAULT 0.0 CHECK (progress_percent >= 0 AND progress_percent <= 100),
    scroll_position FLOAT CHECK (scroll_position >= 0 AND scroll_position <= 1),
    reading_time_seconds INTEGER NOT NULL DEFAULT 0,
    attempts INTEGER NOT NULL DEFAULT 0,
    best_score FLOAT CHECK (best_score >= 0 AND best_score <= 100),
    last_answer TEXT,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    last_accessed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_user_content UNIQUE (user_id, content_id)
);

CREATE INDEX ix_progress_user_type ON user_progress(user_id, content_type);
CREATE INDEX ix_progress_user_recent ON user_progress(user_id, last_accessed_at);

-- Create chat_sessions table
CREATE TABLE chat_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    title VARCHAR(255),
    initial_context JSONB,
    is_active BOOLEAN NOT NULL DEFAULT true,
    message_count INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX ix_sessions_user_active ON chat_sessions(user_id, is_active);
CREATE INDEX ix_sessions_user_updated ON chat_sessions(user_id, updated_at);

-- Create chat_messages table
CREATE TABLE chat_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE,
    sequence_number INTEGER NOT NULL,
    role VARCHAR(20) NOT NULL,
    content TEXT NOT NULL,
    retrieved_chunks JSONB,
    selection_context JSONB,
    input_tokens INTEGER,
    output_tokens INTEGER,
    feedback_rating INTEGER CHECK (feedback_rating >= 1 AND feedback_rating <= 5),
    feedback_text TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX ix_messages_session_seq ON chat_messages(session_id, sequence_number);
CREATE INDEX ix_messages_session_created ON chat_messages(session_id, created_at);
```

---

## Module Content Specification

Based on FR-007 through FR-011:

| Module | ID | Chapters (min) | Topics |
|--------|-----|----------------|--------|
| 1 | `module-1-intro` | 4 | Physical AI foundations, sensor systems (LiDAR, cameras, IMUs), embodied intelligence, humanoid advantages |
| 2 | `module-2-ros2` | 4 | ROS 2 nodes/topics/services/actions, URDF for humanoids, Python-ROS integration |
| 3 | `module-3-simulation` | 4 | Gazebo physics, Unity rendering, sensor simulation |
| 4 | `module-4-isaac` | 4 | Isaac Sim, Isaac ROS with VSLAM, Nav2 path planning, bipedal locomotion |
| 5 | `module-5-vla` | 4 | Voice-to-action pipelines, LLM cognitive planning, capstone project |

**Content ID Format:**
- Module: `module-{n}`
- Chapter: `module-{n}/chapter-{m}`
- Exercise: `module-{n}/chapter-{m}/exercise-{k}`
