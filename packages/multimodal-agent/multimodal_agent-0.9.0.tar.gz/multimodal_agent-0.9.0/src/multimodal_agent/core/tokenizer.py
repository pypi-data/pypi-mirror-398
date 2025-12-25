import re
from typing import List


def estimate_token_count(text: str) -> int:
    """
    Estimate token count using a lightweight heuristic:
    ~ 4 characters ≈ 1 token.
    """
    if not text:
        return 0

    # remove extra white spaces.
    cleaned = re.sub(r"\s+", " ", text).strip()
    # Ignore spaces when estimating token length
    no_space = re.sub(r"\s+", "", cleaned)

    return max(1, len(no_space) // 4)


def split_into_chunks(
    text: str,
    max_tokens: int = 200,
    preserve_sentences: bool = True,
) -> List[str]:
    """
    Split long text into token-safe chunks.
    - Preserve sentence boundaries when possible
    - Ensure each chunk is < max_tokens tokens
    - Avoid breaking in the middle of words
    """

    if text is None:
        return [""]

    if not isinstance(text, str):
        if isinstance(text, (int, float, bool)):
            text = str(text)
        else:
            raise TypeError(
                f"split_into_chunks expects a string, got {type(text)}",
            )

    # remove empty leading and trailing spaces.
    cleaned = text.strip()
    if len(cleaned) == 0:
        return [""]

    # when text size is smaller than the chunk size.
    if estimate_token_count(cleaned) <= max_tokens:
        return [cleaned]

    # split text into sentences.
    if preserve_sentences:
        sentences = re.split(r"(?<=[.!?])\s+", cleaned)
        # If there is only one long sentence.
        if len(sentences) == 1:
            sentences = cleaned.split()
            preserve_sentences = False
    else:
        sentences = cleaned.split()

    chunks = []
    # start a new chunk.
    current = []
    current_tokens = 0

    for sentence in sentences:
        sentence_token = estimate_token_count(sentence)
        new_token_size = sentence_token + current_tokens
        # If adding this sentence causes length exceed max size,
        # Finish this chunk and start a new one.
        if current and new_token_size > max_tokens:
            # close current chunk
            chunks.append(" ".join(current).strip())
            # start a fresh chunk
            current = []
            current_tokens = 0

        current.append(sentence)
        current_tokens += sentence_token

    if current:
        chunks.append(" ".join(current).strip())

    return chunks
