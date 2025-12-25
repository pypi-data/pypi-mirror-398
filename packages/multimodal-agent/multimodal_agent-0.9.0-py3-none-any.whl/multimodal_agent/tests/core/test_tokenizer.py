import pytest

from multimodal_agent.core.tokenizer import (
    estimate_token_count,
    split_into_chunks,
)


def test_token_count_basic():
    assert estimate_token_count("hello") >= 1
    assert estimate_token_count("a" * 40) >= 10


def test_token_count_empty():
    assert estimate_token_count("") == 0
    assert estimate_token_count(None) == 0


def test_chunk_short_text():
    assert split_into_chunks("hello world", max_tokens=50) == ["hello world"]


def test_chunk_empty():
    assert split_into_chunks("") == [""]
    assert split_into_chunks("   ") == [""]


def test_chunk_non_string_numeric():
    assert split_into_chunks(123) == ["123"]


def test_chunk_invalid_type():
    with pytest.raises(TypeError):
        split_into_chunks({"a": 1})


def test_chunk_sentence_splitting():
    text = "This is the first. This is the second. And this is the third."
    chunks = split_into_chunks(text, max_tokens=5)
    assert len(chunks) > 1


def test_chunk_word_based_mode():
    text = "This is a sentence without punctuation"
    chunks = split_into_chunks(text, max_tokens=3, preserve_sentences=False)
    assert len(chunks) > 1


def test_chunk_token_limit_respected():
    # Large text
    text = "word " * 200
    chunks = split_into_chunks(text, max_tokens=20)
    for chunk in chunks:
        assert estimate_token_count(chunk) <= 20


def test_chunk_order_stable():
    text = "A. B. C. D. E."
    chunks = split_into_chunks(text, max_tokens=2)
    # reconstruct
    reconstructed = " ".join(chunks)
    # removing double spaces to normalize
    assert reconstructed.replace("  ", " ") == text.replace("  ", " ")
