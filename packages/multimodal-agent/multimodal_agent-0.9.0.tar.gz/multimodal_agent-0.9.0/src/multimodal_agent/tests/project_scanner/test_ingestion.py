from multimodal_agent.project_scanner import ingest_style_into_rag
from multimodal_agent.rag.rag_store import SQLiteRAGStore


def test_ingest_style_into_rag(tmp_path):
    rag = SQLiteRAGStore(db_path=str(tmp_path / "memory.db"))

    style = {
        "package_name": "my_app",
        "uses_bloc": True,
        "uses_getx": False,
    }

    ingest_style_into_rag(style, rag)

    # Should be stored as a chunk
    rows = rag.get_recent_chunks(limit=10)
    assert len(rows) == 1
    assert rows[0].role == "project_style"
    assert "uses_bloc" in rows[0].content
