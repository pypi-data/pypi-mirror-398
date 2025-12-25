import json
import re
import xml.dom.minidom
from typing import Literal

ContentType = Literal["json", "code", "xml", "html", "plain"]


def format_output(text: str) -> str:
    """
    Main entry point: detect → format.
    """
    # Handle None safely
    if text is None:
        return ""

    # enforce string
    if not isinstance(text, str):
        text = str(text)

    content_type = detect_content_type(text)

    if content_type == "json":
        return format_json(text)

    elif content_type == "code":
        language = detect_language(text)
        return f"```{language}\n{text.strip()}\n```"

    elif content_type in ("xml", "html"):
        return format_xml_html(text)
    else:
        return format_plain(text)


def detect_content_type(text: str) -> ContentType:
    """
    Very lightweight content-type detection.
    """
    if not text or not isinstance(text, str):
        return "plain"

    stripped = text.strip()

    # json
    if (stripped.startswith("{") and stripped.endswith("}")) or (
        stripped.startswith("[") and stripped.endswith("]")
    ):
        try:
            json.loads(stripped)
            return "json"
        except Exception:
            pass

    # Markdown fenced code ```
    if stripped.startswith("```"):
        return "code"

    # Code-like heuristics
    if any(sym in stripped for sym in ("=", "(", ")", "{", "}", "->")):
        return "code"

    # XML / HTML
    if stripped.startswith("<") and stripped.endswith(">"):
        tags = re.findall(r"</?([a-zA-Z0-9]+)", stripped)
        if tags:
            t = tags[0].lower()
            if t in ("html", "body", "div", "head"):
                return "html"
            return "xml"

    return "plain"


def detect_language(text: str) -> str:
    lower = text.lower()
    stripped = text.strip()

    # json
    if stripped.startswith("{") and stripped.endswith("}"):
        try:
            json.loads(stripped)
            return "json"
        except Exception:
            pass

    # objective-c
    if (
        "@interface" in text
        or "@implementation" in text
        or "@end" in text
        or re.search(r"@property\s*\(", text)
        or re.search(r"\[[A-Za-z_]\w*\s+[A-Za-z_]\w*", text)
        or ("#import" in lower and ".h" in lower)
    ):
        return "objectivec"

    # kotlin
    if (
        # functions
        re.search(r"\bfun\s+\w+", text)
        or "suspend fun" in lower
        or
        # kotlin val (Swift does not have "val")
        re.search(r"\bval\s+\w+", text)
        or
        # Kotlin coroutines / kotlinx imports
        "import kotlinx" in lower
        or "kotlin.coroutines" in lower
    ):
        return "kotlin"

    # swift
    if (
        # Swift function syntax
        re.search(r"\bfunc\s+\w+\s*\(", text)
        or
        # Swift "let"
        re.search(r"\blet\s+\w+", text)
        or
        # Swift imports
        "import foundation" in lower
        or "import swiftui" in lower
        or
        # Swift var but ONLY if no Kotlin patterns appear
        (
            re.search(r"\bvar\s+\w+", text)
            and "fun " not in lower
            and "suspend fun" not in lower
            and "kotlin" not in lower
            and not re.search(r"\bval\s+\w+", text)
        )
    ):
        return "swift"

    # dart
    if (
        "import 'package:" in text
        or "void main()" in text
        or "@override" in text
        or re.search(r"class\s+\w+\s+extends\s+\w+", text)
    ):
        return "dart"

    # JS / TS
    if (
        "console.log" in lower
        or "function " in lower
        or "export default" in lower
        or "import {" in text
        or "import * as" in lower
        or re.search(r"\bconst\s+\w+", text)
        or re.search(r"\blet\s+\w+", text)
    ):
        return "javascript"

    # java
    if (
        "public class" in text
        or "public static void main" in lower
        or "import java." in lower
        or re.search(r"^package\s+[a-zA-Z_]\w*", lower, re.MULTILINE)
    ):
        return "java"

    # C++
    if (
        "#include" in lower
        or re.search(r"\bstd::\w+", text)
        or re.search(r"class\s+\w+\s*\{", text)
        or "template <" in text
    ):
        if "system.out" not in lower:  # avoid java collision
            return "cpp"

    # python
    if re.search(r"^\s*def\s+\w+\(", text, re.MULTILINE) or re.search(
        r"^\s*class\s+\w+\s*[:\(]", text, re.MULTILINE
    ):
        return "python"

    # python import rule must be last & strict
    if (
        "import " in lower
        and "package:" not in lower
        and "java." not in lower
        and "kotlinx" not in lower
        and "react" not in lower  # JS import
    ):
        return "python"

    return "plain"


def format_json(text: str) -> str:
    """
    Beautify JSON safely according to test expectations.
    Tests require raw pretty-printed JSON (no code fences).
    """
    try:
        parsed = json.loads(text)
        pretty = json.dumps(parsed, indent=2, ensure_ascii=False)
        return pretty
    except Exception:
        # If it’s invalid JSON, return raw text unchanged
        return text.strip()


def guess_code_language(text: str) -> str:
    """
    Very simple heuristic for code language annotation.
    """
    if "class " in text and "{" in text and "}" in text:
        return "dart"
    if "def " in text or "import " in text:
        return "python"
    return ""  # unknown


def format_code(text: str) -> str:
    """
    Wraps code in triple-backticks and annotates language if possible.
    """
    lang = guess_code_language(text)
    lang_prefix = f"{lang}" if lang else ""

    # strip existing ticks if present
    stripped = text.strip().removeprefix("```").removesuffix("```")

    return f"```{lang_prefix}\n{stripped}\n```"


def format_xml_html(text: str) -> str:
    """
    Pretty-print XML/HTML if possible.
    """
    try:
        dom = xml.dom.minidom.parseString(text)
        return dom.toprettyxml(indent="  ")
    except Exception:
        return text


def format_plain(text: str) -> str:
    """
    Normalize whitespace for plain text output.
    """
    # collapse excessive blank lines
    formatted = re.sub(r"\n\s*\n\s*\n+", "\n\n", text)
    return formatted.strip()
