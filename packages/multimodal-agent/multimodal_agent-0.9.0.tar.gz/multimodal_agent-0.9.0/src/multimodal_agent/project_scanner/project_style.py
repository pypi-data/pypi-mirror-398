from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class LintRuleSet:
    """Represents lint configuration derived from analysis_options.yaml."""

    enabled_rules: List[str] = field(default_factory=list)
    excluded_files: List[str] = field(default_factory=list)
    max_line_length: Optional[int] = None
    raw_path: Optional[Path] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "enabled_rules": self.enabled_rules,
            "excluded_files": self.excluded_files,
            "max_line_length": self.max_line_length,
            "raw_path": str(self.raw_path) if self.raw_path else None,
        }


@dataclass
class ArchitectureInfo:
    """
    High-level view of detected architecture & state management.
    """

    # e.g. ["clean_architecture", "feature_first"]
    patterns: List[str] = field(default_factory=list)
    # e.g. ["bloc", "riverpod"]
    state_management: List[str] = field(default_factory=list)
    uses_build_runner: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ProjectStyleProfile:
    """
    Snapshot of a Flutter/Dart project style.

    This will later be used as context for code generation.
    """

    root: Path
    is_flutter_project: bool
    package_name: Optional[str]
    pubspec_path: Optional[Path]
    analysis_options_path: Optional[Path]

    architecture: ArchitectureInfo = field(default_factory=ArchitectureInfo)
    lint: LintRuleSet = field(default_factory=LintRuleSet)

    # Simple style hints – can be expanded later
    dart_files_count: int = 0
    widget_files_count: int = 0
    uses_freezed: bool = False
    uses_json_serializable: bool = False

    def to_dict(self) -> Dict[str, Any]:
        path = (
            (
                str(
                    self.analysis_options_path,
                )
                if self.analysis_options_path
                else None
            ),
        )
        return {
            "root": str(self.root),
            "is_flutter_project": self.is_flutter_project,
            "package_name": self.package_name,
            "pubspec_path": path,
            "analysis_options_path": path,
            "architecture": self.architecture.to_dict(),
            "lint": self.lint.to_dict(),
            "dart_files_count": self.dart_files_count,
            "widget_files_count": self.widget_files_count,
            "uses_freezed": self.uses_freezed,
            "uses_json_serializable": self.uses_json_serializable,
        }
