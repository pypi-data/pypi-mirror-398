import pytest

from multimodal_agent.core.agent_core import MultiModalAgent
from multimodal_agent.errors import RetryableError


class DummyRetryable(Exception):
    def __init__(self, *args):
        super().__init__(*args)
        self.status_code = 503


def test_safe_generate_content_retries_and_fails(monkeypatch, caplog):
    agent = MultiModalAgent(client=None)

    class DummyRetryable(Exception):
        def __init__(self, msg):
            super().__init__(msg)
            self.status_code = 503

    class DummyClient:
        class models:
            @staticmethod
            def generate_content(*args, **kwargs):
                raise DummyRetryable("503 overload")

    agent.client = DummyClient()
    agent.logger.handlers = [caplog.handler]
    agent.logger.setLevel("WARNING")

    with caplog.at_level("WARNING"):
        with pytest.raises(RetryableError):
            agent.safe_generate_content(["hello"], max_retries=3, base_delay=0)

    warnings = [m for m in caplog.messages if "Retry" in m]
    assert len(warnings) == 3
