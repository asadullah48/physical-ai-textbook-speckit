"""The RAG pipeline, with the three external boundaries faked:
query embedding (Gemini), vector search (Qdrant) and generation (Gemini)."""

from dataclasses import dataclass

import pytest

from src.services import rag
from src.services.prompts import NO_CONTEXT_RESPONSE
from src.services.qdrant import SearchResult


@dataclass
class FakeGemini:
    answer: str = "A service is a request/response call; an action is long-running with feedback."
    seen: list | None = None

    async def generate_response(self, messages, temperature=None):
        self.seen = messages
        return self.answer, {"input_tokens": 120, "output_tokens": 30}

    async def stream_response(self, messages, temperature=None):
        self.seen = messages
        for part in ["A service ", "is synchronous."]:
            yield part


HIT = SearchResult(
    chunk_id="c1",
    score=0.83,
    text="Services are synchronous request/response calls. Actions handle long-running goals with feedback.",
    module_id="module-2-ros2",
    chapter_id="services-actions-parameters",
    section_title="Choosing the Right Pattern",
)


@pytest.fixture
def fakes(monkeypatch):
    calls = {}
    gemini = FakeGemini()

    def fake_embed(text):
        calls["embedded"] = text
        return [0.1] * 768

    async def fake_search(**kwargs):
        calls["search"] = kwargs
        return calls.get("results", [HIT])

    monkeypatch.setattr(rag, "generate_query_embedding", fake_embed)
    monkeypatch.setattr(rag, "search_similar", fake_search)
    monkeypatch.setattr(rag, "get_gemini_service", lambda: gemini)
    return calls, gemini


async def test_answer_is_grounded_in_retrieved_chunks(fakes):
    calls, gemini = fakes
    result = await rag.generate_rag_response("service vs action?", module_id="module-2-ros2")

    assert calls["embedded"] == "service vs action?"
    assert calls["search"]["module_id"] == "module-2-ros2"
    assert result.answer == gemini.answer
    assert result.sources == [
        {"module_id": "module-2-ros2", "chapter_id": "services-actions-parameters",
         "section": "Choosing the Right Pattern", "score": 0.83}
    ]
    prompt = gemini.seen[-1]["parts"][0]
    assert HIT.text in prompt and "service vs action?" in prompt
    assert (result.input_tokens, result.output_tokens) == (120, 30)


async def test_no_context_means_no_model_call(fakes):
    calls, gemini = fakes
    calls["results"] = []
    result = await rag.generate_rag_response("how do I bake bread?")
    assert result.answer == NO_CONTEXT_RESPONSE
    assert gemini.seen is None  # never asked the model to improvise


async def test_selected_text_is_answered_even_without_hits(fakes):
    calls, gemini = fakes
    calls["results"] = []
    result = await rag.generate_rag_response("explain this", selected_text="zero moment point", chapter_id="x")
    assert result.answer == gemini.answer
    assert "zero moment point" in gemini.seen[-1]["parts"][0]


async def test_retrieval_failure_degrades_to_no_context(monkeypatch):
    def boom(_):
        raise RuntimeError("quota exceeded")

    monkeypatch.setattr(rag, "generate_query_embedding", boom)
    assert await rag.retrieve_context("anything") == []


async def test_stream_sends_sources_first_then_chunks_then_done(fakes):
    events = [e async for e in rag.stream_rag_response("service vs action?")]
    assert events[0]["type"] == "sources" and events[0]["data"][0]["section"] == "Choosing the Right Pattern"
    assert [e["data"] for e in events if e["type"] == "chunk"] == ["A service ", "is synchronous."]
    assert events[-1] == {"type": "done", "data": None}
