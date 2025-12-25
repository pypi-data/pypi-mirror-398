import json


def print_markdown_with_meta(
    sections: list[tuple[str, str]],
    meta: dict | None = None,
) -> None:
    """
    Print markdown-formatted sections, then optionally a JSON metadata block.

    sections: list of (title, body) pairs.
    meta: optional dict with machine-readable metadata for tools.
    """
    first = True
    for title, body in sections:
        if not first:
            # print blank line between sections.
            print()
        first = False

        print(f"## {title}\n")
        print(body if body else "(none)")

    if meta is not None:
        print()
        print(json.dumps(meta))
