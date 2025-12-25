import sys as system
from unittest.mock import patch

from multimodal_agent.cli.cli import main
from multimodal_agent.core.agent_core import AgentResponse, MultiModalAgent


def fake_ask(
    self,
    question,
    session_id=None,
    response_format="text",
    formatted=False,
):
    if formatted:
        return AgentResponse(
            text="```python\nprint('hello')\n```",
            data=None,
            usage=None,
        )
    return AgentResponse(
        text="print('hello')",
        data=None,
        usage=None,
    )


@patch.object(MultiModalAgent, "ask", fake_ask)
def test_cli_formatting_flag(monkeypatch, capsys):
    monkeypatch.setattr(
        system,
        "argv",
        ["agent", "ask", "test", "--format"],
    )

    main()

    output = capsys.readouterr().out.strip()

    assert "```" in output
    assert "print('hello')" in output
