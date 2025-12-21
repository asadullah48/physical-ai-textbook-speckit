# Research: Physical AI & Humanoid Robotics Textbook

**Date**: 2025-12-19
**Branch**: `001-physical-ai-textbook`
**Status**: Complete

---

## Research Summary

This document consolidates research findings for the Physical AI textbook implementation, covering five key technology areas. All research topics have been resolved with clear decisions and implementation patterns.

---

## 1. Docusaurus v3 Chatbot Integration

### Decision
Use the **Root component wrapper pattern** with React Context for persistent chatbot state.

### Rationale
- Root component persists across all SPA navigations
- No swizzle command needed - just create `src/theme/Root.js`
- React Context with localStorage provides session persistence
- Text Selection API works reliably with `mouseup` + `selectionchange` events

### Alternatives Considered
| Alternative | Rejected Because |
|-------------|------------------|
| Client modules | Cannot render React components, only side effects |
| Layout wrapper (swizzle) | Less stable across Docusaurus updates |
| Zustand store | Additional dependency not needed for simple state |

### Implementation Pattern

```tsx
// src/theme/Root.tsx
import React from 'react';
import { ChatProvider } from '@site/src/context/ChatContext';
import ChatbotWidget from '@site/src/components/ChatWidget';

export default function Root({ children }) {
  return (
    <ChatProvider>
      {children}
      <ChatbotWidget />
    </ChatProvider>
  );
}
```

**Text Selection Hook:**
```tsx
// src/hooks/useTextSelection.ts
import { useState, useEffect, useCallback } from 'react';
import ExecutionEnvironment from '@docusaurus/ExecutionEnvironment';

export function useTextSelection() {
  const [selection, setSelection] = useState({ text: '', position: null });

  useEffect(() => {
    if (!ExecutionEnvironment.canUseDOM) return;

    const handleSelection = () => {
      const sel = window.getSelection();
      const text = sel?.toString().trim() || '';
      if (text.length > 0) {
        const range = sel.getRangeAt(0);
        const rect = range.getBoundingClientRect();
        setSelection({ text, position: rect });
      }
    };

    document.addEventListener('mouseup', handleSelection);
    document.addEventListener('selectionchange', handleSelection);
    return () => {
      document.removeEventListener('mouseup', handleSelection);
      document.removeEventListener('selectionchange', handleSelection);
    };
  }, []);

  return selection;
}
```

### Key Considerations
- Always check `ExecutionEnvironment.canUseDOM` for SSR compatibility
- Use Infima CSS variables (`--ifm-*`) for theme consistency
- Import paths: `@site/src/...` for project, `@docusaurus/...` for framework

---

## 2. Google Gemini RAG Implementation

### Decision
Use **google-generativeai SDK** with `gemini-1.5-flash` for chat and `text-embedding-004` for embeddings.

### Rationale
- Gemini 1.5 Flash: Fast, cost-effective, sufficient for educational Q&A
- text-embedding-004: 768 dimensions, supports task types for query vs document
- Native streaming support via SDK
- No need for LangChain - direct SDK is simpler

### Alternatives Considered
| Alternative | Rejected Because |
|-------------|------------------|
| Gemini 1.5 Pro | Higher cost, slower, overkill for simple Q&A |
| Gemini 2.0 Flash | Experimental, behavior may change |
| text-embedding-005 | Not yet available at scale |

### Implementation Pattern

**Embeddings:**
```python
import google.generativeai as genai

def generate_embedding(text: str, task_type: str = "retrieval_document") -> list[float]:
    result = genai.embed_content(
        model="models/text-embedding-004",
        content=text,
        task_type=task_type  # "retrieval_document" or "retrieval_query"
    )
    return result['embedding']  # 768 dimensions
```

**RAG Prompt Template:**
```python
RAG_PROMPT = """You are an AI teaching assistant for a Physical AI & Humanoid Robotics textbook.

INSTRUCTIONS:
1. Answer ONLY based on the provided context
2. Cite sources using [Chapter: Section] format
3. If not in context, say "This topic is not covered"
4. Use clear, educational language for university students

CONTEXT:
{context}

QUESTION: {query}

Answer:"""
```

**Streaming Response:**
```python
async def stream_response(query: str, context: str):
    model = genai.GenerativeModel("gemini-1.5-flash")
    prompt = RAG_PROMPT.format(context=context, query=query)

    response = model.generate_content(prompt, stream=True)
    for chunk in response:
        if chunk.text:
            yield chunk.text
```

### Key Considerations
- Use `task_type="retrieval_query"` for user queries, `retrieval_document"` for content
- Implement retry with exponential backoff for rate limits
- Temperature 0.3 for factual educational responses

---

## 3. Qdrant Vector Database Integration

### Decision
Use **single collection with metadata filtering** rather than separate collections per module.

### Rationale
- Simpler architecture, easier cross-module search
- Efficient filtering with payload indexes
- Qdrant Cloud free tier supports this pattern well
- Use gRPC (`prefer_grpc=True`) for 2-3x faster cloud connections

### Alternatives Considered
| Alternative | Rejected Because |
|-------------|------------------|
| Collection per module | More complex, harder cross-module search |
| Collection per chapter | Too many collections, management overhead |
| Hybrid BM25 + vector | Free tier doesn't support sparse vectors |

### Implementation Pattern

**Collection Setup:**
```python
from qdrant_client import AsyncQdrantClient
from qdrant_client.models import VectorParams, Distance

async def create_collection(client: AsyncQdrantClient):
    await client.create_collection(
        collection_name="textbook_content",
        vectors_config=VectorParams(
            size=768,  # text-embedding-004
            distance=Distance.COSINE
        )
    )

    # Create indexes for filtering
    for field in ["module_id", "chapter_id", "content_type"]:
        await client.create_payload_index(
            collection_name="textbook_content",
            field_name=field,
            field_schema="keyword"
        )
```

**Search with Filtering:**
```python
from qdrant_client.models import Filter, FieldCondition, MatchValue

async def search(query_embedding: list[float], module_id: str = None):
    filter_conditions = []
    if module_id:
        filter_conditions.append(
            FieldCondition(key="module_id", match=MatchValue(value=module_id))
        )

    return await client.search(
        collection_name="textbook_content",
        query_vector=query_embedding,
        query_filter=Filter(must=filter_conditions) if filter_conditions else None,
        limit=5
    )
```

### Key Considerations
- AsyncQdrantClient for FastAPI integration
- Use `prefer_grpc=True` for cloud connections
- HNSW ef=128 for accurate search (configurable)

---

## 4. Neon Postgres with AsyncPG

### Decision
Use **Neon pooler endpoint** with small asyncpg pool (2-5 connections).

### Rationale
- Neon's built-in PgBouncer handles connection pooling at proxy level
- Free tier limits: ~10-20 concurrent connections
- Cold starts can take 5-10s, need generous timeouts
- asyncpg provides true async for FastAPI

### Alternatives Considered
| Alternative | Rejected Because |
|-------------|------------------|
| Direct connections | Exhausts free tier limits quickly |
| SQLAlchemy only | Adds ORM overhead for simple operations |
| Supabase | Already have Neon provisioned |

### Implementation Pattern

**Connection Configuration:**
```python
from pydantic_settings import BaseSettings

class DatabaseSettings(BaseSettings):
    database_url: str  # Use -pooler endpoint
    pool_min_size: int = 2
    pool_max_size: int = 5
    connection_timeout: float = 30.0  # Handle cold starts

# Connection string format:
# postgresql://user:pass@ep-xxx-pooler.region.neon.tech/dbname?sslmode=require
```

**Alembic with Async:**
```python
# alembic/env.py
async def run_async_migrations():
    url = config.get_main_option("sqlalchemy.url")
    url = url.replace("postgresql://", "postgresql+asyncpg://")

    connectable = async_engine_from_config(
        {"sqlalchemy.url": url},
        poolclass=pool.NullPool,
        connect_args={"ssl": "require"}
    )
    # ... run migrations
```

### Key Considerations
- Always use SSL (`ssl="require"`) for Neon
- Use `-pooler` suffix endpoint for connection pooling
- Set `max_inactive_connection_lifetime=300` to handle Neon resets

---

## 5. Content Chunking Strategy

### Decision
Use **semantic chunking with 400-600 tokens** and **15-20% sentence-based overlap**.

### Rationale
- 400-600 tokens fits complete explanatory paragraphs
- Matches text-embedding-004's 2048 token limit well
- Code blocks kept intact with surrounding context
- Hierarchical metadata (module > chapter > section) improves retrieval

### Alternatives Considered
| Alternative | Rejected Because |
|-------------|------------------|
| Fixed character split | Breaks mid-sentence, loses context |
| Large chunks (1000+) | Too much noise in retrieval |
| No overlap | Context loss at boundaries |
| 50% overlap | Excessive storage, redundant retrieval |

### Implementation Pattern

**Chunk Structure:**
```python
@dataclass
class ContentChunk:
    id: str
    text: str
    module_id: str
    chapter_id: str
    section_title: str
    content_type: str  # "explanation", "code", "exercise"
    position: int
    token_count: int
```

**Chunking Configuration by Type:**
| Content Type | Chunk Size | Overlap | Notes |
|--------------|------------|---------|-------|
| Concept explanation | 500 tokens | 15% | Standard prose |
| Code tutorial | 600 tokens | 20% | Keep code with context |
| Exercise | 300 tokens | 10% | Self-contained |
| Learning objectives | 150 tokens | 0% | Complete units |
| Reference | 200 tokens | 5% | Minimal context |

**Code Block Handling:**
- Never split code blocks
- Include 1-2 paragraphs of context before/after
- Dual-index: code with prose AND as standalone snippet

### MDX Frontmatter Schema

```yaml
---
title: "Understanding ROS 2 Nodes"
module: 2
chapter: 1
learning_objectives:
  - "Explain publisher-subscriber pattern"
  - "Create Python ROS 2 node"
prerequisites:
  - "module-1/04-humanoid-advantages"
estimated_reading_time: 25
difficulty: "intermediate"
keywords: ["ROS 2", "nodes", "topics", "publisher"]
content_type: "lesson"
week: 4  # 13-week course alignment
---
```

---

## Database Schema Summary

### User & Auth Tables
- `users`: UUID PK, email, hashed_password, role, timestamps
- `refresh_tokens`: Token hash storage, device info, expiration

### Progress Tables
- `user_progress`: Per-content progress (chapter/exercise)
- `module_progress`: Aggregated module completion
- `reading_sessions`: Analytics for engagement

### Chat Tables
- `chat_sessions`: Conversation containers, context
- `chat_messages`: Individual messages with RAG metadata
- `chat_contexts`: Cached sliding window for LLM calls

### Key Design Decisions
- UUID primary keys for distributed compatibility
- JSONB for flexible metadata (chunks, context)
- Explicit sequence numbers for message ordering
- Cascading deletes for data integrity

---

## API Design Summary

### Core Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/auth/register` | POST | User registration |
| `/api/auth/login` | POST | Get token pair |
| `/api/auth/refresh` | POST | Rotate tokens |
| `/api/chat/query` | POST | RAG Q&A (non-streaming) |
| `/api/chat/query/stream` | POST | RAG Q&A (SSE streaming) |
| `/api/progress/{content_id}` | GET/PATCH | Progress tracking |
| `/api/progress/summary` | GET | User dashboard data |

### Streaming Format
Server-Sent Events (SSE):
```
data: {"type": "sources", "data": [...]}
data: {"type": "chunk", "data": "The answer..."}
data: {"type": "done"}
```

---

## Performance Targets

| Metric | Target | How Achieved |
|--------|--------|--------------|
| Page load | <3s | Static Docusaurus on GitHub Pages |
| Chat response | <5s | Gemini 1.5 Flash + Qdrant |
| API latency | <200ms p95 | AsyncPG + Qdrant gRPC |
| Retrieval accuracy | 90% | Semantic chunking + metadata filters |

---

## Unresolved Items

None. All research questions have been resolved with clear decisions.

---

## References

- [Docusaurus Swizzling](https://docusaurus.io/docs/swizzling)
- [Google Gemini API](https://ai.google.dev/gemini-api/docs)
- [Qdrant Documentation](https://qdrant.tech/documentation/)
- [Neon Connection Pooling](https://neon.tech/docs/connect/connection-pooling)
- [Chunking Best Practices](https://www.pinecone.io/learn/chunking-strategies/)
