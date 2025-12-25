import json
import math
import os
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple

from multimodal_agent.core.embedding import embed_text
from multimodal_agent.core.tokenizer import split_into_chunks


@dataclass
class Chunk:
    id: int
    session_id: Optional[str]
    role: str
    content: str
    created_at: str
    source: Optional[str]


def default_db_path() -> Path:
    """
    Default location for memory DB, e.g. ~/.multimodal_agent/memory.db
    """
    home = Path.home()
    root = home / ".multimodal_agent"
    root.mkdir(parents=True, exist_ok=True)
    return root / "memory.db"


class RAGStore:
    """
    Small interface to swap test and implementation.
    """

    def add_chunk(
        self,
        content: str,
        role: str,
        session_id: Optional[str],
        source: str = "chat",
    ) -> int:
        raise NotImplementedError

    def add_embedding(
        self,
        chunk_id: int,
        embedding: List[float],
        model: str,
    ) -> None:
        raise NotImplementedError

    def get_recent_chunk(self, limit: int = 50) -> List[Chunk]:
        raise NotImplementedError

    def search_similar(
        self,
        query_embedding: List[float],
        model: str,
        top_k: int = 5,
        max_candidates: int = 1000,
    ) -> List[Tuple[float, Chunk]]:
        raise NotImplementedError

    def clear_all(self) -> None:
        raise NotImplementedError

    def delete_chunk(self, chunk_id: int) -> None:
        raise NotImplementedError

    def add_logical_message(
        self,
        content: str,
        role: str,
        session_id: str | None,
        source: str = "chat",
        max_tokens: int = 200,
    ) -> list[int]:
        """
        High-level API:
        - normalize / chunk a logical message
        - store each chunk in `chunks` table
        - return list of chunk IDs.
        """

        if not isinstance(content, str):
            raise TypeError(f"content must be str, received: {type(content)}")

        text_chunks = split_into_chunks(
            content,
            max_tokens=max_tokens,
        )
        chunk_ids: list[int] = []

        for chunk in text_chunks:
            chunk_id = self.add_chunk(
                content=chunk,
                role=role,
                session_id=session_id,
                source=source,
            )

            chunk_ids.append(chunk_id)

        return chunk_ids


class SQLiteRAGStore(RAGStore):
    def __init__(
        self,
        db_path: Optional[str | Path] = None,
        check_same_thread=True,
    ) -> None:
        if db_path is None:
            env_path = os.environ.get("MULTIMODAL_AGENT_DB")
            if env_path:
                db_path = Path(env_path)
            else:
                db_path = default_db_path()
        self.db_path = db_path

        # Cli has one connection per process
        self.conn = sqlite3.connect(
            self.db_path,
            check_same_thread=check_same_thread,
        )
        self.conn.row_factory = sqlite3.Row
        self._init_db()

    def _init_db(self) -> None:
        curser = self.conn.cursor()
        curser.executescript(
            """
            PRAGMA foreign_keys = ON;

            CREATE TABLE IF NOT EXISTS sessions (
                id          TEXT PRIMARY KEY,
                label       TEXT,
                created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS chunks (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id  TEXT NULL,
                role        TEXT NOT NULL,
                content     TEXT NOT NULL,
                created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                source      TEXT,
                FOREIGN KEY(session_id) REFERENCES sessions(id) ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_chunks_session_id ON chunks(session_id);
            CREATE INDEX IF NOT EXISTS idx_chunks_role ON chunks(role);

            CREATE TABLE IF NOT EXISTS embeddings (
                chunk_id    INTEGER PRIMARY KEY,
                model       TEXT NOT NULL,
                dim         INTEGER NOT NULL,
                embedding   TEXT NOT NULL,
                FOREIGN KEY(chunk_id) REFERENCES chunks(id) ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_embeddings_model ON embeddings(model);
            """  # noqa: E501
        )
        self.conn.commit()

    def add_chunk(
        self,
        content,
        role,
        session_id,
        source="chat",
    ) -> int:
        cursor = self.conn.cursor()
        # If session_id provided but not already in sessions,
        # insert automatically
        if session_id is not None:
            cursor.execute(
                "INSERT OR IGNORE INTO sessions (id) VALUES (?)",
                (session_id,),
            )
        cursor.execute(
            """
        INSERT INTO chunks (session_id, role, content, source)
        VALUES (?, ?, ?, ?)
        """,
            (session_id, role, content, source),
        )
        self.conn.commit()
        return int(cursor.lastrowid)

    def add_embedding(self, chunk_id, embedding, model) -> None:
        embedding_list = [float(x) for x in embedding]
        dimension = len(embedding_list)
        embedding_json = json.dumps(embedding_list)
        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO embeddings (chunk_id, model, dim, embedding)
            VALUES (?, ?, ?, ?)
            """,  # noqa: E501,
            (chunk_id, model, dimension, embedding_json),
        )
        self.conn.commit()

    def get_recent_chunks(self, limit: int = 50) -> List[Chunk]:
        cursor = self.conn.cursor()
        if limit is None:
            cursor.execute(
                """
                SELECT id, session_id, role, content, created_at, source
                FROM chunks
                ORDER BY created_at DESC, id ASC;
                """
            )
        else:
            cursor.execute(
                """
                SELECT id, session_id, role, content, created_at, source
                FROM chunks
                ORDER BY created_at DESC, id ASC
                LIMIT ?
                """,
                (limit,),
            )
        rows = cursor.fetchall()
        return [
            Chunk(
                id=row["id"],
                session_id=row["session_id"],
                role=row["role"],
                content=row["content"],
                created_at=row["created_at"],
                source=row["source"],
            )
            for row in rows
        ]

    @staticmethod
    def _cosine(a: list[float], b: List[float]) -> float:
        if not a or not b or len(a) != len(b):
            return 0.0

        # initial values
        dot = 0.0
        na = 0.0
        nb = 0.0

        for x, y in zip(a, b):
            dot += x * y
            na += x * x
            nb += y * y

        if na == 0.0 or nb == 0.0:
            return 0.0

        return dot / (math.sqrt(na) * math.sqrt(nb))

    def search_similar(
        self,
        query_embedding,
        model,
        top_k=5,
        max_candidates=1000,
    ):
        """
        v1: simple in-Python cosine similarity.

        - Fetch up to `max_candidates` embeddings for model
        - Compute cosine similarity in Python
        - Return best `top_k` as (score, Chunk)
        """
        # fetch up data.
        cursor = self.conn.cursor()

        cursor.execute(
            """
            SELECT e.chunk_id, e.embedding
            FROM embeddings e
            WHERE e.model = ?
            ORDER BY e.rowid DESC
            LIMIT ?
            """,
            (model, max_candidates),
        )

        rows = cursor.fetchall()
        if isinstance(query_embedding, str):
            # Raw text
            q_embedding = self._embed_text(query_embedding, model=model)
        else:
            # Assume caller passed an embedding already
            q_embedding = query_embedding

        query_embedding = [float(x) for x in q_embedding]

        scored: List[Tuple[float, int]] = []
        # compute cosine similarity and sort them based on the similarity
        for row in rows:
            chunk_id = int(row["chunk_id"])
            embedding = json.loads(row["embedding"])
            score = self._cosine(query_embedding, embedding)
            scored.append((score, chunk_id))

        scored.sort(reverse=True, key=lambda x: x[0])
        scored = scored[:top_k]

        if not scored:
            return []

        # load chunk rows
        chunk_ids = [cid for _, cid in scored]
        placeholders = ",".join("?" for _ in chunk_ids)
        cursor.execute(
            f"""
            SELECT id, session_id, role, content, created_at, source
            FROM chunks
            WHERE id IN ({placeholders})
            """,
            chunk_ids,
        )

        chunk_rows = {int(row["id"]): row for row in cursor.fetchall()}

        results: List[Tuple[float, Chunk]] = []
        for score, cid in scored:
            row = chunk_rows.get(cid)
            if not row:
                continue
            chunk = Chunk(
                id=row["id"],
                session_id=row["session_id"],
                role=row["role"],
                content=row["content"],
                created_at=row["created_at"],
                source=row["source"],
            )
            results.append((score, chunk))

        return results

    def _embed_text(self, text: str, model: str):
        """
        Internal wrapper calling global embed_text() so the store
        can embed queries the same way as stored chunks.
        """

        emb = embed_text(text, model=model)
        return [float(x) for x in emb]

    def clear_all(self):

        cursor = self.conn.cursor()

        cursor.executescript(
            """
            DELETE FROM embeddings;
            DELETE FROM chunks;
            DELETE FROM sessions;
            """
        )

        self.conn.commit()

    def delete_chunk(self, chunk_id: int) -> None:
        cursor = self.conn.cursor()
        cursor.execute(
            "DELETE FROM chunks WHERE id = ?",
            (chunk_id,),
        )
        self.conn.commit()

    def get_project_profiles(self):
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT session_id, content, created_at
            FROM chunks
            WHERE role='project_profile'
            ORDER BY created_at DESC
        """
        )
        return cursor.fetchall()

    def load_project_profile(self, project_id: str):
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT content FROM chunks
            WHERE session_id=? AND role='project_profile'
            ORDER BY created_at DESC LIMIT 1
        """,
            (project_id,),
        )
        rows = cursor.fetchall()
        for row in rows:
            try:
                return json.loads(row["content"])
            except Exception:
                continue

    def close(self) -> None:
        self.conn.close()
