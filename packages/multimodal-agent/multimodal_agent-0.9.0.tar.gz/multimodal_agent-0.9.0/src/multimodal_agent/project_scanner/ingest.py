from multimodal_agent.core.embedding import embed_text
from multimodal_agent.rag.rag_store import SQLiteRAGStore


def ingest_style_into_rag(style_profile: dict, rag_store: SQLiteRAGStore):
    """
    Store style profile as chunks in RAG.
    """
    text = "PROJECT_STYLE_PROFILE:\n" + str(style_profile)

    chunk_ids = rag_store.add_logical_message(
        content=text,
        role="project_style",
        session_id="project_style",
        source="project-learning",
    )

    emb = embed_text(text)

    for chunk_id in chunk_ids:
        rag_store.add_embedding(
            chunk_id=chunk_id,
            embedding=emb,
            model="text-embedding-004",
        )

    return chunk_ids
