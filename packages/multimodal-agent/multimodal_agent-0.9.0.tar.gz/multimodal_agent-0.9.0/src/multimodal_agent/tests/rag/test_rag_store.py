from pathlib import Path

import pytest

from multimodal_agent.rag.rag_store import Chunk, SQLiteRAGStore


@pytest.fixture
def rag_store(tmp_path: Path):
    db_path = tmp_path / "memory.db"
    store = SQLiteRAGStore(db_path=db_path)
    try:
        yield store
    finally:
        store.close()


@pytest.mark.use_real_rag
def test_add_and_get_recent_chunks(rag_store: SQLiteRAGStore):

    id1 = rag_store.add_chunk(
        "hello",
        role="user",
        session_id="s1",
        source="chat",
    )
    id2 = rag_store.add_chunk(
        "world",
        role="agent",
        session_id="s2",
        source="chat",
    )

    chunks = rag_store.get_recent_chunks(limit=10)
    assert [chunk.id for chunk in chunks] == [id1, id2]

    chunk1, chunk2 = chunks
    # assert chunk1
    assert isinstance(chunk1, Chunk)
    assert chunk1.id == id1
    assert chunk1.content == "hello"
    assert chunk1.role == "user"
    assert chunk1.session_id == "s1"
    # assert chunk 2
    assert isinstance(chunk2, Chunk)
    assert chunk2.id == id2
    assert chunk2.content == "world"
    assert chunk2.role == "agent"
    assert chunk2.session_id == "s2"


def test_add_embedding_and_search_similar(rag_store: SQLiteRAGStore):
    # prepare two chunks with embeddings
    chunk_id1 = rag_store.add_chunk("chunk-1", role="user", session_id="s1")
    chunk_id2 = rag_store.add_chunk("chunk-2", role="agent", session_id="s2")
    model = "test-emb"

    rag_store.add_embedding(chunk_id1, [1.0, 0.0], model=model)
    rag_store.add_embedding(chunk_id2, [0.0, 1.0], model=model)

    query = [1.0, 0.0]

    results = rag_store.search_similar(
        query_embedding=query,
        model=model,
        top_k=2,
    )

    assert len(results) == 2

    (score1, chunk1), (score2, chunk2) = results

    # assert first chunk values.
    assert chunk1.id == chunk_id1
    assert chunk1.content == "chunk-1"
    assert chunk1.role == "user"
    assert chunk1.session_id == "s1"
    # assert second chunk values.
    assert score1 > score2
    assert chunk2.id == chunk_id2
    assert chunk2.role == "agent"
    assert chunk2.content == "chunk-2"
    assert chunk2.session_id == "s2"


def test_search_similar_empty_db(rag_store: SQLiteRAGStore):
    results = rag_store.search_similar(
        query_embedding=[1.0, 0.0],
        model="no-model",
        top_k=5,
    )
    assert results == []


def test_delete_chunk_cascades_embedding(rag_store: SQLiteRAGStore):
    # initial setup.
    chunk_id = rag_store.add_chunk("to-delete", role="user", session_id="s1")
    embedding = [0.1, 0.2, 0.3]
    model = "test_emb"

    rag_store.add_embedding(
        chunk_id=chunk_id,
        embedding=embedding,
        model=model,
    )

    results_before = rag_store.search_similar(
        query_embedding=embedding,
        model=model,
        top_k=1,
    )

    # assert initial results.
    assert len(results_before) == 1
    assert results_before[0][1].id == chunk_id

    # delete chunk
    rag_store.delete_chunk(chunk_id=chunk_id)

    # confirm the results after deleting the chunk.
    results_after = rag_store.search_similar(
        query_embedding=embedding,
        model=model,
        top_k=1,
    )
    # cascades strategy confirms that after delete results should be empty.
    assert len(results_after) == 0


def test_clear_all(rag_store: SQLiteRAGStore):
    # initial setup.
    chunk_id1 = rag_store.add_chunk(
        "chunk-1",
        role="user",
        session_id="s1",
    )
    chunk_id2 = rag_store.add_chunk(
        "chunk-2",
        role="agent",
        session_id="s2",
    )
    model = "test-emb"

    # add embeddings.
    rag_store.add_embedding(
        chunk_id=chunk_id1,
        embedding=[0.1, 0.2],
        model=model,
    )

    rag_store.add_embedding(
        chunk_id=chunk_id2,
        embedding=[0.3, 0.4],
        model=model,
    )
    # delete all embeddings
    rag_store.clear_all()

    assert rag_store.get_recent_chunks(limit=10) == []

    results = rag_store.search_similar(
        query_embedding=[0.1, 0.2],
        model=model,
    )

    assert results == []
