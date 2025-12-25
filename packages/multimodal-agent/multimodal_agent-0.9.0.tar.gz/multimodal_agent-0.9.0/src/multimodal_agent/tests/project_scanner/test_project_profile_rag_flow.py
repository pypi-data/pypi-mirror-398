from multimodal_agent.project_scanner import (
    extract_style_profile,
    ingest_style_into_rag,
    scan_project,
)
from multimodal_agent.rag.rag_store import SQLiteRAGStore


def test_full_project_learning_flow(tmp_path):
    proj = tmp_path / "demo"
    proj.mkdir()
    (proj / "pubspec.yaml").write_text("name: demo_app\n")

    scan = scan_project(str(proj))
    style = extract_style_profile(scan)

    rag = SQLiteRAGStore(check_same_thread=False)
    ingest_style_into_rag(style, rag)

    results = rag.search_similar("demo_app", model=None)  # FIXED CALL
    assert isinstance(results, list)
