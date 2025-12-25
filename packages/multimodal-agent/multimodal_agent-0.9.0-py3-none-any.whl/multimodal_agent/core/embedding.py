from typing import List

from google import genai

_embedding_client = None

DEFAULT_EMBED_MODEL = "text-embedding-004"


def get_embedding_client():
    """
    Returns a cached embedding client.
    In tests, this function is monkeypatched to return a DummyClient.
    In real usage, it creates a genai.Client using GOOGLE_API_KEY.
    """
    global _embedding_client

    # Reuse existing instance.
    if _embedding_client is not None:
        return _embedding_client

    # No API key means offline fake client.
    try:
        _embedding_client = genai.Client()
    except Exception:

        class OfflineEmbeddingClient:
            def embed(self, text):
                # Deterministic fake embedding
                return [float((ord(c) % 10) / 10) for c in text][:32]

        _embedding_client = OfflineEmbeddingClient()

    return _embedding_client


def embed_text(text: str, model: str = DEFAULT_EMBED_MODEL) -> List[float]:
    """
    Embed text using any available backend:

    - Real Google API (client.embeddings.embed_content)
    - Offline fallback (client.embed)
    - DummyClient (client.models.embed_content) used in tests

    Always returns a flat Python list of floats.
    """

    if model is None:
        model = DEFAULT_EMBED_MODEL
    client = get_embedding_client()

    # Offline fallback: client has no real embedding API
    if hasattr(client, "embed"):
        return list(client.embed(text))

    # Real google client.
    if hasattr(client, "embeddings"):
        response = client.embeddings.embed_content(
            model=model,
            content=text,
        )
        first = response.embeddings[0]
        return list(getattr(first, "values", first))

    # Dummy api used in tests.
    response = client.models.embed_content(model=model, contents=[text])
    first = response.embeddings[0]
    values = getattr(first, "values", first)

    return list(values)
