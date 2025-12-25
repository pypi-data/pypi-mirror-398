import os
import re
from pathlib import Path
from typing import Optional

from multimodal_agent.codegen.enum_template import (
    build_enum_fallback,
    build_enum_prompt,
)
from multimodal_agent.codegen.model_template import (
    build_model_fallback,
    build_model_prompt,
)
from multimodal_agent.codegen.repository_template import (
    build_repository_fallback,
    build_repository_prompt,
)
from multimodal_agent.codegen.screen_template import (
    build_screen_fallback,
    build_screen_prompt,
)
from multimodal_agent.codegen.utils import sanitize_class_name
from multimodal_agent.codegen.widget_template import (
    build_widget_fallback,
    build_widget_prompt,
)
from multimodal_agent.config import get_config


class CodegenEngine:
    """
    v0.9.0 Core engine for generating Flutter code using the agent.

    Responsibilities:
    - Detect Flutter project root (contains pubspec.yaml)
    - Construct prompt templates
    - Call the agent to generate code
    - Extract clean Dart code from response
    - Write files safely (prevent overwrites unless override=True)
    """

    def __init__(self, model: Optional[str] = None):
        engine_config = get_config()
        self.model = model or engine_config["chat_model"]

    # Project Root Detection
    def detect_project_root(self, start_path: str | Path) -> Path:
        """
        Walk upward from the start_path until a pubspec.yaml is found.
        Returns the directory containing pubspec.yaml.

        Raises FileNotFoundError if no project root is found.
        """

        path = Path(start_path).resolve()

        if path.is_file():
            path = path.parent

        while True:
            if (path / "pubspec.yaml").exists():
                return path
            # reach the filesystem root
            if path.parent == path:
                break
            path = path.parent
        raise FileNotFoundError(
            "Could not find pubspec.yaml in any parent directory."
        )  # noqa

    # File writing.
    def safe_write(
        self,
        file_path: Path,
        content: str,
        override: bool = False,
    ):
        """
        Write generated code to the file system.
        Prevents accidental overwrites unless override=True.
        """
        if file_path.exists() and not override:
            raise FileExistsError(
                f"File {file_path} already exists. Use override=True to overwrite."  # noqa
            )
        file_path.parent.mkdir(parents=True, exist_ok=True)
        # write.
        with open(file_path, "w", encoding="utf-8") as file:
            file.write(content)

        return file_path

    # Code Extraction
    def extract_code(self, raw_text: str) -> str:
        """
        Given LLM output, extract code from ```dart ... ``` or ``` ... ```.
        If no code fences exist, return raw text unchanged.
        """
        if "```" not in raw_text:
            return raw_text.strip()

        parts = raw_text.split("```")
        if len(parts) < 3:
            return raw_text.strip()

        code_block = parts[1]
        first_newline = code_block.find("\n")

        if first_newline != -1:
            first_line = code_block[:first_newline].strip()
            if first_line.lower() in ("dart", "language", "code"):
                code_block = code_block[first_newline + 1 :]  # noqa

        return code_block.strip()

    def validate_and_clean(
        self,
        code: str,
        expected_class: str,
        kind: str,
    ) -> str:
        """
        Final cleanup + validation to ensure output is safe Dart code.
        """
        if not code or not code.strip():
            raise ValueError("Generated code is empty.")

        text = code.strip()

        # Remove markdown fences if they escaped extract_code()
        text = text.replace("```dart", "").replace("```", "").strip()

        # Remove accidental leading commentary from LLM
        # Keep only the part starting with 'class' or 'import'
        lines = text.splitlines()
        cleaned = []

        passed_header = False
        for line in lines:
            if line.strip().startswith(("class ", "import ", "enum ")):
                passed_header = True
            if passed_header:
                cleaned.append(line)

        text = "\n".join(cleaned).strip() or text

        # Ensure class name exists
        if kind in {"widget", "screen", "model", "repository"}:
            if f"class {expected_class}" not in text:
                raise ValueError(
                    f"Generated code does not contain class `{expected_class}`."  # noqa
                )
        if kind == "enum":
            if f"enum {expected_class}" not in text:
                raise ValueError(
                    f"Generated code does not contain enum `{expected_class}`."
                )

        # Deduplicate imports
        lines = text.splitlines()
        seen = set()
        unique_lines = []
        for line in lines:
            if line.strip().startswith("import "):
                if line not in seen:
                    seen.add(line)
                    unique_lines.append(line)
                continue
            unique_lines.append(line)

        text = "\n".join(unique_lines)

        # Normalize whitespace
        while "\n\n\n" in text:
            text = text.replace("\n\n\n", "\n\n")

        return text.strip()

    # Invoke the agent
    def run(self, prompt: str, response_format="text") -> str:
        from multimodal_agent import MultiModalAgent

        agent = MultiModalAgent(model=self.model)

        response = agent.ask(prompt, response_format=response_format)

        if not hasattr(response, "text"):
            raise RuntimeError("Model did not return text output")

        return self.extract_code(response.text)

    # Orchestrators for CLI
    def generate_and_write(
        self,
        kind: str,
        name: str,
        root: str | Path,
        override: bool = False,
        stateful: bool = False,
        description: str = "",
        entity: str | None = None,
        values: list[str] | None = None,
    ) -> Path:
        """
        Determine output path, call generation, write file.
        """

        root_path = self.detect_project_root(root)
        class_name = sanitize_class_name(name)
        snake_case = re.sub(r"(?<!^)([A-Z])", r"_\1", class_name).lower()

        if kind == "widget":
            out_path = root_path / "lib" / "widgets" / f"{snake_case}.dart"
            if self.is_offline_mode():
                content = self.generate_fallback_code(
                    kind=kind,
                    class_name=class_name,
                    stateful=stateful,
                )
            else:
                content = self.generate_widget(
                    name,
                    stateful=stateful,
                    description=description,
                )
                content = self.ensure_material_import(content)
        elif kind == "screen":
            out_path = (
                root_path / "lib" / "screens" / f"{snake_case}_screen.dart"
            )  # noqa
            if self.is_offline_mode():
                content = self.generate_fallback_code(
                    kind=kind,
                    class_name=class_name,
                )
            else:
                content = self.generate_screen(name, description=description)
                content = self.ensure_material_import(content)

        elif kind == "model":
            out_path = root_path / "lib" / "models" / f"{snake_case}.dart"
            if self.is_offline_mode():
                content = self.generate_fallback_code(
                    kind=kind,
                    class_name=class_name,
                )

            else:
                content = self.generate_model(name, description=description)

        elif kind == "enum":
            out_path = root_path / "lib" / "enums" / f"{snake_case}.dart"
            if self.is_offline_mode():
                content = self.generate_fallback_code(
                    kind=kind,
                    class_name=class_name,
                    values=values,
                )
            else:
                content = self.generate_enum(
                    name,
                    description=description,
                    values=values,
                )

        elif kind == "repository":
            out_path = root_path / "lib" / "repositories" / f"{snake_case}.dart"  # noqa

            if self.is_offline_mode():
                content = self.generate_fallback_code(
                    kind=kind,
                    class_name=class_name,
                    entity=entity,
                )
            else:
                content = self.generate_repository(
                    name,
                    description=description,
                    entity=entity,
                )

        else:
            raise ValueError(f"Unknown generation type: {kind}")

        cleaned = self.validate_and_clean(content, class_name, kind=kind)

        return self.safe_write(out_path, cleaned, override=override)

    def ensure_material_import(self, code: str) -> str:
        """
        Ensures the generated Dart code includes:
        import 'package:flutter/material.dart';
        Adds it at the top if missing.
        Avoids duplicates.
        """
        import_line = "import 'package:flutter/material.dart';"

        # If already imported → return as-is
        if import_line in code:
            return code

        # If file starts with imports → insert before the first non-import line
        lines = code.splitlines()
        insert_at = 0

        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith("import "):
                insert_at = i + 1
                continue
            # Stop at the first non-import line
            break

        new_lines = lines[:insert_at] + [import_line, ""] + lines[insert_at:]
        return "\n".join(new_lines)

    def is_offline_mode(self) -> bool:
        """
        Offline mode = no real API key available.
        """
        config = get_config()
        key = os.environ.get("GOOGLE_API_KEY") or config.get("api_key")
        return not key

    def generate_fallback_code(
        self,
        kind: str,
        class_name: str,
        stateful: bool = False,
        entity: str | None = None,
        values: list[str] | None = None,
    ) -> str:
        class_name = sanitize_class_name(class_name)
        if kind == "widget":
            return build_widget_fallback(
                class_name,
                stateful=stateful,
            )

        if kind == "screen":
            return build_screen_fallback(class_name)

        if kind == "model":
            return build_model_fallback(class_name)

        if kind == "enum":
            return build_enum_fallback(class_name, values=values)

        if kind == "repository":
            return build_repository_fallback(class_name, entity=entity)

        raise ValueError(f"Unknown generation type: {kind}")

    def generate_widget(
        self,
        name: str,
        stateful=False,
        description: str = "",
    ) -> str:
        class_name = sanitize_class_name(name)
        content = self.run(
            build_widget_prompt(
                class_name,
                stateful=stateful,
                description=description,
            )
        )
        return content

    def generate_screen(self, name: str, description: str = "") -> str:
        class_name = sanitize_class_name(name)
        content = self.run(
            build_screen_prompt(
                class_name,
                description=description,
            )
        )
        return content

    def generate_model(self, name: str, description: str = "") -> str:
        class_name = sanitize_class_name(name)
        content = self.run(
            build_model_prompt(
                class_name,
                description=description,
            )
        )
        return content

    def generate_enum(
        self,
        name: str,
        description: str = "",
        values: list[str] | None = None,
    ) -> str:
        class_name = sanitize_class_name(name)
        content = self.run(
            build_enum_prompt(
                class_name,
                values=values,
                description=description,
            )
        )
        return content

    def generate_repository(
        self, name: str, description: str = "", entity: Optional[str] = None
    ) -> str:
        class_name = sanitize_class_name(name)
        content = self.run(
            build_repository_prompt(
                class_name,
                entity=entity,
                description=description,
            )
        )
        return content
