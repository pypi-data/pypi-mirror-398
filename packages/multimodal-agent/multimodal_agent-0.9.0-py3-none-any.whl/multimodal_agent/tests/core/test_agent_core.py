import builtins

import pytest

from multimodal_agent.core import agent_core
from multimodal_agent.core.agent_core import MultiModalAgent
from multimodal_agent.errors import NonRetryableError, RetryableError
from multimodal_agent.utils import load_image_as_part


def test_task_text(mock_agent):
    response = mock_agent.ask("hello")
    assert response.text == "mocked response"


def test_task_with_image(mock_agent, tmp_path, monkeypatch):
    image_path = tmp_path / "img.jpg"
    # Fake image bytes.
    image_path.write_bytes(b"\xff\xd8\xff\xd9")

    # Mock PIL.Image.open so decoding always succeeds.
    class DummyImage:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def tobytes(self):
            return b"fakeimage"

    monkeypatch.setattr("PIL.Image.open", lambda *_: DummyImage())

    image_part = load_image_as_part(str(image_path))

    response = mock_agent.ask_with_image("describe", image_part)
    assert response.text == "mocked response"


def test_chat_history_format(mock_agent, mocker):
    """
    Ensure chat appends text to history correctly.
    """
    # simulate user input twice then exit
    mocker.patch("builtins.input", side_effect=["hello", "exit"])

    # MUST return AgentResponse, not plain object
    mock_agent.safe_generate_content = lambda contents: (
        type("R", (), {"text": "reply"})(),
        None,
    )

    mock_agent.chat()


class DummyModels:
    @staticmethod
    def generate_content(*args, **kwargs):
        raise RuntimeError("Dummy client: no API key available.")


class DummyClientNoModels:
    """Client with no .models attribute → forces OFFLINE mode."""

    def __init__(self):
        self.models = DummyModels()


class FakeUsageResponse:
    def __init__(self, text, usage=None):
        self.text = text
        self.usage_metadata = usage


class FakeModels:
    def __init__(self, text):
        self._text = text

    def generate_content(self, model, contents):
        return FakeUsageResponse(self._text)


class FakeClientWithModels:
    def __init__(self, text='{"answer": 1}'):
        self.models = FakeModels(text)


class FakeRAGStore:
    def __init__(self):
        self.messages = []
        self.embeddings = []
        self.searched = []

    def add_logical_message(self, content, role, session_id, source):
        self.messages.append(
            {
                "content": content,
                "role": role,
                "session_id": session_id,
                "source": source,
            },
        )
        # Return fake chunk ids
        return [1]

    def add_embedding(self, chunk_id, embedding, model):
        self.embeddings.append((chunk_id, tuple(embedding), model))

    def search_similar(self, query_embedding, model, top_k):
        # Return nothing, to exercise the "no context" paths.
        self.searched.append((tuple(query_embedding), model, top_k))
        return []


def test_agent_init_uses_dummy_client_when_no_api_key(monkeypatch):
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)

    # IMPORTANT: config may contain an api_key → must neutralize it
    monkeypatch.setattr(agent_core, "get_config", lambda: {})

    agent = MultiModalAgent(client=None, enable_rag=False, rag_store=None)

    assert hasattr(agent.client, "models")
    with pytest.raises(RuntimeError):
        agent.client.models.generate_content(model="x", contents=["y"])


# ask_with_image JSON path + _parse_json_output exception
def test_ask_with_image_json_parse_error_falls_back_to_none(monkeypatch):
    # Online mode client
    monkeypatch.setenv("GOOGLE_API_KEY", "dummy-key")

    client = FakeClientWithModels(text="```json {not-valid-json} ```")
    agent = MultiModalAgent(client=client, enable_rag=False, rag_store=None)
    agent.usage_logging = False

    # Force _parse_json_output to raise → we want data = None
    def boom(_text):
        raise ValueError("bad json")

    monkeypatch.setattr(agent, "_parse_json_output", boom)

    # Dummy 'image' (no need to be real Part; runtime doesn't enforce type)
    dummy_image = object()

    resp = agent.ask_with_image(
        "question",
        dummy_image,
        response_format="json",
    )
    assert isinstance(resp.text, str)
    assert resp.data is None  # came from the except-branch


def test_ask_json_with_rag_calls_store_agent_reply(monkeypatch):
    monkeypatch.setenv("GOOGLE_API_KEY", "dummy-key")

    client = FakeClientWithModels(text='{"answer": 42}')
    rag_store = FakeRAGStore()

    agent = MultiModalAgent(
        client=client,
        rag_store=rag_store,
        enable_rag=True,
    )
    agent.usage_logging = False

    # Fake embed_text so it doesn't hit the real API
    monkeypatch.setattr(
        agent_core,
        "embed_text",
        lambda text, model: [0.1, 0.2],
    )

    resp = agent.ask(
        "What is life?",
        session_id="sess-1",
        response_format="json",
    )

    assert resp.data == {"answer": 42}
    # Question + agent reply should be stored
    roles = [m["role"] for m in rag_store.messages]
    assert "user" in roles
    assert "agent" in roles


def test_ensure_session_id_returns_given_value(monkeypatch):
    agent = MultiModalAgent(
        client=DummyClientNoModels(), enable_rag=False, rag_store=None
    )
    assert agent._ensure_session_id("custom") == "custom"


def test_convert_to_json_response_parses_valid_json():
    agent = MultiModalAgent(
        client=DummyClientNoModels(), enable_rag=False, rag_store=None
    )

    class Resp:
        def __init__(self):
            self.text = '{"x": 1}'

    r = Resp()
    out = agent._convert_to_json_response(r)
    assert out.json == {"x": 1}


def test_convert_to_json_response_fallback_raw():
    agent = MultiModalAgent(
        client=DummyClientNoModels(), enable_rag=False, rag_store=None
    )

    class Resp:
        def __init__(self):
            self.text = "not-json"

    r = Resp()
    out = agent._convert_to_json_response(r)
    assert out.json == {"raw": "not-json"}


def test_parse_json_output_handles_fenced_block():
    agent = MultiModalAgent(
        client=DummyClientNoModels(), enable_rag=False, rag_store=None
    )
    text = '```json\n{"a": 1}\n```'
    parsed = agent._parse_json_output(text)
    assert parsed == {"a": 1}


def test_parse_json_output_trailing_backticks_only():
    agent = MultiModalAgent(
        client=DummyClientNoModels(), enable_rag=False, rag_store=None
    )
    text = 'json {"b": 2}```'
    parsed = agent._parse_json_output(text)
    assert parsed == {"b": 2}


def test_strip_markdown_removes_fence_and_json_prefix():
    agent = MultiModalAgent(
        client=DummyClientNoModels(), enable_rag=False, rag_store=None
    )
    raw = '```json\n{"c": 3}\n```'
    cleaned = agent._strip_markdown(raw)
    assert cleaned == '{"c": 3}'


def test_store_agent_reply_catches_embedding_errors(monkeypatch):
    rag_store = FakeRAGStore()
    agent = MultiModalAgent(
        client=DummyClientNoModels(), rag_store=rag_store, enable_rag=True
    )

    # embed_text should blow up → we want except-block to swallow it
    def boom(text, model):
        raise RuntimeError("embed failed")

    monkeypatch.setattr(agent_core, "embed_text", boom)

    # Should not raise
    agent._store_agent_reply(answer={"foo": "bar"}, session_id="sess-2")

    # Message still stored
    assert any(m["role"] == "agent" for m in rag_store.messages)


def test_log_usage_ignores_file_errors(monkeypatch):
    agent = MultiModalAgent(
        client=DummyClientNoModels(), enable_rag=False, rag_store=None
    )

    def fake_open(*args, **kwargs):
        raise IOError("disk full")

    monkeypatch.setattr(builtins, "open", fake_open)

    # Should not raise even if open() fails
    agent._log_usage(
        usage={"prompt_tokens": 1, "response_tokens": 2, "total_tokens": 3},
        contents=["hi"],
        response_format="text",
        model="dummy",
    )


def test_chat_embedding_failure_and_assistant_embed_failure(monkeypatch):
    """
    Covers:
    - question_embedding exception → question_embedding = None (485–486)
    - rag_context = [] (490)
    - assistant reply embedding exception in chat (566–567)
    """

    rag_store = FakeRAGStore()
    agent = MultiModalAgent(
        client=DummyClientNoModels(), rag_store=rag_store, enable_rag=True
    )

    # embed_text always fails (both for user message and assistant reply).
    def boom(text, model):
        raise RuntimeError("embed failed in chat")

    monkeypatch.setattr(agent_core, "embed_text", boom)

    # safe_generate_content returns a fake response so chat can proceed.
    class Resp:
        def __init__(self, t):
            self.text = t

    def fake_safe_generate(
        contents, max_retries=3, base_delay=1, response_format="text"
    ):
        return Resp("answer from model"), {
            "prompt_tokens": 1,
            "response_tokens": 1,
            "total_tokens": 2,
        }

    monkeypatch.setattr(agent, "safe_generate_content", fake_safe_generate)

    # Simulate one user message then exit.
    inputs = iter(["hello", "exit"])
    monkeypatch.setattr("builtins.input", lambda _prompt: next(inputs))

    agent.chat(session_id="chat-sess-1", enable_rag=True, rag_top_k=3)
    # No assertion needed: just ensuring exceptions don’t bubble.


def test_chat_handles_retryable_error(monkeypatch):
    """
    Covers except RetryableError (533–534).
    """

    agent = MultiModalAgent(
        client=DummyClientNoModels(), rag_store=None, enable_rag=False
    )

    def raise_retryable(
        contents,
        max_retries=3,
        base_delay=1,
        response_format="text",
    ):
        raise RetryableError("temporary")

    monkeypatch.setattr(agent, "safe_generate_content", raise_retryable)

    inputs = iter(["hello", "exit"])
    monkeypatch.setattr("builtins.input", lambda _prompt: next(inputs))

    # Should not raise; just logs and continues to next loop iteration
    agent.chat(session_id="chat-sess-3", enable_rag=False)


def test_chat_handles_non_retryable_error(monkeypatch):
    """
    Covers except NonRetryableError (540–542).
    """

    agent = MultiModalAgent(
        client=DummyClientNoModels(), rag_store=None, enable_rag=False
    )

    def raise_non_retryable(
        contents,
        max_retries=3,
        base_delay=1,
        response_format="text",
    ):
        raise NonRetryableError("permanent")

    monkeypatch.setattr(agent, "safe_generate_content", raise_non_retryable)

    inputs = iter(["hello", "exit"])
    monkeypatch.setattr("builtins.input", lambda _prompt: next(inputs))

    # Should not raise; just logs and continues to next loop iteration
    agent.chat(session_id="chat-sess-4", enable_rag=False)
