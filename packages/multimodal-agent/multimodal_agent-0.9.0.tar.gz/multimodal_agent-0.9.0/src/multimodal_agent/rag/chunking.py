from __future__ import annotations

import re
from typing import List

# Rough, conservative default:
# ~ 4 chars ≈ 1 token, so 800 chars ≈ 200 tokens.
DEFAULT_MAX_CHARS = 800

__all__ = [
    "chunk_text",
    "_split_paragraphs",
    "_split_sentences",
]


def chunk_text(
    text: str,
    max_chars: int = DEFAULT_MAX_CHARS,
) -> List[str]:
    """
    Split text into reasonably sized chunks.

    Strategy:
    - Split into paragraphs.
    - If a paragraph is too long, split into sentences.
    - Group sentences into windows up to max_chars.
    """

    text = text.strip()
    if not text:
        return []

    if len(text) <= max_chars:
        return [text]

    chunks: list[str] = []
    paragraphs = _split_paragraphs(text=text)

    for paragraph in paragraphs:
        if len(paragraph) <= max_chars:
            chunks.append(paragraph)
            continue

        sentences = _split_sentences(text=paragraph)
        # when we have one giant big sentence we break it to word level split.
        if len(sentences) == 1 and len(sentences[0]) > max_chars:
            chunks.extend(_split_long_string(sentences[0], max_chars))
            continue
        current = ""

        for s in sentences:
            if not current:
                current = s
                continue

            if len(current) + 1 + len(s) > max_chars:
                chunks.append(current)
                current = s
            else:
                current = current + " " + s

    result = [chunk for chunk in chunks if chunk.strip()] or [text]
    return result


def _split_paragraphs(text: str) -> List[str]:
    """
    Split text into paragraphs on double newlines.
    """
    parts = [p.strip() for p in text.split("\n\n")]
    return [p for p in parts if p]


def _split_sentences(text: str) -> List[str]:
    """
    Very lightweight sentence splitter (no heavy NLP deps).
    """
    # split text on .,?,!.
    sentence_end_re = re.compile(r"([.!?])")
    chunks: list[str] = []
    buffer = ""

    for piece in sentence_end_re.split(text):
        if not piece:
            continue
        buffer += piece

        if sentence_end_re.match(piece):
            sentence = buffer.strip()
            if sentence:
                chunks.append(sentence)
            buffer = ""

    if buffer.strip():
        chunks.append(buffer.strip())

    return chunks or [text]


def _split_long_string(sentence: str, max_chars: int) -> List[str]:
    """
    Split long text with no punctuation or giant tokens.
    Splits by whitespace, but also splits inside long words if needed.
    """
    words = sentence.split()
    if not words:
        return [sentence]

    chunks = []
    current = ""

    for word in words:
        # Word itself longer than max_chars → break inside the word
        if len(word) > max_chars:
            if current.strip():
                chunks.append(current.strip())
                current = ""

            # Split inside the long word
            for i in range(0, len(word), max_chars):
                split_word = word[i : i + max_chars]  # noqa
                chunks.append(split_word)
            continue

        if not current:
            current = word
        elif len(current) + 1 + len(word) > max_chars:
            chunks.append(current.strip())
            current = word
        else:
            current += " " + word

    if current.strip():
        chunks.append(current.strip())

    return chunks
