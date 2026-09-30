"""Auth, embeddings, ingestion parser, rate limiter and health endpoint."""

from datetime import timedelta
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

import pytest

from src.api.config import get_settings
from src.api.middleware.rate_limit import SlidingWindowCounter
from src.api.routes import health
from src.scripts.ingest.mdx_parser import MDXParser
from src.services import auth, embeddings

DOCS = Path(__file__).resolve().parents[2] / "frontend" / "docs"


# --- auth ------------------------------------------------------------------------------

def test_password_hash_roundtrip_and_rejection():
    hashed = auth.hash_password("correct horse battery")
    assert hashed.startswith("$2")
    assert auth.verify_password("correct horse battery", hashed)
    assert not auth.verify_password("wrong", hashed)
    assert not auth.verify_password("x", "not-a-bcrypt-hash")


def test_passwords_longer_than_72_bytes_do_not_crash():
    long = "p" * 200
    assert auth.verify_password(long, auth.hash_password(long))


def test_access_and_refresh_tokens_are_not_interchangeable():
    settings = get_settings()
    pair = auth.create_token_pair(uuid4(), settings)
    assert auth.verify_access_token(pair.access_token, settings) is not None
    assert auth.verify_refresh_token(pair.refresh_token, settings) is not None
    assert auth.verify_access_token(pair.refresh_token, settings) is None
    assert auth.verify_refresh_token(pair.access_token, settings) is None


def test_expired_and_tampered_tokens_are_rejected():
    settings = get_settings()
    expired = auth.create_access_token(uuid4(), settings, expires_delta=timedelta(seconds=-5))
    assert auth.verify_access_token(expired, settings) is None
    good = auth.create_access_token(uuid4(), settings)
    assert auth.verify_access_token(good[:-2] + ("A" if good[-2] != "A" else "B") + good[-1], settings) is None


# --- embeddings ------------------------------------------------------------------------

def test_query_and_document_embeddings_use_the_right_task_and_model(monkeypatch):
    calls = []

    class FakeModels:
        def embed_content(self, *, model, contents, config):
            calls.append({"model": model, "contents": contents, "config": config})
            return SimpleNamespace(embeddings=[SimpleNamespace(values=[0.5] * config.output_dimensionality)])

    monkeypatch.setattr(embeddings, "get_genai_client", lambda *a: SimpleNamespace(models=FakeModels()))

    assert len(embeddings.generate_query_embedding("what is urdf?")) == get_settings().embedding_dimension
    embeddings.generate_document_embedding("URDF describes links.", title="URDF")
    q, d = calls
    assert q["config"].task_type == "RETRIEVAL_QUERY" and q["config"].title is None
    assert d["config"].task_type == "RETRIEVAL_DOCUMENT" and d["config"].title == "URDF"
    assert q["model"] == d["model"] == get_settings().embedding_model


async def test_gemini_chat_splits_history_from_the_new_turn(monkeypatch):
    from src.services import gemini

    seen = {}

    class FakeChat:
        async def send_message(self, parts):
            seen["parts"] = parts
            usage = SimpleNamespace(prompt_token_count=11, candidates_token_count=7)
            return SimpleNamespace(text="Grounded answer.", usage_metadata=usage)

    class FakeChats:
        def create(self, *, model, config, history):
            seen.update(model=model, history=history, temperature=config.temperature)
            return FakeChat()

    fake_client = SimpleNamespace(aio=SimpleNamespace(chats=FakeChats()))
    monkeypatch.setattr(gemini, "get_genai_client", lambda *a: fake_client)
    service = gemini.GeminiChatService()
    text, usage = await service.generate_response([
        {"role": "user", "parts": ["system rules"]},
        {"role": "model", "parts": ["ok"]},
        {"role": "user", "parts": ["What is a URDF?"]},
    ])
    assert text == "Grounded answer." and usage == {"input_tokens": 11, "output_tokens": 7}
    assert [c.role for c in seen["history"]] == ["user", "model"]
    assert seen["parts"][0].text == "What is a URDF?"
    assert seen["temperature"] == 0.3


# --- ingestion parser ------------------------------------------------------------------

@pytest.mark.parametrize("path", sorted(DOCS.glob("module-*/0*.mdx")), ids=lambda p: f"{p.parent.name}/{p.name}")
def test_every_chapter_parses_into_chunks_with_docusaurus_ids(path):
    parsed = MDXParser().parse_file(path)
    assert parsed.title
    assert parsed.module_id == path.parent.name
    assert not parsed.chapter_id[0].isdigit(), "chapter ids must match Docusaurus routes (no 01- prefix)"
    assert parsed.chunks and all(c.text.strip() for c in parsed.chunks)
    assert parsed.learning_objectives


def test_the_book_has_chapters_in_every_module():
    modules = {p.parent.name for p in DOCS.glob("module-*/0*.mdx")}
    assert modules == {"module-1-intro", "module-2-ros2", "module-3-simulation", "module-4-isaac", "module-5-vla"}


# --- rate limiting ---------------------------------------------------------------------

def test_sliding_window_blocks_after_the_limit_per_client():
    limiter = SlidingWindowCounter()
    results = [limiter.is_allowed("ip-1", 60, 3)[0] for _ in range(4)]
    assert results == [True, True, True, False]
    assert limiter.is_allowed("ip-2", 60, 3)[0] is True


# --- health ----------------------------------------------------------------------------

async def _up():
    return True


async def _down():
    return False


async def test_health_is_healthy_only_when_database_and_vector_store_are_up(client, monkeypatch):
    monkeypatch.setattr(health, "check_database_connection", _up)
    monkeypatch.setattr(health, "check_qdrant_connection", _up)
    body = (await client.get("/api/health")).json()
    assert body["status"] == "healthy" and body["vector_store"] is True

    monkeypatch.setattr(health, "check_qdrant_connection", _down)
    body = (await client.get("/api/health")).json()
    assert body["status"] == "degraded" and body["database"] is True and body["vector_store"] is False


async def test_ping(client):
    assert (await client.get("/api/health/ping")).json() == {"ping": "pong"}
