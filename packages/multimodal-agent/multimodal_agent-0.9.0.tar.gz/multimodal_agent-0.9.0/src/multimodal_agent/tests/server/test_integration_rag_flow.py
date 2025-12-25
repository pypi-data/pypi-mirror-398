from multimodal_agent.project_scanner import (
    extract_style_profile,
    ingest_style_into_rag,
    scan_project,
)
from multimodal_agent.rag.rag_store import SQLiteRAGStore


def test_full_project_learning_flow(tmp_path, monkeypatch):
    # Create dummy project
    proj = tmp_path / "demo"
    proj.mkdir()
    (proj / "pubspec.yaml").write_text("name: demo_app\n")

    scan = scan_project(str(proj))
    assert scan.package_name == "demo_app"

    style = extract_style_profile(scan)
    assert "package_name" in style

    # Define RAG store.
    rag = SQLiteRAGStore()

    # Ingest style (will store a chunk + embedding metadata)
    ingest_style_into_rag(style, rag)

    # Patch embed_text so query embedding returns something
    def fake_embed_text(text, model):
        return [0.1, 0.2, 0.3]

    monkeypatch.setattr(
        "multimodal_agent.core.embedding.embed_text",
        fake_embed_text,
    )

    # Get the model name actually used during ingestion
    stored = rag.conn.execute(
        "SELECT DISTINCT model FROM embeddings",
    ).fetchall()

    assert stored, "No embeddings were stored at all"
    model_name = stored[0][0]

    # Perform search using correct model
    results = rag.search_similar(
        query_embedding="demo_app",
        model=model_name,
        top_k=5,
    )

    # Assert results are non-empty
    assert len(results) > 0
