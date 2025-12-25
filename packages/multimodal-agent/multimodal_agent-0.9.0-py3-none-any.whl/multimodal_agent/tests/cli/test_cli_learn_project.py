from multimodal_agent.cli import test_main as cli


def test_cli_learn_project(tmp_path):
    # Create a fake project with pubspec.yaml
    proj = tmp_path / "proj"
    proj.mkdir()
    (proj / "pubspec.yaml").write_text("name: cli_app\n")

    # Call CLI wrapper directly
    result = cli(["learn-project", str(proj)])

    # Exit code should be zero
    assert result == 0

    # The output should contain project name
    # cli() prints to stdout, so capture via capsys if needed
    # But for now just ensure no crash
    # The scanner always prints profile JSON; so test minimal success condition


def test_cli_list_projects():
    # Just call list-projects; should not crash
    result = cli(["list-projects"])
    assert result == 0


def test_cli_show_project(tmp_path):
    proj = tmp_path / "myp"
    proj.mkdir()
    (proj / "pubspec.yaml").write_text("name: show_app\n")

    # First learn project
    cli(["learn-project", str(proj), "-p", "project:show_app"])

    # Show project
    result = cli(["show-project", "project:show_app"])
    assert result == 0
