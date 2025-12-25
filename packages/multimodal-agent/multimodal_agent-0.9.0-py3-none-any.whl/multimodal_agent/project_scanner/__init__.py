from .ingest import ingest_style_into_rag
from .scanner import ProjectScanner
from .style_profile import extract_style_profile

__all__ = ["scan_project", "extract_style_profile", "ingest_style_into_rag"]


def scan_project(path: str):
    return ProjectScanner().scan_project(path)
