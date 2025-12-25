import pytest

import multimodal_agent.rag.rag_store as rag_mod
from multimodal_agent.core.agent_core import MultiModalAgent
from multimodal_agent.rag import RAGStore


@pytest.fixture
def mock_client_response():
    """
    Fake Gemini response object with .text attribute.
    """

    class Response:
        def __init__(self, text="mocked response"):
            self.text = text

    return Response()


@pytest.fixture
def mock_agent(mocker, mock_client_response):
    """
    Create a MultiModalAgent with a mocked client so no real API calls happen.
    """
    mock_client = mocker.Mock()
    agent = MultiModalAgent(client=mock_client)

    mocker.patch.object(
        agent.client.models,
        "generate_content",
        return_value=mock_client_response,
    )
    return agent


@pytest.fixture
def fake_part():
    class FakePart:
        data = b"fake-bytes"
        mime_type = "image/jpeg"

    return FakePart()


@pytest.fixture(autouse=True)
def no_real_rag(monkeypatch, request):
    """
    Disable SQLiteRAGStore for tests that are not testing the real DB.
    """
    if "use_real_rag" in getattr(request, "keywords", {}):
        return  # let RAG tests hit real SQLite

    class DummyStore(RAGStore):
        def __init__(self, *a, **k):
            pass

        def add_chunk(self, *a, **k):
            return 1

        def add_embedding(self, *a, **k):
            return None

        def get_recent_chunks(self, *a, **k):
            return []

        def get_recent_chunk(self, *a, **k):
            return []

        def search_similar(self, *a, **k):
            return []

        def delete_chunk(self, *a, **k):
            return None

        def clear_all(self):
            return None

    monkeypatch.setattr(rag_mod, "SQLiteRAGStore", DummyStore)
