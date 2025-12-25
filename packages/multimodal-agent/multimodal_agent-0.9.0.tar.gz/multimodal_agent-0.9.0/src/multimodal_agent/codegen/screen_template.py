from textwrap import dedent

from multimodal_agent.codegen.utils import sanitize_class_name


def build_screen_prompt(
    raw_name: str,
    description: str = "",
) -> str:
    class_name = sanitize_class_name(raw_name)

    extra_description = ""
    if description.strip():
        extra_description = (
            "\n    Additional UI description from user:\n"
            f"    - {description.strip()}\n"
        )

    prompt = f"""
    You are an expert Flutter developer following official Flutter documentation and Flutter lints.

    Task:
    - Generate a Flutter screen widget named `{class_name}` (input: '{raw_name}').
    - Output MUST be ONLY valid Dart code. 
    - Do NOT include markdown fences, explanations, comments, or text before/after the code.

    Requirements:
    - The screen MUST be a `StatelessWidget`.
    - Class name MUST be `{class_name}`.
    - MUST include:
        import 'package:flutter/material.dart';
    - Use idiomatic Flutter patterns and lint rules:
        - const constructors
        - const widgets where possible
        - final for fields
        - no unused imports
        - readable layout

    UI Requirements:
    - Use a Scaffold with:
        - an AppBar (title uses the class name)
        - a simple, centered body layout
    - Code MUST compile in a fresh Flutter project.{extra_description}

    Output:
    Your entire output MUST be a single Dart file defining exactly one class named `{class_name}`.
    No comments, no markdown, no explanations. ONLY the Dart code.
    """  # noqa

    return dedent(prompt).strip()


def build_screen_fallback(raw_name: str) -> str:
    class_name = sanitize_class_name(raw_name)
    return f"""import 'package:flutter/material.dart';

class {class_name} extends StatelessWidget {{
  const {class_name}({{super.key}});

  @override
  Widget build(BuildContext context) {{
    return const Scaffold(
      body: Center(child: Text('{class_name}')),
    );
  }}
}}
"""
