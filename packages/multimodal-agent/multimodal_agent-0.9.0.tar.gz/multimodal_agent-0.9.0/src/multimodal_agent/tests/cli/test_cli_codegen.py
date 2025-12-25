import os

from multimodal_agent.cli.cli import test_main


def test_cli_gen_widget(tmp_path, monkeypatch):
    """
    Verifies:
    - CLI command `gen widget MyWidget` runs without errors
    - Engine writes the generated widget file to the correct location
    - Generated code contains correct class name `MyWidget`
    - No markdown or junk text is present
    """

    # Create fake Flutter project root
    (tmp_path / "pubspec.yaml").write_text("name: test")

    # Mock LLM output so we don’t call actual models
    monkeypatch.setattr(
        "multimodal_agent.codegen.engine.CodegenEngine.run",
        lambda self, prompt: (
            "import 'package:flutter/material.dart';\n\n"
            "class MyWidget extends StatelessWidget {\n"
            "  const MyWidget({ super.key });\n\n"
            "  @override\n"
            "  Widget build(BuildContext context) {\n"
            "    return const Text('Hello');\n"
            "  }\n"
            "}\n"
        ),
    )

    # Switch into project directory
    cwd = os.getcwd()
    os.chdir(tmp_path)

    try:
        # Execute CLI
        result = test_main(["gen", "widget", "MyWidget", "--override"])

        # Confirm CLI exited successfully
        assert result == 0 or result is None

        # Expected output file
        expected_file = tmp_path / "lib" / "widgets" / "my_widget.dart"
        assert (
            expected_file.exists()
        ), f"Expected file not found:{expected_file}"  # noqa

        generated = expected_file.read_text()

        # Class must be exactly MyWidget
        assert "class MyWidget" in generated

        # Ensure StatelessWidget structure exists
        assert "extends StatelessWidget" in generated

        # Ensure import exists
        assert "import 'package:flutter/material.dart';" in generated

        # Ensure no markdown or irrelevant wrapper text is present
        assert "```" not in generated
        assert "<html>" not in generated
        assert "# " not in generated

    finally:
        # Restore working directory
        os.chdir(cwd)


def test_cli_gen_widget_offline_fallback(tmp_path, monkeypatch):
    (tmp_path / "pubspec.yaml").write_text("name: test")
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)

    cwd = os.getcwd()
    os.chdir(tmp_path)

    try:
        result = test_main(["gen", "widget", "OfflineWidget"])
        assert result == 0

        out_file = tmp_path / "lib/widgets/offline_widget.dart"
        assert out_file.exists()

        code = out_file.read_text()
        assert "class OfflineWidget" in code
        assert "SizedBox.shrink" in code
        assert "Follow lint rules" not in code
    finally:
        os.chdir(cwd)


def test_cli_gen_widget_stateful_offline(tmp_path, monkeypatch):
    (tmp_path / "pubspec.yaml").write_text("name: test")
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)

    cwd = os.getcwd()
    os.chdir(tmp_path)

    try:
        result = test_main(["gen", "widget", "Counter", "--stateful"])
        assert result == 0

        code = (tmp_path / "lib/widgets/counter.dart").read_text()

        assert "StatefulWidget" in code
        assert "_CounterState" in code
    finally:
        os.chdir(cwd)


def test_cli_gen_model_offline(tmp_path, monkeypatch):
    (tmp_path / "pubspec.yaml").write_text("name: test")
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)

    cwd = os.getcwd()
    os.chdir(tmp_path)

    try:
        result = test_main(["gen", "model", "User"])
        assert result == 0

        code = (tmp_path / "lib/models/user.dart").read_text()

        assert "class User" in code
        assert "fromJson" in code
        assert "toJson" in code
    finally:
        os.chdir(cwd)


def test_cli_gen_repository_offline(tmp_path, monkeypatch):
    (tmp_path / "pubspec.yaml").write_text("name: test")
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)

    cwd = os.getcwd()
    os.chdir(tmp_path)

    try:
        result = test_main(
            ["gen", "repository", "UserRepository", "--entity", "User"],
        )

        assert result == 0

        out_file = tmp_path / "lib" / "repositories" / "user_repository.dart"
        assert out_file.exists()

        code = out_file.read_text()

        # Core expectations
        class_in_code = "class UserRepository" in "code"
        abstract_in_code = "abstract class UserRepository" in code

        assert class_in_code or abstract_in_code

        assert "User" in code  # entity should appear somewhere
        assert "```" not in code
        assert "<html>" not in code

    finally:
        os.chdir(cwd)


def test_cli_gen_enum_offline(tmp_path, monkeypatch):
    (tmp_path / "pubspec.yaml").write_text("name: test")
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)

    cwd = os.getcwd()
    os.chdir(tmp_path)

    try:
        result = test_main(["gen", "enum", "OrderStatus"])
        assert result == 0

        out_file = tmp_path / "lib" / "enums" / "order_status.dart"
        assert out_file.exists()

        code = out_file.read_text()

        # Core expectations
        assert "enum OrderStatus" in code
        assert "```" not in code
        assert "<html>" not in code
        assert "class OrderStatus" not in code  # must be enum

    finally:
        os.chdir(cwd)
