import re
from textwrap import dedent
from typing import List, Optional

from multimodal_agent.codegen.utils import sanitize_class_name


def build_enum_prompt(
    raw_name: str,
    values: Optional[List[str]] = None,
    description: str = "",
) -> str:
    enum_name = sanitize_class_name(raw_name)

    values_part = ""
    if values:
        values_part = "\n".join([f"- {v}" for v in values])
    else:
        values_part = "- Choose 3–5 reasonable enum values"

    extra_description = ""
    if description.strip():
        extra_description = (
            "\nAdditional description from user:\n"
            f"- {description.strip()}\n"  # noqa
        )

    prompt = f"""
    You are an expert Dart developer following Effective Dart guidelines.

    Task:
    - Generate a Dart enum named `{enum_name}` (input: '{raw_name}').
    - Output MUST be ONLY valid Dart code.
    - Do NOT include markdown, comments, or explanations.

    Requirements:
    - Enum name MUST be `{enum_name}`.
    - Use lowerCamelCase enum values.
    - Keep values concise and meaningful.

    Enum Values:
    {values_part}{extra_description}

    Output:
    Your entire output MUST be a single Dart enum named `{enum_name}`.
    No comments, no markdown, no explanations. ONLY the Dart code.
    """  # noqa

    return dedent(prompt).strip()


def build_enum_fallback(raw_name: str, values: list[str] | None = None) -> str:
    enum_name = sanitize_class_name(raw_name)
    enum_values = values or ["value1", "value2", "value3"]
    enum_values = [sanitize_enum_value(v) for v in enum_values]

    joined = ",\n ".join(enum_values)
    return f"""enum {enum_name} {{
{joined}
}}
"""


def sanitize_enum_value(value: str) -> str:
    value = value.strip()
    value = re.sub(r"[^a-zA-Z0-9]", "_", value)
    value = value[0].lower() + value[1:]
    return value
