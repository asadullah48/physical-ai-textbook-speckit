# Quickstart: Physical AI Textbook

This guide helps developers set up the Physical AI & Humanoid Robotics Textbook platform for local development.

---

## Prerequisites

- **Node.js**: 20.x or later
- **Python**: 3.11 or later
- **Git**: Latest version
- **Docker** (optional): For containerized development

### External Services (Already Provisioned)

- **Qdrant Cloud**: Vector database (free tier)
- **Neon Postgres**: Serverless database (free tier)
- **Google Gemini API**: API key required

---

## Quick Setup

### 1. Clone and Setup Environment

```bash
# Clone the repository
git clone https://github.com/panaversity/physical-ai-textbook.git
cd physical-ai-textbook

# Create environment files
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
```

### 2. Configure Environment Variables

Edit `backend/.env`:
```bash
# Database (Neon Postgres)
DB_DATABASE_URL=postgresql://user:pass@ep-xxx-pooler.region.neon.tech/dbname?sslmode=require

# Vector Store (Qdrant Cloud)
QDRANT_URL=https://your-cluster.cloud.qdrant.io:6333
QDRANT_API_KEY=your-qdrant-api-key

# AI (Google Gemini)
GOOGLE_API_KEY=your-gemini-api-key

# JWT (generate with: openssl rand -hex 32)
JWT_SECRET_KEY=your-secret-key

# CORS
FRONTEND_URL=http://localhost:3000
```

Edit `frontend/.env`:
```bash
DOCUSAURUS_API_URL=http://localhost:8000
```

### 3. Setup Backend

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Run database migrations
alembic upgrade head

# Seed sample content (optional)
python -m src.scripts.seed_db

# Start development server
uvicorn src.api.main:app --reload --port 8000
```

### 4. Setup Frontend

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run start
```

### 5. Ingest Content

```bash
cd backend

# Index textbook content into Qdrant
python -m src.scripts.ingest_content

# Verify ingestion
python -m src.scripts.verify_ingestion
```

---

## Verify Setup

### Backend Health Check

```bash
curl http://localhost:8000/api/health
```

Expected response:
```json
{
  "status": "healthy",
  "database": true,
  "vector_store": true,
  "timestamp": "2025-12-19T10:00:00Z"
}
```

### Test Chat Endpoint

```bash
curl -X POST http://localhost:8000/api/chat/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What is ROS 2?"}'
```

### Frontend Access

Open http://localhost:3000 in your browser.

---

## Project Structure

```
physical-ai-textbook/
├── backend/                 # FastAPI backend
│   ├── src/
│   │   ├── api/            # API routes and middleware
│   │   ├── models/         # SQLAlchemy models
│   │   ├── services/       # Business logic
│   │   ├── db/             # Database connections
│   │   └── scripts/        # CLI utilities
│   ├── tests/              # Pytest tests
│   ├── alembic/            # Database migrations
│   ├── requirements.txt    # Production dependencies
│   └── .env                # Environment variables
│
├── frontend/               # Docusaurus frontend
│   ├── docs/               # MDX content (textbook)
│   │   ├── module-1-intro/
│   │   ├── module-2-ros2/
│   │   ├── module-3-simulation/
│   │   ├── module-4-isaac/
│   │   └── module-5-vla/
│   ├── src/
│   │   ├── components/     # React components
│   │   ├── hooks/          # Custom hooks
│   │   ├── services/       # API client
│   │   └── theme/          # Theme customization
│   ├── static/             # Static assets
│   └── package.json
│
└── specs/                  # Specification documents
    └── 001-physical-ai-textbook/
```

---

## Common Tasks

### Run Tests

```bash
# Backend tests
cd backend
pytest tests/ -v

# Frontend tests
cd frontend
npm run test
```

### Add a New Chapter

1. Create MDX file in `frontend/docs/module-{n}/`:
   ```bash
   touch frontend/docs/module-2-ros2/05-new-chapter.mdx
   ```

2. Add frontmatter:
   ```yaml
   ---
   title: "New Chapter Title"
   module: 2
   chapter: 5
   learning_objectives:
     - "Objective 1"
   prerequisites:
     - "module-2/chapter-4"
   estimated_reading_time: 20
   difficulty: "intermediate"
   ---
   ```

3. Re-index content:
   ```bash
   cd backend
   python -m src.scripts.ingest_content --chapter module-2/chapter-5
   ```

### Create Database Migration

```bash
cd backend

# Generate migration
alembic revision --autogenerate -m "Add new table"

# Apply migration
alembic upgrade head

# Rollback
alembic downgrade -1
```

### Update API Contract

After changing routes, regenerate the TypeScript client:

```bash
# Generate TypeScript types from OpenAPI
cd frontend
npm run generate-api-types
```

---

## Development Workflow

### Feature Development

1. Create feature branch from `main`
2. Implement backend changes with tests
3. Update OpenAPI spec if API changes
4. Implement frontend changes
5. Run full test suite
6. Create pull request

### Content Development

1. Write MDX content in `frontend/docs/`
2. Add code examples with tests in `static/code/`
3. Run `ingest_content.py` to index
4. Test chatbot responses
5. Verify learning objectives display

---

## Troubleshooting

### Database Connection Issues

```bash
# Check connection string
echo $DB_DATABASE_URL

# Test connection
cd backend
python -c "from src.db.connection import test_connection; test_connection()"
```

### Qdrant Connection Issues

```bash
# Verify Qdrant is reachable
curl -H "api-key: $QDRANT_API_KEY" $QDRANT_URL/collections
```

### Gemini API Issues

```bash
# Test API key
cd backend
python -c "
import google.generativeai as genai
genai.configure(api_key='your-key')
print(genai.list_models())
"
```

### Port Conflicts

```bash
# Backend on different port
uvicorn src.api.main:app --reload --port 8001

# Frontend on different port
npm run start -- --port 3001
```

---

## Next Steps

1. **Read the spec**: `specs/001-physical-ai-textbook/spec.md`
2. **Explore the API**: `specs/001-physical-ai-textbook/contracts/openapi.yaml`
3. **Understand the data model**: `specs/001-physical-ai-textbook/data-model.md`
4. **Check research decisions**: `specs/001-physical-ai-textbook/research.md`

---

## Useful Links

- [Docusaurus Documentation](https://docusaurus.io/docs)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Qdrant Documentation](https://qdrant.tech/documentation/)
- [Neon Documentation](https://neon.tech/docs)
- [Gemini API Documentation](https://ai.google.dev/gemini-api/docs)
