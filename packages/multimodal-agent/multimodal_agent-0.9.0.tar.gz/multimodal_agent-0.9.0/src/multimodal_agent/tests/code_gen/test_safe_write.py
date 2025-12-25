from multimodal_agent.codegen.engine import CodegenEngine


def test_safe_write_creates_file(tmp_path):
    eng = CodegenEngine()
    fp = tmp_path / "file.dart"

    eng.safe_write(fp, "hello")

    assert fp.read_text() == "hello"


def test_safe_write_prevents_overwrite(tmp_path):
    eng = CodegenEngine()
    fp = tmp_path / "file.dart"
    fp.write_text("old")

    try:
        eng.safe_write(fp, "new")
        assert False, "Expected FileExistsError"
    except FileExistsError:
        assert True


def test_safe_write_override(tmp_path):
    eng = CodegenEngine()
    fp = tmp_path / "file.dart"
    fp.write_text("old")

    eng.safe_write(fp, "new", override=True)

    assert fp.read_text() == "new"
