from multimodal_agent.codegen.engine import CodegenEngine


def test_detect_project_root(tmp_path):
    proj = tmp_path / "myapp"
    proj.mkdir()
    (proj / "pubspec.yaml").write_text("name: test")

    eng = CodegenEngine()
    root = eng.detect_project_root(proj)

    assert root == proj


def test_detect_project_root_from_child(tmp_path):
    proj = tmp_path / "myapp"
    nested = proj / "lib" / "screens"
    nested.mkdir(parents=True)

    (proj / "pubspec.yaml").write_text("name: test")

    eng = CodegenEngine()
    root = eng.detect_project_root(nested)

    assert root == proj


def test_detect_project_root_missing(tmp_path):
    eng = CodegenEngine()
    try:
        eng.detect_project_root(tmp_path)
        assert False, "Expected FileNotFoundError"
    except FileNotFoundError:
        assert True
