from multimodal_agent.rag.chunking import (
    _split_paragraphs,
    _split_sentences,
    chunk_text,
)


# chunk_text
def test_chunk_text_empty():
    assert chunk_text("") == []


def test_chunk_text_below_limit():
    text = "short text"
    assert chunk_text(text, max_chars=100) == [text]


def test_chunk_text_single_paragraph_large():
    # long text in one paragraph and sentence.
    text = "word " * 300
    chunks = chunk_text(text, max_chars=100)
    for chunk in chunks:
        print(len(chunk))
    assert all(len(c) <= 100 for c in chunks)
    assert len(chunks) > 1


def test_chunk_text_multiple_paragraphs():

    text_1 = "Paragraph_1.\n\n"
    text_2 = "Sentence1. Sentence2. " * 50
    text_3 = "\n\nLast paragraph."
    text = text_1 + text_2 + text_3
    chunks = chunk_text(text, max_chars=120)

    # All chunks must be <= max_chars
    assert all(len(chunk) <= 120 for chunk in chunks)

    # Must preserve the order
    assert chunks[0].startswith("Paragraph_1")
    assert chunks[-1].startswith("Last paragraph")


def test_chunk_text_sentence_boundary_respected():
    text = "A. " * 100
    chunks = chunk_text(text, max_chars=50)

    # Each chunk must end in a full sentence
    for chunk in chunks:
        assert chunk.endswith(".")


def test_chunk_text_no_paragraphs_long():
    text = "A long text. " * 80
    chunks = chunk_text(text, max_chars=150)
    assert all(len(c) <= 150 for c in chunks)
    assert len(chunks) > 1


def test_chunk_text_extremely_long_sentence():
    text = "X" * 1000
    chunks = chunk_text(text, max_chars=200)

    assert all(len(chunk) <= 200 for chunk in chunks)
    assert len(chunks) >= 5


def test_chunk_text_fallback_when_all_empty():
    assert chunk_text("   ") == []


def test_chunk_text_final_join_no_empty_chunks():
    text = "Hi.\n\n.\n\nHello."
    chunks = chunk_text(text, max_chars=50)
    # no empty chunks
    assert all(chunk.strip() for chunk in chunks)


# split paragraphs
def test_split_paragraphs_basic():
    section_1 = "Paragraph1"
    section_2 = "Paragraph2"
    section_3 = "Paragraph3"
    text = f"{section_1}\n\n{section_2}\n\n{section_3}"
    parts = _split_paragraphs(text)
    assert parts == [section_1, section_2, section_3]


def test_split_paragraphs_trims_whitespace():
    text = "  A \n\n B\n\n\n C  "
    parts = _split_paragraphs(text)
    assert parts == ["A", "B", "C"]


def test_split_empty_paragraphs():
    assert _split_paragraphs("") == []


# sentences
def test_split_sentences_basic():
    text = "Hello world. This is a test!"
    sentences = _split_sentences(text)
    assert sentences == ["Hello world.", "This is a test!"]


def test_split_sentences_question_mark():
    text = "What is AI? It is cool."
    sentences = _split_sentences(text)
    assert sentences == ["What is AI?", "It is cool."]


def test_split_sentences_no_punctuation():
    text = "This has no punctuation and should stay as one piece"
    sentences = _split_sentences(text)
    assert sentences == [text]


def test_split_sentences_mixed():
    text = "A! B? C."
    sentences = _split_sentences(text)
    assert sentences == ["A!", "B?", "C."]
