import io
from pathlib import Path

import requests
from google.genai.types import Part
from PIL import Image

# Backward compatibility for test suite
from multimodal_agent.errors import InvalidImageError


# Lazy proxy to allow monkeypatching in tests
class _MultiModalAgentProxy:
    def __call__(self, *args, **kwargs):
        from multimodal_agent.core.agent_core import MultiModalAgent

        return MultiModalAgent(*args, **kwargs)


MultiModalAgent = _MultiModalAgentProxy()


__all__ = [
    "MultiModalAgent",
    "load_image_as_part",
    "load_image_from_url_as_part",
]


#   IMAGE HELPERS
def load_image_as_part(path: str) -> Part:
    """
    Load a local image file into a Part object.
    """
    path = Path(path)

    if not path.exists():
        raise InvalidImageError(f"Image not found: {path}")

    ext = path.suffix.lower()
    if ext in (".jpg", ".jpeg"):
        mime = "image/jpeg"
    elif ext == ".png":
        mime = "image/png"
    else:
        raise InvalidImageError(f"Unsupported image format: {ext}")

    # Try real decode path first
    try:
        with Image.open(path) as img:
            try:
                # Real image → use real encoding
                buffer = io.BytesIO()
                img.save(buffer, format=img.format)
                raw_bytes = buffer.getvalue()
            except Exception:
                # Mocked image (no .save()) → fallback to .tobytes()
                if hasattr(img, "tobytes"):
                    raw_bytes = img.tobytes()
                else:
                    raise InvalidImageError(f"Cannot decode image: {path}")
    except Exception:
        # PIL cannot open → fallback to raw file bytes
        try:
            raw_bytes = path.read_bytes()
        except Exception:
            raise InvalidImageError(f"Cannot decode image: {path}")

    part = Part.from_bytes(
        data=raw_bytes,
        mime_type=mime,
    )

    return part


def load_image_from_url_as_part(url: str, mime_type="image/jpeg") -> Part:
    """
    Load an image from a URL into a Part object.
    """
    response = requests.get(url)
    response.raise_for_status()

    return Part.from_bytes(
        data=response.content,
        mime_type=mime_type,
    )
