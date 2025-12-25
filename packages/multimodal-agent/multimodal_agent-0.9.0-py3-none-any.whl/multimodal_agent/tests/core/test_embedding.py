import pytest

from multimodal_agent.core import embedding as embedding_module


@pytest.fixture
def embedding_client(monkeypatch):
    """
    Provides a dummy embedding client by monkeypatching get_embedding_client()
    to avoid calling real Google genai.Client().
    """

    class DummyClient:
        def embed(self, text):
            # simple predictable fake embedding
            return [float((ord(c) % 10) / 10) for c in text]

    dummy = DummyClient()

    monkeypatch.setattr(
        embedding_module,
        "_embedding_client",
        dummy,
    )
    monkeypatch.setattr(
        embedding_module,
        "get_embedding_client",
        lambda: dummy,
    )
    return dummy


def test_embedding_invalid_model(embedding_client):
    result = embedding_module.embed_text("hello", model="bad-model")
    assert isinstance(result, list)


def test_embedding_empty_text(embedding_client):
    result = embedding_module.embed_text("")
    assert isinstance(result, list)


def test_embedding_list_input(embedding_client):
    vec = embedding_module.embed_text(["a", "b"])
    assert isinstance(vec, list)
    assert all(isinstance(x, float) for x in vec)


def test_embedding_offline_mode(embedding_client):
    vec = embedding_module.embed_text("abc")
    assert vec == [0.7, 0.8, 0.9]  # 'a'=97→7, 'b'=98→8, 'c'=99→9


def test_embedding_api_exception(monkeypatch, embedding_client):
    # Force the dummy's embed to crash
    def boom(text):
        raise RuntimeError("boom")

    monkeypatch.setattr(embedding_client, "embed", boom)

    with pytest.raises(RuntimeError):
        embedding_module.embed_text("abc")


def test_embedding_offline_client_created(monkeypatch):
    """
    Covers the except-branch in get_embedding_client()
    where genai.Client() raises and OfflineEmbeddingClient is created.
    """

    # Force genai.Client() to fail.
    def boom():
        raise RuntimeError("no api key")

    monkeypatch.setattr(embedding_module.genai, "Client", boom)
    monkeypatch.setattr(embedding_module, "_embedding_client", None)

    client = embedding_module.get_embedding_client()
    # We should get the OfflineEmbeddingClient with an `embed` method.
    assert hasattr(client, "embed")
    assert callable(client.embed)

    # And embed_text should work using that client.
    vec = embedding_module.embed_text("ab")
    assert vec == [0.7, 0.8]  # deterministic offline embedding


def test_embedding_real_client_path(monkeypatch):
    """
    Covers the `if hasattr(client, "embeddings")` branch in embed_text().
    """

    class FakeResponse:
        def __init__(self):
            # Mimic Google response: a list of embedding objects
            self.embeddings = [type("E", (), {"values": [0.1, 0.2, 0.3]})]

    class FakeEmbeddingsClient:
        def embed_content(self, model, content):
            # Ignore arguments; just return FakeResponse
            return FakeResponse()

    class FakeRealClient:
        def __init__(self):
            self.embeddings = FakeEmbeddingsClient()

    fake_client = FakeRealClient()

    monkeypatch.setattr(
        embedding_module,
        "_embedding_client",
        fake_client,
    )
    monkeypatch.setattr(
        embedding_module,
        "get_embedding_client",
        lambda: fake_client,
    )

    vec = embedding_module.embed_text("hello")
    assert vec == [0.1, 0.2, 0.3]
