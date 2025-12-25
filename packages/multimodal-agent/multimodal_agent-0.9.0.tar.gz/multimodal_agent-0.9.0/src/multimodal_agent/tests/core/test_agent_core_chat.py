from multimodal_agent.core.agent_core import MultiModalAgent


def test_chat_error_path(monkeypatch, caplog):
    agent = MultiModalAgent(client=None)

    # Dummy client throwing raw exception from generate_content
    class DummyClient:
        class models:
            @staticmethod
            def generate_content(*a, **k):
                raise Exception("chat failure")

    agent.client = DummyClient()

    # Patch logger for caplog.
    agent.logger.handlers = [caplog.handler]
    agent.logger.setLevel("ERROR")

    # Patch `input()` so chat loop gets "hello" and "exit".
    inputs = iter(["hello", "exit"])
    monkeypatch.setattr("builtins.input", lambda *_: next(inputs))

    with caplog.at_level("ERROR"):
        agent.chat()

    # Validate that error was logged
    messages = " ".join(caplog.messages)
    assert "chat failure" in messages
