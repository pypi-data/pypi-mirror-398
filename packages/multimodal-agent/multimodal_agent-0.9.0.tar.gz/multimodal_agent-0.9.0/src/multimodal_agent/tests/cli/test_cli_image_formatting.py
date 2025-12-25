import sys
from unittest.mock import patch

import multimodal_agent.cli.cli as cli
from multimodal_agent.core.agent_core import AgentResponse, MultiModalAgent


@patch.object(MultiModalAgent, "ask")
def test_cli_formatting_flag(mock_ask, monkeypatch, capsys):
    # Mock ask() to simulate already-formatted output
    mock_ask.return_value = AgentResponse(
        text="```python\nprint('hello')\n```",
        data=None,
        usage=None,
    )

    # Simulate command-line: agent ask test --format
    monkeypatch.setattr(sys, "argv", ["agent", "ask", "test", "--format"])

    cli.main()

    captured = capsys.readouterr()
    output = captured.out.strip()

    # Ensure CLI printed the formatted text
    assert "```" in output
    assert "print('hello')" in output

    # Optionally also verify that formatted=True was passed
    _, kwargs = mock_ask.call_args
    assert kwargs.get("formatted") is True
