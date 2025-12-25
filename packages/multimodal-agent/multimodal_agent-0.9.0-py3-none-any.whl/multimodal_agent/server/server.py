import json
import logging
import os
import tempfile
import time
import uuid
from pathlib import Path
from typing import Optional

from fastapi import (
    FastAPI,
    File,
    Form,
    HTTPException,
    Query,
    Request,
    UploadFile,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from multimodal_agent import MultiModalAgent, config
from multimodal_agent.codegen.engine import CodegenEngine
from multimodal_agent.project_scanner import scan_project
from multimodal_agent.rag.rag_store import SQLiteRAGStore
from multimodal_agent.server.server_models import (
    AskRequest,
    ChatRequest,
    ChatResponse,
    GenerateCodeResponse,
    GenerateEnumRequest,
    GenerateModelRequest,
    GenerateRepositoryRequest,
    GenerateRequest,
    GenerateScreenRequest,
    GenerateWidgetRequest,
    HistoryItem,
    HistoryResponse,
    LearnProjectRequest,
    MemorySearchRequest,
    SummaryResponse,
)
from multimodal_agent.utils import load_image_as_part

# Logging setup
logger = logging.getLogger("multimodal_agent.server")


# Shared instances (agent + RAG store)
rag = SQLiteRAGStore(
    db_path=os.environ.get("MULTIMODAL_AGENT_DB", ":memory:"),
    check_same_thread=False,
)
agent = MultiModalAgent(rag_store=rag, enable_rag=True)

engine_config = config.get_config()
model = engine_config.get("chat_model")
engine = CodegenEngine(model=model)

# FastAPI app
app = FastAPI(
    title="Multimodal Agent Server",
    description="HTTP API for the multimodal-agent (Gemini wrapper + RAG).",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# Middleware: request logging + basic error handling
@app.middleware("http")
async def log_requests(request: Request, call_next):
    request_id = str(uuid.uuid4())
    start = time.time()
    logger.info(f"[{request_id}] {request.method} {request.url.path}")

    try:
        response = await call_next(request)
    except HTTPException as exc:
        # Let FastAPI handle HTTPException, but log it
        logger.warning(
            f"[{request_id}] HTTPException {exc.status_code}: {exc.detail}",
        )
        raise
    except Exception:
        logger.exception(f"[{request_id}] Unhandled server error")
        return JSONResponse(
            status_code=500,
            content={
                "detail": "Internal server error",
                "request_id": request_id,
            },
        )

    duration_ms = (time.time() - start) * 1000.0
    logger.info(
        f"[{request_id}] {response.status_code} ({duration_ms:.1f} ms)",
    )
    response.headers["X-Request-ID"] = request_id
    return response


# Meta / health
@app.get("/health", tags=["meta"])
def health_check():
    """
    Simple health check for monitoring / Flutter extension.
    """
    return {"status": "ok"}


# Core text endpoints
@app.post("/ask", tags=["core"])
async def ask(request: AskRequest):
    """
    One-off prompt to the agent.
    """
    response = agent.ask(
        request.prompt,
        response_format=request.response_format or "text",
        session_id=request.session_id,
        rag_enabled=not request.no_rag,
    )
    return {
        "text": response.text,
        "data": response.data,
        "usage": response.usage,
    }


@app.post("/chat", tags=["chat"], response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Chat-style endpoint (single turn) ideal for Flutter extension.

    - Uses `message` instead of `prompt`.
    - Supports optional `session_id` for multi-turn conversations.
    """

    prompt = request.message

    if request.context:
        context = request.context

        context_block = []

        if context.get("language"):
            context_block.append(f"Language: {context['language']}")

        if context.get("fileName"):
            context_block.append(f"File: {context['fileName']}")

        if context.get("selection"):
            context_block.append(f"Selected code:\n{context['selection']}")

        if context_block:
            prompt = (
                "You are assisting a developer inside an IDE.\n\n"
                "Context:\n"
                + "\n".join(f"- {line}" for line in context_block)
                + "\n\nUser question:\n"
                + request.message
            )

    resp = agent.ask(
        prompt,
        response_format=request.response_format or "text",
        session_id=request.session_id,
        rag_enabled=not request.no_rag,
    )

    return ChatResponse(
        text=resp.text,
        data=resp.data,
        usage=resp.usage,
        session_id=request.session_id,
    )


# Image endpoints
@app.post("/ask_with_image")
async def ask_with_image(
    prompt: str = Form(...),
    file: UploadFile = File(...),
):
    """
    Accepts an image and text prompt, returns LLM output with robust error
    handling.
    """
    try:
        contents = await file.read()

        # Save temporarily
        suffix = Path(file.filename).suffix or ".jpg"
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=True) as temp:
            temp.write(contents)
            temp.flush()
            image_part = load_image_as_part(temp.name)

        # Try calling LLM
        try:
            response = agent.ask_with_image(prompt, image_part)
            text = response.text or "No text response."
            return {
                "text": text,
                "data": response.data,
                "usage": response.usage,
            }

        except Exception as exception:
            error_message = f"Image processing failed: {str(exception)}"

            usage = (
                getattr(
                    response,
                    "usage",
                    None,
                )
                if "response" in locals()
                else None
            )

            return {
                "text": error_message,
                "data": None,
                "usage": usage,
                "error": True,
            }

    except Exception as exception:
        # Critical failure (I/O, file, unexpected)
        raise HTTPException(
            status_code=500,
            detail=f"Server failed to process image: {str(exception)}",
        )


@app.post("/image", tags=["image"])
async def image(
    file: UploadFile = File(...),
    prompt: str = Form(...),
):
    """
    Convenience alias for /ask_with_image so this works:
    """
    return await ask_with_image(prompt=prompt, file=file)


# Generate endpoint.
@app.post("/generate", tags=["core"])
async def generate(request: GenerateRequest):
    """
    Generic generate endpoint.

    - If `json=True`, returns `data` + `text`.
    - Otherwise returns a raw string.
    """
    response = agent.ask(
        request.prompt,
        response_format="json" if request.json else "text",
    )

    if response.data:
        return {
            "data": response.data,
            "text": response.text,
        }

    return {"raw": response.text}


# Memory / RAG endpoints
@app.post("/memory/search", tags=["memory"])
async def memory_search(request: MemorySearchRequest):
    """
    Vector search over stored memory / RAG store.
    """
    if not agent.enable_rag or agent.rag_store is None:
        return {"results": [], "error": "RAG disabled"}

    results = agent.rag_store.search_similar(
        request.query,
        model=agent.embedding_model,
        top_k=request.limit,
    )
    return {"results": results}


@app.post("/memory/summary", tags=["memory"])
@app.get("/memory/summary", tags=["memory"])
async def memory_summary(limit: int = 50, session_id: Optional[str] = None):
    """
    Summarize recent history / memory.

    We reuse `agent.summarize_history` so behavior is consistent with the CLI.
    """
    if not hasattr(agent, "summarize_history"):
        return {"summary": "Memory summarization not available."}

    summary = agent.summarize_history(limit=limit, session_id=session_id)
    return {"summary": summary}


# History endpoints (HTTP view on the same SQLite history used by the CLI)


def _serialize_chunk(chunk) -> HistoryItem:
    return HistoryItem(
        id=chunk.id,
        role=chunk.role,
        session_id=getattr(chunk, "session_id", None),
        content=chunk.content,
        created_at=str(chunk.created_at),
        source=getattr(chunk, "source", None),
    )


@app.get("/history", tags=["history"], response_model=HistoryResponse)
def history(
    limit: int = Query(50, ge=1),
    session: Optional[str] = Query(None),
):
    """
    Get recent history from the SQLite RAG store.

    This is useful for:
    - Inspecting what the CLI / agents have stored
    - Feeding context into your Flutter extension if you want an external
    viewer
    """
    if agent.rag_store is None:
        raise HTTPException(400, "RAG store not available")

    chunks = agent.rag_store.get_recent_chunks(limit=limit)

    if session:
        chunks = [
            chunk
            for chunk in chunks
            if getattr(chunk, "session_id", None) == session  # noqa
        ]

    items = [_serialize_chunk(c) for c in chunks]

    return HistoryResponse(
        items=items,
        limit=limit,
        session=session,
    )


@app.get("/history/summary", tags=["history"], response_model=SummaryResponse)
def history_summary(
    limit: int = Query(50, ge=1),
    session: Optional[str] = Query(None),
):
    """
    Summarize history using the same summarizer used by the CLI.
    """
    if not hasattr(agent, "summarize_history"):
        raise HTTPException(
            status_code=400,
            detail="History summarization not available on this agent.",
        )

    summary = agent.summarize_history(limit=limit, session_id=session)
    return SummaryResponse(
        summary=summary,
        limit=limit,
        session=session,
    )


# Project learning / profiles
@app.post("/learn/project", tags=["project"])
def learn_project(req: LearnProjectRequest):
    """
    Learn a project's style profile and optionally store it in RAG.

    This is the HTTP twin of your CLI `learn-project` command and will be
    super useful once your Flutter extension wants to:
    - scan an existing project
    - store its style in RAG
    - then call `/generate` or `/ask` with that style as hidden context
    """
    root = Path(req.path).resolve()
    if not root.exists() or not root.is_dir():
        raise HTTPException(400, f"Invalid project path: {root}")

    # 1. Run scanner
    if req.auto_scan:
        profile = scan_project(root)
    else:
        raise HTTPException(400, "auto_scan=False is not supported yet.")

    profile_dict = profile.to_dict()

    # 2. Optionally store in RAG
    project_id = (
        req.project_id or f"project:{profile.package_name or profile.root.name}"  # noqa
    )

    if req.store_profile:
        agent.rag_store.add_logical_message(
            content=json.dumps(profile_dict),
            role="project_profile",
            session_id=project_id,
            source="project-learning",
        )

    return {
        "status": "ok",
        "message": "Project learned",
        "project_id": project_id,
        "profile": profile_dict,
    }


@app.get("/project_profiles/list", tags=["project"])
def list_project_profiles():
    """
    List all learned project profiles stored in RAG.
    """
    rows = agent.rag_store.get_project_profiles()
    results = [
        {
            "project_id": row["session_id"],
            "profile": json.loads(row["content"]),
            "created_at": row["created_at"],
        }
        for row in rows
    ]
    return {"projects": results}


@app.get("/project_profiles/get", tags=["project"])
def get_project_profile(id: str):
    """
    Get a single project profile by id.
    """
    profile = agent.rag_store.load_project_profile(id)
    if not profile:
        raise HTTPException(404, "Profile not found")
    return {"project_id": id, "profile": profile}


@app.get("/project/{project_id}", tags=["project"])
def load_project_api(project_id: str):
    """
    Backward-compatible project profile endpoint.
    """
    profile = agent.rag_store.load_project_profile(project_id)
    if not profile:
        raise HTTPException(404, "Not found")
    return {
        "id": project_id,
        "profile": profile,
    }


@app.post("/generate/widget", tags=["generate"])
def generate_widget(request: GenerateWidgetRequest):
    return generate_api_helper(
        request,
        kind="widget",
    )


@app.post("/generate/screen", tags=["generate"])
def generate_screen(request: GenerateScreenRequest):
    return generate_api_helper(
        request,
        kind="screen",
    )


@app.post("/generate/model", tags=["generate"])
def generate_model(request: GenerateModelRequest):
    return generate_api_helper(
        request,
        kind="model",
    )


@app.post("/generate/enum", tags=["generate"])
def generate_enum(request: GenerateEnumRequest):
    return generate_api_helper(
        request,
        kind="enum",
    )


@app.post("/generate/repository", tags=["generate"])
def generate_repository(request: GenerateRepositoryRequest):
    return generate_api_helper(
        request,
        kind="repository",
    )


def generate_api_helper(
    request,
    kind: str,
) -> GenerateCodeResponse:
    if not request.name or not request.name[0].isalpha():
        raise HTTPException(
            400,
            "Name must start with a letter (valid Dart identifier)",
        )

    try:
        root = Path(request.project_root).resolve()
        if not root.exists():
            raise HTTPException(400, "Invalid project_root")

        path = engine.generate_and_write(
            kind=kind,
            name=request.name,
            root=root,
            override=getattr(request, "override", False),
            stateful=getattr(request, "stateful", False),
            description=request.description or "",
            entity=getattr(request, "entity", None),
            values=getattr(request, "values", None),
        )

        return GenerateCodeResponse(
            code=path.read_text(),
            path=str(path),
        )

    except HTTPException:
        raise
    except Exception as exception:
        raise HTTPException(400, str(exception))
