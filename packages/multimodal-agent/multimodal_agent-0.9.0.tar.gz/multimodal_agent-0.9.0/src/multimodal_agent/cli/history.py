from multimodal_agent.cli.printing import print_markdown_with_meta
from multimodal_agent.rag import SQLiteRAGStore


#   HISTORY HANDLERS (RAG-Backed, Session-Aware)
def handle_history(args, store) -> int:
    """
    Dispatch RAG history operations.
    """
    try:
        if args.history_cmd == "show":
            return _show_history(args, store)
        elif args.history_cmd == "delete":
            return _delete_history(args, store)
        elif args.history_cmd == "clear":
            return _clear_history(args, store)
        elif args.history_cmd == "summary":
            return _summary_history(args, store)
        else:
            print(f"unknown history subcommand: {args.history_cmd}")
            return 1
    finally:
        store.close()


def _show_history(args, store: SQLiteRAGStore) -> int:
    """
    Show stored history from RAG SQLite database.
    """
    limit = args.limit if args.limit is not None else 1000
    chunks = store.get_recent_chunks(limit=limit)

    # Filter by session
    if getattr(args, "session", None):
        chunks = [c for c in chunks if c.session_id == args.session]

    if getattr(args, "clean", False):
        chunks = [c for c in chunks if not _is_noise_chunk(c)]

    if not chunks:
        print_markdown_with_meta(
            sections=[("History", "No history found.")],
            meta={
                "type": "history_show",
                "limit": args.limit,
                "session": getattr(args, "session", None),
                "count": 0,
            },
        )
        return 0

    lines: list[str] = []

    # Reverse chunks in chronological order and generate the content
    for chunk in reversed(chunks):
        session_id = chunk.session_id or "-"
        lines.append(
            f"[{chunk.id}] ({session_id}) {chunk.role} @ {chunk.created_at}",
        )
        # filter content length
        preview = chunk.content[:200]
        lines.append(preview)
        if len(chunk.content) > 200:
            lines.append(" ...")
        lines.append("---")

    body = "\n".join(lines)

    # print content.
    print_markdown_with_meta(
        sections=[("History", body)],
        meta={
            "type": "history_show",
            "limit": args.limit,
            "session": getattr(args, "session", None),
            "count": len(chunks),
        },
    )
    return 0


def _clear_history(args, store: SQLiteRAGStore) -> int:
    store.clear_all()
    print_markdown_with_meta(
        sections=[("History", "History cleared.")],
        meta={"type": "history_clear"},
    )
    return 0


def _delete_history(args, store: SQLiteRAGStore) -> int:
    print(args)
    store.delete_chunk(chunk_id=args.chunk_id)
    print_markdown_with_meta(
        sections=[("History", f"Deleted chunk {args.chunk_id}.")],
        meta={
            "type": "history_delete",
            "chunk_id": args.chunk_id,
        },
    )
    return 0


def _summary_history(args, store: SQLiteRAGStore) -> int:
    """
    Summarize recent history using the LLM.
    """
    # Get recent chunks, if user has not defined limit, fetch all chunks.
    limit = args.limit if args.limit is not None else None
    chunks = store.get_recent_chunks(limit=limit)

    # Optional filtering
    if getattr(args, "session", None):
        chunks = [c for c in chunks if c.session_id == args.session]

    if not chunks:
        print_markdown_with_meta(
            sections=[("Summary", "No history to summarize.")],
            meta={
                "type": "history_summary",
                "limit": args.limit,
                "session": getattr(args, "session", None),
            },
        )
        return 0

    clean_chunks = [c for c in chunks if not _is_noise_chunk(c)]

    if not clean_chunks:
        print_markdown_with_meta(
            sections=[("Summary", "No meaningful history to summarize.")],
            meta={
                "type": "history_summary",
                "limit": args.limit,
                "session": getattr(args, "session", None),
            },
        )
        return 0

    lines = []
    for chunk in clean_chunks:
        role = {
            "user": "User",
            "agent": "Assistant",
        }.get(chunk.role, chunk.role.capitalize())

        lines.append(f"{role}: {chunk.content}")

    transcript = "\n".join(lines)
    # Summarization prompt
    summarization_prompt = (
        "Summarize the following conversation in a concise, coherent way:\n\n"
        + transcript
    )

    # To avoid circular dependency
    from multimodal_agent.core.agent_core import MultiModalAgent

    agent = MultiModalAgent(enable_rag=False)
    response, usage = agent.safe_generate_content(summarization_prompt)

    text = getattr(response, "text", str(response))

    print_markdown_with_meta(
        sections=[("Summary", text)],
        meta={
            "type": "history_summary",
            "limit": args.limit,
            "session": getattr(args, "session", None),
        },
    )
    return 0


# NEW — Option B Noise Filter
def _is_noise_chunk(chunk):
    """
    Smart noise filter (Option B):
      - keep all messages except obvious noise.
      - we do NOT remove future tool/system roles needed for extensions.
    """

    c = chunk.content or ""

    # Never treat normal user messages as noise
    if chunk.role == "user":
        return False

    # Ignore tests and fake responses
    if c.startswith("FAKE_RESPONSE"):
        return True

    # Ignore project scanning noise from test suite
    if chunk.role == "project_profile":
        return True

    # Empty or whitespace-only content
    if not c.strip():
        return True

    # Extremely short meaningless messages
    if c.strip() in {"hello", "hi", "reply", "mocked response"}:
        return True

    return False
