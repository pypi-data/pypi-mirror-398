import json
from pathlib import Path

# DEPRECATED JSON MEMORY (KEPT FOR BACKWARD COMPATIBILITY)
#
# NOTE: These methods are no longer used now that you have SQLite memory.
# They are kept for compatibility with old code but can be removed
# in a future cleanup release.


MEMORY_PATH = Path.home() / ".multimodal_agent_memory.json"


def append_memory(entry: str) -> None:
    """
    Deprecated: do not use anymore.
    Left for backward compatibility.
    """
    memory = load_memory()
    if not isinstance(memory, list):
        memory = []
    memory.append(entry)
    save_memory(memory=memory)


def delete_memory_index(index: int) -> bool:
    """
    Deprecated: do not use anymore.
    Left for backward compatibility.
    """
    memory = load_memory()
    if index < 0 or index >= len(memory):
        return False
    memory.pop(index)
    save_memory(memory=memory)
    return True


def reset_memory() -> None:
    save_memory([])


def load_memory() -> list[str]:
    """
    Deprecated: do not use anymore.
    Left for backward compatibility.
    """
    if not MEMORY_PATH.exists():
        return []
    try:
        with open(MEMORY_PATH, "r") as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except Exception:
        return []


def save_memory(memory: list[str]) -> None:
    """
    Deprecated: do not use anymore.
    Left for backward compatibility.
    """
    MEMORY_PATH.write_text(json.dumps(memory, indent=2))
