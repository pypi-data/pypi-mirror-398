import re
from pathlib import Path

import pytest

from multimodal_agent.codegen.engine import CodegenEngine
from multimodal_agent.codegen.utils import sanitize_class_name, to_snake_case


@pytest.fixture
def fake_engine(monkeypatch):
    """
    Creates a CodegenEngine with run() patched so we do not call actual LLM.
    run() will return a valid Dart class containing the expected class name.
    """
    engine = CodegenEngine()

    def fake_run(self, prompt):

        match = re.search(r"named\s+`([A-Za-z0-9_]+)`", prompt)
        if match:
            class_name = match.group(1)
        else:
            class_name = "GeneratedWidget"
        return f"class {class_name} {{}}"

    monkeypatch.setattr(CodegenEngine, "run", fake_run, raising=True)

    return engine


def test_generate_and_write_widget(tmp_path: Path, fake_engine: CodegenEngine):
    # create fake Flutter project
    (tmp_path / "pubspec.yaml").write_text("name: test")

    out = fake_engine.generate_and_write(
        kind="widget",
        name="TestWidget",
        root=tmp_path,
        override=True,
    )

    class_name = sanitize_class_name("TestWidget")
    snake = to_snake_case(class_name)

    expected_path = tmp_path / "lib" / "widgets" / f"{snake}.dart"
    assert out == expected_path
    assert expected_path.exists()

    code = expected_path.read_text()
    assert f"class {class_name}" in code


def test_generate_and_write_screen(tmp_path: Path, fake_engine: CodegenEngine):
    (tmp_path / "pubspec.yaml").write_text("name: test")

    out = fake_engine.generate_and_write(
        kind="screen",
        name="Home",
        root=tmp_path,
        override=True,
    )

    class_name = sanitize_class_name("Home")
    snake = to_snake_case(class_name)

    expected_path = tmp_path / "lib" / "screens" / f"{snake}_screen.dart"
    assert out == expected_path
    assert expected_path.exists()

    code = expected_path.read_text()
    assert f"class {class_name}" in code


def test_generate_and_write_model(tmp_path: Path, fake_engine: CodegenEngine):
    (tmp_path / "pubspec.yaml").write_text("name: test")

    out = fake_engine.generate_and_write(
        kind="model",
        name="User",
        root=tmp_path,
        override=True,
    )

    class_name = sanitize_class_name("User")
    snake = to_snake_case(class_name)

    expected_path = tmp_path / "lib" / "models" / f"{snake}.dart"
    assert out == expected_path
    assert expected_path.exists()

    code = expected_path.read_text()
    assert f"class {class_name}" in code
