import pytest

from multimodal_agent.errors import InvalidImageError
from multimodal_agent.utils import (  # noqa
    load_image_as_part,
    load_image_from_url_as_part,
)


def test_load_image_as_part_valid_png(tmp_path, monkeypatch):
    img = tmp_path / "test.png"
    img.write_bytes(b"fake-png-data")

    class FakeImage:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            pass

        def tobytes(self):
            return b"image-bytes"

    def fake_open(path):
        assert path == img
        return FakeImage()

    monkeypatch.setattr("multimodal_agent.utils.Image.open", fake_open)

    part = load_image_as_part(str(img))
    assert part.inline_data.mime_type == "image/png"
    assert part.inline_data.data == b"image-bytes"


def test_load_image_as_part_missing(tmp_path):
    with pytest.raises(InvalidImageError):
        load_image_as_part(tmp_path / "missing.png")


def test_load_image_as_part_unsupported(tmp_path):
    bad = tmp_path / "test.bmp"
    bad.write_bytes(b"123")
    with pytest.raises(InvalidImageError):
        load_image_as_part(bad)


def test_load_image_from_url_as_part(monkeypatch):
    class FakeResponse:
        content = b"fake image bytes"

        def raise_for_status(self):
            pass

    monkeypatch.setattr("requests.get", lambda url: FakeResponse())

    part = load_image_from_url_as_part("http://example.com/img.jpg")

    assert part.inline_data.data == b"fake image bytes"
    assert part.inline_data.mime_type == "image/jpeg"
