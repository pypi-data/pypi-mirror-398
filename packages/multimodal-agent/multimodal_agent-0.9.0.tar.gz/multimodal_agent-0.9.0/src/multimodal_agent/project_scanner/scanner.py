from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable, Optional, Tuple

from .project_style import (
    ArchitectureInfo,
    LintRuleSet,
    ProjectStyleProfile,
)


class ProjectScanner:
    """
    Responsibilities:
      - Locate pubspec.yaml & analysis_options.yaml
      - Detect if it is a Flutter project
      - Heuristically detect architecture patterns
      - Detect state-management libraries
      - Parse basic lint rules (max line length, rules list)
      - Count Dart/widget files
      - Detect some popular tooling (freezed, json_serializable)
    """

    def __init__(self, max_files: int = 200) -> None:
        # Avoid scanning giant monorepos fully
        self.max_files = max_files

    def scan_project(self, path: str | Path) -> ProjectStyleProfile:
        """
        Convenience function: one-shot scanner.
        """
        scanner = ProjectScanner()
        return scanner.scan(path)

    def scan(self, root: str | Path) -> ProjectStyleProfile:
        root_path = Path(root).resolve()
        # obtain pubspec info.
        pubspec_path = self._find_pubspec(root_path)
        if pubspec_path:
            pubspec_text = pubspec_path.read_text(encoding="utf-8")
        else:
            pubspec_text = ""
        # obtain package name & flutter status
        package_name = (
            self._extract_package_name(pubspec_text) if pubspec_text else None
        )
        if pubspec_text:
            is_flutter_project = "flutter:" in pubspec_text
        else:
            is_flutter_project = False

        analysis_options_path = self._find_analysis_options(root_path)

        architecture = self._scan_architecture(root_path, pubspec_text)
        lint = (
            self._parse_lint_config(analysis_options_path)
            if analysis_options_path
            else LintRuleSet()
        )

        (
            dart_files_count,
            widget_files_count,
            uses_freezed,
            uses_json_serializable,
        ) = self._scan_dart_files(root_path)

        return ProjectStyleProfile(
            root=root_path,
            is_flutter_project=is_flutter_project,
            package_name=package_name,
            pubspec_path=pubspec_path,
            analysis_options_path=analysis_options_path,
            architecture=architecture,
            lint=lint,
            dart_files_count=dart_files_count,
            widget_files_count=widget_files_count,
            uses_freezed=uses_freezed,
            uses_json_serializable=uses_json_serializable,
        )

    # helper methods
    @staticmethod
    def _find_pubspec(root: Path) -> Optional[Path]:
        candidate = root / "pubspec.yaml"
        return candidate if candidate.exists() else None

    @staticmethod
    def _find_analysis_options(root: Path) -> Optional[Path]:
        # Most common locations
        for name in ("analysis_options.yaml", "analysis_options.yml"):
            candidate = root / name
            if candidate.exists():
                return candidate

        # Fallback: search up to a small depth
        for p in root.rglob("analysis_options.yaml"):
            return p
        for p in root.rglob("analysis_options.yml"):
            return p

        return None

    @staticmethod
    def _extract_package_name(pubspec_text: str) -> Optional[str]:
        # super simple heuristic – first "name:" at column 0
        for line in pubspec_text.splitlines():
            if line.startswith("name:"):
                _, value = line.split(":", 1)
                return value.strip()
        return None

    # architecture

    def _scan_architecture(
        self,
        root: Path,
        pubspec_text: str,
    ) -> ArchitectureInfo:

        patterns: list[str] = []
        state_management: list[str] = []

        lib_dir = root / "lib"
        if not lib_dir.exists():
            return ArchitectureInfo(
                patterns=patterns,
                state_management=state_management,
                uses_build_runner=False,
            )

        # Folder-based hints
        has_domain = (lib_dir / "domain").exists()
        has_data = (lib_dir / "data").exists()
        has_presentation = (lib_dir / "presentation").exists()
        is_architecture_clean = has_domain and has_data and has_presentation
        is_features_available = (lib_dir / "features").exists() or (
            (lib_dir / "src" / "features").exists(),
        )
        is_module_available = (lib_dir / "modules").exists()
        # clean architecture
        if is_architecture_clean:
            patterns.append("clean_architecture")
        # feature-first architecture
        if is_features_available:
            patterns.append("feature_first")
        # modular architecture
        if is_module_available:
            patterns.append("modular")

        # File-based hints
        if any(lib_dir.rglob("*_bloc.dart")):
            patterns.append("bloc_pattern")

        if any(lib_dir.rglob("*_state.dart")) and any(
            lib_dir.rglob("*_event.dart"),
        ):
            patterns.append("state_event_pattern")

        # Dependencies-based state management
        text = pubspec_text

        if "flutter_bloc:" in text or "bloc:" in text:
            state_management.append("bloc")
        if (
            "riverpod:" in text
            or "hooks_riverpod:" in text
            or "flutter_riverpod:" in text
        ):
            state_management.append("riverpod")
        if "provider:" in text:
            state_management.append("provider")
        if "mobx:" in text:
            state_management.append("mobx")
        if "get_it:" in text:
            state_management.append("get_it")
        if "redux:" in text:
            state_management.append("redux")

        uses_build_runner = "build_runner:" in text

        # Deduplicate while keeping order
        patterns = list(dict.fromkeys(patterns))
        state_management = list(dict.fromkeys(state_management))

        return ArchitectureInfo(
            patterns=patterns,
            state_management=state_management,
            uses_build_runner=uses_build_runner,
        )

    #  Lint parsing
    def _parse_lint_config(self, path: Path) -> LintRuleSet:
        text = path.read_text(encoding="utf-8")
        enabled_rules: list[str] = []
        excluded_files: list[str] = []
        max_line_length: Optional[int] = None

        lines = text.splitlines()

        # Very simple parser – good enough for most real-world files
        in_rules_block = False
        in_exclude_block = False

        for raw in lines:
            line = raw.rstrip()

            # max line length (common patterns)
            if "max_line_length" in line and ":" in line:
                try:
                    _, value = line.split(":", 1)
                    value = value.strip()
                    if value.isdigit():
                        max_line_length = int(value)
                except Exception:
                    pass

            # rules:
            if re.match(r"^\s*rules\s*:", line):
                in_rules_block = True
                in_exclude_block = False
                continue

            # analyzer:
            if re.match(r"^\s*analyzer\s*:", line):
                in_rules_block = False
                in_exclude_block = False
                continue

            # analyzer -> exclude:
            if re.match(r"^\s*exclude\s*:", line):
                in_exclude_block = True
                in_rules_block = False
                continue

            # inside rules block:
            if in_rules_block:
                m = re.match(r"^\s*-\s*([A-Za-z0-9_\.]+)\s*$", line)
                if m:
                    enabled_rules.append(m.group(1))

            # inside exclude block:
            if in_exclude_block:
                m = re.match(r"^\s*-\s*(.+?)\s*$", line)
                if m:
                    excluded_files.append(m.group(1))

        return LintRuleSet(
            enabled_rules=list(dict.fromkeys(enabled_rules)),
            excluded_files=excluded_files,
            max_line_length=max_line_length,
            raw_path=path,
        )

    # dart file scanning.

    def _iter_dart_files(self, root: Path) -> Iterable[Path]:
        lib = root / "lib"
        if not lib.exists():
            return []

        count = 0
        for path in lib.rglob("*.dart"):
            yield path
            count += 1
            if count >= self.max_files:
                break

    def _scan_dart_files(self, root: Path) -> Tuple[int, int, bool, bool]:
        dart_files_count = 0
        widget_files_count = 0
        uses_freezed = False
        uses_json_serializable = False

        widget_regex = re.compile(
            r"class\s+(\w+)\s+extends\s+(StatelessWidget|StatefulWidget)"
        )
        freezed_hint = re.compile(r"@freezed\b")
        json_ser_hint = re.compile(r"json_serializable|@JsonSerializable\b")

        for dart_path in self._iter_dart_files(root):
            dart_files_count += 1
            try:
                text = dart_path.read_text(encoding="utf-8")
            except Exception:
                continue

            if widget_regex.search(text):
                widget_files_count += 1

            if freezed_hint.search(text):
                uses_freezed = True

            if json_ser_hint.search(text):
                uses_json_serializable = True

        return (
            dart_files_count,
            widget_files_count,
            uses_freezed,
            uses_json_serializable,
        )
