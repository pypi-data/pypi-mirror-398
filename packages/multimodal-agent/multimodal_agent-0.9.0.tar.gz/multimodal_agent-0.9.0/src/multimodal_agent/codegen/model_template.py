from textwrap import dedent

from multimodal_agent.codegen.utils import sanitize_class_name


def build_model_prompt(
    raw_name: str,
    description: str = "",
) -> str:
    class_name = sanitize_class_name(raw_name)

    extra_description = ""
    if description.strip():
        extra_description = (
            "\n    Additional model description from user"
            " (fields, purpose, etc.):\n"
            f"    - {description.strip()}\n"
        )

    prompt = f"""
    You are an expert Dart developer following Effective Dart and official Flutter lints.

    Task:
    - Generate a Dart model class named `{class_name}` (input: '{raw_name}').
    - Output MUST be ONLY valid Dart code.
    - Do NOT include markdown fences, comments, or explanations.

    Requirements:
    - Class name MUST be `{class_name}`.
    - Use:
        - final fields
        - const constructor
        - immutability
    - MUST include:
        - copyWith
        - factory {class_name}.fromJson(Map<String, dynamic>)
        - Map<String, dynamic> toJson()
        - @override String toString()

    Field Requirements:
    - Choose 3–5 realistic fields (String, int, bool, DateTime).
    - Use explicit types.
    - No extra imports unless needed (e.g., DateTime parsing).{extra_description}

    Lint Rules:
    - no unused imports
    - no unnecessary null checks
    - idiomatic formatting
    - const where possible

    Output:
    Your entire output MUST be a single Dart file defining exactly one class named `{class_name}`.
    No comments, no markdown, no explanations. ONLY the Dart code.
    """  # noqa

    return dedent(prompt).strip()


def build_model_fallback(raw_name: str) -> str:
    class_name = sanitize_class_name(raw_name)
    return f"""class {class_name} {{
  final String id;

  const {class_name}({{required this.id}});

  {class_name} copyWith({{String? id}}) {{
    return {class_name}(id: id ?? this.id);
  }}

  factory {class_name}.fromJson(Map<String, dynamic> json) {{
    return {class_name}(id: json['id'] as String);
  }}

  Map<String, dynamic> toJson() {{
    return {{'id': id}};
  }}

  @override
  String toString() => '{class_name}(id: $id)';
}}
"""
