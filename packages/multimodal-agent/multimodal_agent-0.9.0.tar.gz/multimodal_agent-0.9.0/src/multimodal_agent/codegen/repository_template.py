from textwrap import dedent
from typing import Optional

from multimodal_agent.codegen.utils import sanitize_class_name


def build_repository_prompt(
    raw_name: str,
    entity: Optional[str] = None,
    description: str = "",
) -> str:
    repo_name = sanitize_class_name(raw_name)
    entity_name = sanitize_class_name(entity) if entity else "T"

    extra_description = ""
    if description.strip():
        extra_description = (
            "\nAdditional repository description from user:\n"
            f"- {description.strip()}\n"
        )

    prompt = f"""
    You are an expert Dart developer following Clean Architecture principles.

    Task:
    - Generate a Dart repository abstraction named `{repo_name}`.
    - Output MUST be ONLY valid Dart code.
    - Do NOT include markdown, comments, or explanations.

    Requirements:
    - Repository name MUST be `{repo_name}`.
    - Use generics or entity `{entity_name}`.
    - Prefer abstract class over implementation.
    - Use asynchronous methods (Future).

    Required Methods:
    - getAll
    - getById
    - save
    - delete{extra_description}

    Output:
    Your entire output MUST be a single Dart file defining exactly one
    abstract class `{repo_name}`.
    No comments, no markdown, no explanations. ONLY the Dart code.
    """  # noqa

    return dedent(prompt).strip()


def build_repository_fallback(
    raw_name: str,
    entity: Optional[str] = None,
) -> str:
    repo_name = sanitize_class_name(raw_name)
    entity_name = sanitize_class_name(entity) if entity else "T"

    return f"""abstract class {repo_name}<{entity_name}> {{
  Future<List<{entity_name}>> getAll();
  Future<{entity_name}?> getById(String id);
  Future<void> save({entity_name} entity);
  Future<void> delete(String id);
}}
"""
