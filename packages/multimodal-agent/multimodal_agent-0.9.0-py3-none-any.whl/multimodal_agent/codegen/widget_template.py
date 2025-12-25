from textwrap import dedent

from multimodal_agent.codegen.utils import sanitize_class_name


def build_widget_prompt(
    raw_name: str,
    stateful: bool = False,
    description: str = "",
) -> str:
    class_name = sanitize_class_name(raw_name)
    widget_type = "StatefulWidget" if stateful else "StatelessWidget"

    extra_description = ""
    if description.strip():
        extra_description = (
            "\n    Additional UI description from user:\n"
            f"    - {description.strip()}\n"
        )

    prompt = f"""
    You are an expert Flutter developer following official Flutter documentation and Flutter lints.

    Task:
    - Generate a Flutter {widget_type} named `{class_name}` (input: '{raw_name}').
    - Output MUST be ONLY valid Dart code.
    - Do NOT include markdown fences, comments, explanation text, or any extra content.

    Requirements:
    - Class name MUST be exactly `{class_name}`.
    - MUST include:
        import 'package:flutter/material.dart';
    - Follow lint rules:
        - const constructors where possible
        - const widgets where appropriate
        - no unused imports
        - idiomatic formatting
        - prefer final fields

    StatefulWidget Structure (MANDATORY if stateful=True):
        class {class_name} extends StatefulWidget {{
          const {class_name}({{ super.key }});

          @override
          State<{class_name}> createState() => _{class_name}State();
        }}

        class _{class_name}State extends State<{class_name}> {{
          @override
          Widget build(BuildContext context) {{
            // widget UI
          }}
        }}

    Stateless Structure (MANDATORY if stateful=False):
        class {class_name} extends StatelessWidget {{
          const {class_name}({{ super.key }});

          @override
          Widget build(BuildContext context) {{
            // widget UI
          }}
        }}

    UI Requirements:
    - Build a small reusable widget (padding, text, etc.).
    - Code MUST compile in a new Flutter project without modification.{extra_description}

    Output:
    Your entire output MUST be a single Dart file defining exactly one class named `{class_name}`.
    No comments, no markdown, no text before/after the class. ONLY the Dart code.
    """  # noqa

    return dedent(prompt).strip()


def build_widget_fallback(raw_name: str, stateful=False) -> str:
    class_name = sanitize_class_name(raw_name)
    if stateful:
        return f"""import 'package:flutter/material.dart';

class {class_name} extends StatefulWidget {{
  const {class_name}({{super.key}});

  @override
  State<{class_name}> createState() => _{class_name}State();
}}

class _{class_name}State extends State<{class_name}> {{
  @override
  Widget build(BuildContext context) {{
    return const SizedBox.shrink();
  }}
}}
"""
    else:
        return f"""import 'package:flutter/material.dart';

class {class_name} extends StatelessWidget {{
  const {class_name}({{super.key}});

  @override
  Widget build(BuildContext context) {{
    return const SizedBox.shrink();
  }}
}}
"""
