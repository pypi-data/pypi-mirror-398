from .core.agent_core import MultiModalAgent
from .rag.rag_store import SQLiteRAGStore
from .version import __version__


# Lazy imports to avoid circular dependencies
def __getattr__(name):
    """
    Lazily expose MultiModalAgent and SQLiteRAGStore
    to avoid circular imports during CLI initialization.
    """
    if name == "MultiModalAgent":
        return MultiModalAgent

    if name == "SQLiteRAGStore":
        return SQLiteRAGStore

    raise AttributeError(name)


__all__ = [
    "MultiModalAgent",
    "SQLiteRAGStore",
    "__version__",
]
