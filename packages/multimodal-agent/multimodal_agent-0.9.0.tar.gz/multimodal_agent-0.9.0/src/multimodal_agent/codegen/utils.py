import re
import subprocess
from pathlib import Path


class CodegenError(Exception):
    pass


def find_flutter_root(start: str | Path) -> Path:
    """
    Walk up from `start` until we find a directory containing:
      - pubspec.yaml
      - lib/
    """
    current = Path(start).resolve()

    for _ in range(20):
        pubspec = current / "pubspec.yaml"
        lib_dir = current / "lib"
        if pubspec.exists() and lib_dir.exists():
            return current
        if current.parent == current:
            break
        current = current.parent

    raise CodegenError(
        "Could not locate Flutter project root. "
        "Make sure you run this inside a Flutter project (with pubspec.yaml and lib/)."  # noqa
    )


# Widget path helper.
def widget_file_path(root: Path, name: str) -> Path:
    """
    lib/widgets/my_widget.dart
    """
    snake = to_snake_case(name)
    return root / "lib" / "widgets" / f"{snake}.dart"


# Screen path helper.
def screen_file_path(root: Path, name: str) -> Path:
    """
    lib/screens/my_screen.dart
    """
    snake = to_snake_case(name)
    return root / "lib" / "screens" / f"{snake}.dart"


# Model path helper.
def model_file_path(root: Path, name: str) -> Path:
    """
    lib/models/my_model.dart
    """
    snake = to_snake_case(name)
    return root / "lib" / "models" / f"{snake}.dart"


# FILE WRITE + dart format
def safe_write_file(
    path: Path,
    content: str,
    override: bool = False,
    run_format: bool = True,
):
    """
    Write to a file in a safe way:
      - Create parent dirs
      - Refuse overwrite unless override=True
      - Optionally run `dart format` afterwards
    """
    path = Path(path)

    if path.exists() and not override:
        raise CodegenError(
            f"File already exists: {path}. Use --override to overwrite."
        )  # noqa

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")

    if run_format and path.suffix == ".dart":
        format_dart_file(path)


def sanitize_class_name(name: str) -> str:
    """
    Convert any input into a valid PascalCase Dart class name.
    Handles:
    - spaces / hyphens / symbols
    - CamelCase preservation
    - numeric-leading names (prefix W)
    - fallback to GeneratedWidget
    """

    if not name or not name.strip():
        return "GeneratedWidget"

    # Normalize separators into space
    cleaned = re.sub(r"[^A-Za-z0-9]+", " ", name).strip()

    if not cleaned:
        return "GeneratedWidget"

    parts = cleaned.split()

    # Capitalize each part (preserves existing CamelCase)
    capitalized = [p[0].upper() + p[1:] for p in parts if p]

    class_name = "".join(capitalized)

    # If still empty, fallback
    if not class_name:
        return "GeneratedWidget"

    # If starts with digit → prefix W
    if class_name[0].isdigit():
        class_name = "W" + class_name

    return class_name


def to_snake_case(name: str) -> str:
    """
    Rules:
    - CamelCase → collapse to lowercase (no underscores)
    - Spaces and hyphens → underscore
    - Remove other invalid characters
    """
    if not name:
        return ""

    # Normalize separators
    name = name.replace("-", " ").replace("_", " ")

    # Split camelCase / PascalCase boundaries
    name = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", name)

    # Split on spaces and join
    parts = re.split(r"\s+", name)

    # Join and clean
    snake = "_".join(parts).lower()

    # Only allow valid chars
    snake = re.sub(r"[^a-z0-9_]", "", snake)

    return snake


def format_dart_file(path: Path):
    """
    Best-effort `dart format` call. If dart is not installed or fails,
    we do not crash the generator.
    """
    try:
        subprocess.run(
            ["dart", "format", str(path)],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    # silent failure.
    except Exception:
        pass
