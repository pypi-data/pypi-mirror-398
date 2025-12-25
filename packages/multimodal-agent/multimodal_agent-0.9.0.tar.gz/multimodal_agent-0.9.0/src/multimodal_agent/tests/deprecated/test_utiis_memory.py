import pytest

import multimodal_agent.deprecated.json_memory as utils


@pytest.fixture
def memory_file(tmp_path, monkeypatch):
    fake_path = tmp_path / "memory.json"
    monkeypatch.setattr(utils, "MEMORY_PATH", fake_path)
    return fake_path


def test_load_memory_empty(memory_file):
    assert utils.load_memory() == []


def test_append_and_load(memory_file):
    utils.append_memory("USER: hello")
    utils.append_memory("AGENT: hi")
    mem = utils.load_memory()
    assert mem == ["USER: hello", "AGENT: hi"]


def test_delete_memory_index(memory_file):
    utils.append_memory("A")
    utils.append_memory("B")
    utils.append_memory("C")

    ok = utils.delete_memory_index(1)
    assert ok is True
    assert utils.load_memory() == ["A", "C"]

    # invalid index
    assert utils.delete_memory_index(10) is False


def test_reset_memory(memory_file):
    utils.append_memory("X")
    utils.reset_memory()
    assert utils.load_memory() == []
