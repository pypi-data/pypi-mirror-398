from multimodal_agent.project_scanner import (
    extract_style_profile,
    scan_project,
)


def test_scan_project_basic(tmp_path):
    project = tmp_path / "example"
    project.mkdir()

    # Simulate pubspec.yaml
    pubspec = project / "pubspec.yaml"
    pubspec.write_text("name: example_project")

    profile = scan_project(str(project))

    assert profile is not None
    assert profile.package_name == "example_project"
    assert isinstance(profile.root, type(project))


def test_extract_style_profile():
    mock_scan = type(
        "ScanResult",
        (),
        {
            "package_name": "testpkg",
            "uses_bloc": True,
            "uses_getx": False,
            "uses_riverpod": True,
        },
    )()

    style = extract_style_profile(mock_scan)

    assert "package_name" in style
    assert style["uses_bloc"] is True
    assert style["uses_riverpod"] is True
    assert style["uses_getx"] is False
