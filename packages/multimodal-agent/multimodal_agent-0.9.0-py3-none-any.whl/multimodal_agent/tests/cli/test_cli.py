import sys as system
import types
from unittest.mock import MagicMock

import pytest

import multimodal_agent.cli.cli as cli
from multimodal_agent import __version__
from multimodal_agent.core import agent_core


@pytest.fixture(autouse=True)
def mock_google_client(mocker):
    """Mock genai.Client so no real Google API is touched."""
    fake_client = MagicMock()
    fake_client.models.generate_content.return_value = MagicMock(text="mocked")
    mocker.patch(
        "multimodal_agent.agent_core.Client",
        return_value=fake_client,
    )
    return fake_client


# test cli version.
def test_cli_version(monkeypatch, capsys):
    monkeypatch.setattr(system, "argv", ["agent", "--version"])
    cli.main()
    captured = capsys.readouterr().out.strip()
    assert f"multimodal-agent version {__version__}" in captured


def test_cli_ask(monkeypatch, capsys, mocker):
    fake_agent = types.SimpleNamespace(
        ask=lambda prompt, **kwargs: f"ANSWER: {prompt}",
    )
    mocker.patch.object(
        agent_core,
        "MultiModalAgent",
        return_value=fake_agent,
    )

    monkeypatch.setattr(system, "argv", ["agent", "ask", "hello"])
    cli.main()

    out = capsys.readouterr().out.strip()
    assert "ANSWER: hello" in out


# Test text and image question - image command.
def test_cli_image(monkeypatch, capsys, mocker):
    fake_agent = types.SimpleNamespace(
        ask_with_image=lambda prompt, img, **kwargs: f"IMAGE_ANSWER: {prompt}",
    )

    mocker.patch.object(agent_core, "MultiModalAgent", return_value=fake_agent)
    mocker.patch.object(cli, "load_image_as_part", return_value="FAKE_PART")

    monkeypatch.setattr(
        system,
        "argv",
        ["agent", "image", "fake.jpg", "describe this"],
    )
    cli.main()
    out = capsys.readouterr().out.strip()
    assert "IMAGE_ANSWER: describe this" in out


# Test invalid image.
def test_cli_image_invalid(monkeypatch, caplog, mocker):
    monkeypatch.setattr(
        system,
        "argv",
        ["agent", "image", "bad.jpg", "prompt"],
    )

    fake_agent = mocker.Mock()
    mocker.patch.object(agent_core, "MultiModalAgent", return_value=fake_agent)

    mocker.patch.object(
        cli,
        "load_image_as_part",
        side_effect=Exception("boom"),
    )

    logger = cli.logger
    logger.handlers = [caplog.handler]
    logger.setLevel("ERROR")

    # DO NOT expect SystemExit — your CLI does not use it for image errors
    cli.main()

    messages = [rec.getMessage() for rec in caplog.records]
    assert any("Cannot read image: bad.jpg" in msg for msg in messages)


# Test chat command.
def test_cli_chat(monkeypatch, mocker):
    # New chat signature accepts session_id
    fake_agent = types.SimpleNamespace(chat=lambda session_id="default": None)
    mocker.patch.object(
        agent_core,
        "MultiModalAgent",
        return_value=fake_agent,
    )

    monkeypatch.setattr(system, "argv", ["agent", "chat"])
    cli.main()  # should run without exception


def test_cli_no_command(monkeypatch, capsys):
    monkeypatch.setattr(system, "argv", ["agent"])
    cli.main()
    out = capsys.readouterr().out
    assert "usage:" in out.lower()


def test_cli_version_flag(capsys):
    parser = cli.build_parser()
    args = parser.parse_args(["--version"])
    assert args.version is True


def test_cli_ask_parser():
    parser = cli.build_parser()
    args = parser.parse_args(["ask", "hello"])
    assert args.command == "ask"
    assert args.prompt == "hello"
    assert args.no_rag is False


def test_cli_history_show_parser():
    parser = cli.build_parser()
    args = parser.parse_args(["history", "show"])
    assert args.command == "history"
    assert args.history_cmd == "show"
