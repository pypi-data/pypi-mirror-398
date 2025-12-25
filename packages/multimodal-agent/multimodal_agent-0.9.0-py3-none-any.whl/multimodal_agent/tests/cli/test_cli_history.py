import sys as system
import types
from types import SimpleNamespace

import multimodal_agent.cli.cli as cli


def make_store(chunks=None):
    return types.SimpleNamespace(
        get_recent_chunks=lambda limit=None: chunks or [],
        delete_chunk=lambda chunk_id=None: None,
        clear_all=lambda: None,
        close=lambda: None,
    )


def test_cli_history_show_empty(monkeypatch, capsys):
    store = make_store([])
    monkeypatch.setattr(
        "multimodal_agent.cli.cli.SQLiteRAGStore", lambda *a, **k: store
    )
    monkeypatch.setattr(system, "argv", ["agent", "history", "show"])
    cli.main()
    print("output:", capsys.readouterr().out)
    assert "No history" in capsys.readouterr().out


def test_cli_history_delete(monkeypatch, capsys):

    store = make_store()
    store.delete_chunk = lambda **kw: None

    monkeypatch.setattr(
        "multimodal_agent.rag.rag_store.SQLiteRAGStore",
        lambda *a, **k: store,
    )

    monkeypatch.setattr(system, "argv", ["agent", "history", "delete", "2"])
    cli.main()
    out = capsys.readouterr().out

    assert "Deleted chunk 2" in out
    assert '"chunk_id": 2' in out  # also appears in JSON footer


def test_cli_history_reset(monkeypatch, capsys):
    store = make_store()
    monkeypatch.setattr(
        "multimodal_agent.rag.rag_store.SQLiteRAGStore", lambda *a, **k: store
    )

    monkeypatch.setattr(system, "argv", ["agent", "history", "clear"])
    cli.main()
    assert "History cleared" in capsys.readouterr().out


def test_cli_history_summary(monkeypatch, capsys, mocker):
    chunk = SimpleNamespace(
        id=1,
        role="user",
        session_id="s",
        content="hello",
        created_at="2024",
    )
    store = make_store([chunk])

    monkeypatch.setattr(
        "multimodal_agent.cli.cli.SQLiteRAGStore",
        lambda *a, **k: store,
    )

    class FakeAgent:
        def __init__(self, *a, **k):
            pass

        def safe_generate_content(self, contents):
            return (SimpleNamespace(text="summary ok"), {"prompt_tokens": 0})

    mocker.patch("multimodal_agent.core.agent_core.MultiModalAgent", FakeAgent)

    monkeypatch.setattr(system, "argv", ["agent", "history", "summary"])
    cli.main()
    out = capsys.readouterr().out
    print("out is: ", out)
    assert "summary ok" in out
