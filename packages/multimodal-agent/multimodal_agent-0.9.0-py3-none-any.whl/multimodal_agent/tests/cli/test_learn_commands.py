import json
import os
import sys as system

import multimodal_agent.cli.cli as cli
from multimodal_agent.rag.rag_store import SQLiteRAGStore


def test_cli_learn_project(tmp_path, monkeypatch, capsys):
    project = tmp_path / "proj"
    project.mkdir()
    (project / "pubspec.yaml").write_text("name: demo_project")

    os.environ["MULTIMODAL_AGENT_DB"] = str(tmp_path / "db.sqlite")

    monkeypatch.setattr(
        system,
        "argv",
        ["agent", "learn-project", str(project)],
    )
    cli.main()

    out = capsys.readouterr().out
    assert "demo_project" in out


def test_cli_list_projects_empty(tmp_path, monkeypatch, capsys):
    os.environ["MULTIMODAL_AGENT_DB"] = str(tmp_path / "db.sqlite")

    monkeypatch.setattr(system, "argv", ["agent", "list-projects"])
    cli.main()
    out = capsys.readouterr().out
    assert "Stored Project Profiles" in out


def test_cli_show_project(tmp_path, monkeypatch, capsys):
    db = tmp_path / "db.sqlite"
    rag = SQLiteRAGStore(db_path=str(db), check_same_thread=False)

    rag.conn.execute("DELETE FROM chunks")
    rag.conn.commit()

    # Store a simple project profile for this project id
    rag.add_logical_message(
        content=json.dumps({"name": "test"}),
        role="project_profile",
        session_id="project:test",
        source="project-learning",
    )

    # Point the CLI at this temp DB
    os.environ["MULTIMODAL_AGENT_DB"] = str(db)

    # Run the CLI command
    monkeypatch.setattr(
        system,
        "argv",
        ["agent", "show-project", "project:test"],
    )
    cli.main()

    out = capsys.readouterr().out
    print("database", db)

    print("OUTPUT:", out)

    # We expect the stored profile JSON to be printed
    assert '"name": "test"' in out
