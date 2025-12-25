from types import SimpleNamespace

import pytest

from multimodal_agent.cli.history import (
    _clear_history,
    _delete_history,
    _show_history,
    _summary_history,
)


@pytest.fixture
def fake_store(mocker):
    store = mocker.Mock()
    store.close = lambda: None
    return store


def test_show_history_empty(capsys, fake_store):
    fake_store.get_recent_chunks.return_value = []

    args = SimpleNamespace(limit=10, session=None)
    assert _show_history(args, fake_store) == 0

    out = capsys.readouterr().out
    assert "No history found" in out


def test_show_history_with_items(capsys, fake_store):
    chunk = SimpleNamespace(
        id=1,
        role="user",
        session_id="abc",
        content="hello world",
        created_at="2024-01-01",
    )
    fake_store.get_recent_chunks.return_value = [chunk]

    args = SimpleNamespace(limit=10, session=None)
    _show_history(args, fake_store)

    out = capsys.readouterr().out
    assert "[1] (abc) user @ 2024-01-01" in out
    assert "hello world" in out


def test_delete_history(capsys, fake_store):
    args = SimpleNamespace(chunk_id=44)
    _delete_history(args, fake_store)
    fake_store.delete_chunk.assert_called_once_with(chunk_id=44)

    out = capsys.readouterr().out
    assert "Deleted chunk 44" in out


def test_clear_history(capsys, fake_store):
    args = SimpleNamespace()
    assert _clear_history(args, fake_store) == 0
    fake_store.clear_all.assert_called_once()

    out = capsys.readouterr().out
    assert "History cleared" in out


def test_summary_history(mocker, fake_store, capsys):
    chunk = SimpleNamespace(
        id=1,
        role="user",
        session_id="x",
        content="hello world",
        created_at="2024-01-01",
    )
    fake_store.get_recent_chunks.return_value = [chunk]

    class FakeAgent:
        def __init__(self, *a, **k):
            pass

        def safe_generate_content(self, contents):
            return (SimpleNamespace(text="summary text"), {"prompt_tokens": 0})

    mocker.patch("multimodal_agent.core.agent_core.MultiModalAgent", FakeAgent)

    args = SimpleNamespace(limit=10, session=None)
    _summary_history(args, fake_store)

    assert "summary text" in capsys.readouterr().out
