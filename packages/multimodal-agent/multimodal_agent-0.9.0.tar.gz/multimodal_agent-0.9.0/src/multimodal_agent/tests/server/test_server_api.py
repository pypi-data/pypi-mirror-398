import io
from types import SimpleNamespace

from fastapi.testclient import TestClient

from multimodal_agent.server.server import agent, app

client = TestClient(app)


def test_ask(monkeypatch):
    """
    Tests the /ask endpoint with mocked agent.ask().
    """

    def fake_ask(
        prompt,
        response_format=None,
        session_id=None,
        rag_enabled=False,
    ):
        return SimpleNamespace(
            text=f"echo: {prompt}",
            data=None,
            usage={
                "prompt_tokens": 1,
                "response_tokens": 1,
                "total_tokens": 2,
            },
        )

    monkeypatch.setattr(agent, "ask", fake_ask)

    payload = {"prompt": "hello world"}
    resp = client.post("/ask", json=payload)
    data = resp.json()

    assert resp.status_code == 200
    assert data["text"] == "echo: hello world"
    assert data["data"] is None
    assert "usage" in data


def test_ask_with_image(monkeypatch):
    """
    Tests /ask_with_image with mocked ask_with_image and a fake image upload.
    """

    def fake_ask_with_image(prompt, image):
        return SimpleNamespace(
            text="image processed",
            data=None,
            usage={
                "prompt_tokens": 1,
                "response_tokens": 2,
                "total_tokens": 3,
            },
        )

    monkeypatch.setattr(agent, "ask_with_image", fake_ask_with_image)

    fake_image = io.BytesIO(b"\xff\xd8\xff\xd9")

    resp = client.post(
        "/ask_with_image",
        files={"file": ("fake.jpg", fake_image, "image/jpeg")},
        data={"prompt": (None, "describe this")},  # <-- FIXED
    )

    assert resp.status_code == 200
    data = resp.json()
    assert data["text"] == "image processed"
    assert "usage" in data


def test_generate_json(monkeypatch):
    """
    Tests /generate endpoint with JSON response_format.
    """

    def fake_ask(prompt, response_format="json"):
        return SimpleNamespace(
            text='{"x": 42}',
            data={"x": 42},
            usage=None,
        )

    monkeypatch.setattr(agent, "ask", fake_ask)

    resp = client.post(
        "/generate",
        json={"prompt": "give json", "json": True},
    )
    data = resp.json()

    assert resp.status_code == 200
    assert data["data"] == {"x": 42}
    assert data["text"] == '{"x": 42}'


def test_generate_raw(monkeypatch):
    """
    Tests /generate endpoint when JSON mode = False.
    """

    def fake_ask(prompt, response_format="text"):
        return SimpleNamespace(
            text="raw output",
            data=None,
            usage=None,
        )

    monkeypatch.setattr(agent, "ask", fake_ask)

    resp = client.post("/generate", json={"prompt": "raw test", "json": False})
    data = resp.json()

    assert resp.status_code == 200
    assert data == {"raw": "raw output"}


def test_memory_search(monkeypatch):
    """
    Tests /memory/search endpoint with mocked rag_store.search_similar().
    """

    agent.enable_rag = True

    class FakeStore:
        def search_similar(self, query_embedding, model, top_k):
            return [
                ("0.99", SimpleNamespace(content="hello")),
                ("0.88", SimpleNamespace(content="world")),
            ]

    monkeypatch.setattr(agent, "rag_store", FakeStore())

    resp = client.post("/memory/search", json={"query": "test", "limit": 5})
    data = resp.json()

    assert resp.status_code == 200
    assert "results" in data
    assert len(data["results"]) == 2


def test_memory_search_disabled(monkeypatch):
    """
    Memory search should return error when rag disabled.
    """

    agent.enable_rag = False
    agent.rag_store = None

    resp = client.post("/memory/search", json={"query": "test", "limit": 5})
    data = resp.json()

    assert data["results"] == []
    assert data["error"] == "RAG disabled"


def test_memory_summary(monkeypatch):
    """
    If agent does not have summarize_history(), endpoint should fallback.
    """
    if hasattr(agent, "summarize_history"):
        monkeypatch.delattr(agent, "summarize_history", raising=False)

    resp = client.post("/memory/summary")
    data = resp.json()

    assert resp.status_code == 200
    assert data["summary"] == "Memory summarization not available."


def test_memory_summary_missing(monkeypatch):
    """
    /memory/summary returns fallback if summarize_history() is missing.
    """

    if hasattr(agent, "summarize_history"):
        monkeypatch.delattr(agent, "summarize_history")

    resp = client.post("/memory/summary")
    data = resp.json()

    assert resp.status_code == 200
    assert data["summary"] == "Memory summarization not available."


def test_chat_endpoint(monkeypatch):
    def fake_ask(
        prompt,
        response_format=None,
        session_id=None,
        rag_enabled=True,
    ):
        return SimpleNamespace(
            text=f"chat echo: {prompt}",
            data={"ok": True},
            usage={"total_tokens": 5},
        )

    monkeypatch.setattr(agent, "ask", fake_ask)

    resp = client.post("/chat", json={"message": "hello"})
    data = resp.json()

    assert resp.status_code == 200
    assert data["text"] == "chat echo: hello"
    assert data["data"] == {"ok": True}
    assert "usage" in data


def test_image_endpoint(monkeypatch):
    def fake_ask_with_image(prompt, image):
        return SimpleNamespace(
            text="image OK",
            data={"detected": "cat"},
            usage={"prompt_tokens": 1},
        )

    monkeypatch.setattr(agent, "ask_with_image", fake_ask_with_image)

    img = io.BytesIO(b"\xff\xd8\xff\xd9")

    resp = client.post(
        "/image",
        files={"file": ("pic.jpg", img, "image/jpeg")},
        data={"prompt": "describe"},
    )

    assert resp.status_code == 200
    data = resp.json()

    assert data["text"] == "image OK"
    assert data["data"] == {"detected": "cat"}


def test_history_endpoint(monkeypatch):
    class FakeChunk:
        id = 1
        role = "user"
        session_id = "s1"
        content = "hello"
        created_at = "2025-12-01"
        source = None

    class FakeStore:
        def get_recent_chunks(self, limit):
            return [FakeChunk()]

    monkeypatch.setattr(agent, "rag_store", FakeStore())

    resp = client.get("/history?limit=10")
    data = resp.json()

    assert resp.status_code == 200
    assert len(data["items"]) == 1
    assert data["items"][0]["content"] == "hello"


def test_history_summary_endpoint(monkeypatch):
    def fake_summary(limit=50, session_id=None):
        return "summary generated"

    monkeypatch.setattr(
        agent,
        "summarize_history",
        fake_summary,
        raising=False,
    )

    resp = client.get("/history/summary?limit=10")
    data = resp.json()

    assert resp.status_code == 200
    assert data["summary"] == "summary generated"
