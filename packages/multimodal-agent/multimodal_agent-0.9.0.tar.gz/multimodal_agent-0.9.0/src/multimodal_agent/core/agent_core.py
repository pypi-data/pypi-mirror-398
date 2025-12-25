import json
import os
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional

from google.genai import Client
from google.genai.types import HttpOptions, Part

from multimodal_agent.cli.formatting import format_output
from multimodal_agent.config import get_config
from multimodal_agent.core.embedding import embed_text
from multimodal_agent.rag.rag_store import (
    RAGStore,
    SQLiteRAGStore,
    default_db_path,
)

from ..errors import AgentError, NonRetryableError, RetryableError
from ..logger import get_logger


def is_retryable_error(exception):
    # Example: Gemini overload has status_code = 503
    return hasattr(exception, "status_code") and exception.status_code == 503


@dataclass
class AgentResponse:
    text: str
    data: Optional[Dict[str, Any]] = None
    usage: Optional[Dict[str, Any]] = None


class DummyClient:
    class models:
        @staticmethod
        def generate_content(*a, **k):
            raise RuntimeError(
                "Real model not available (no API key).",
            )


class MultiModalAgent:
    def __init__(
        self,
        model="gemini-2.5-flash",
        api_version="v1",
        client=None,
        rag_store: RAGStore | None = None,
        enable_rag: bool = True,
        embedding_model: str = "text-embedding-004",
    ):
        # init logging
        self.logger = get_logger(__name__)
        self.logger.info("Initializing MultiModal agent...")

        # set up config.
        config = get_config()
        config_chat_model = config.get("chat_model", "gemini-2.0-flash")
        config_image_model = config.get("image_model", config_chat_model)
        config_embedding_model = config.get("embedding_model", embedding_model)

        self.model = model or config_chat_model
        self.embedding_model = config_embedding_model
        self.image_model = config_image_model
        # set api key.
        api_key = os.environ.get("GOOGLE_API_KEY") or config.get("api_key")

        # Normalize empty strings to None.
        if not api_key or str(api_key).strip() == "":
            api_key = None

        self.api_key = api_key

        if client is not None:
            self.client = client
        else:
            if self.api_key:
                self.client = Client(
                    http_options=HttpOptions(api_version=api_version),
                    api_key=api_key,
                )
            else:
                # In CI or local without key, use dummy client
                self.client = DummyClient()

        # rag store.
        self.rag_store: RAGStore | None = rag_store or SQLiteRAGStore(
            db_path=default_db_path(),
        )
        self.enable_rag = enable_rag

        # usage logging.
        self.usage_logging = True
        self.usage_log_path = os.path.expanduser(
            "~/.multimodal_agent/usage.log",
        )

        # ensure directory exist.
        os.makedirs(os.path.dirname(self.usage_log_path), exist_ok=True)

    def safe_generate_content(
        self,
        contents,
        max_retries: int = 3,
        base_delay: int = 1,
        response_format: str = "text",
    ):
        api_key = self.api_key
        # Identify when user is real google client.
        is_real_google_client = (
            hasattr(self.client, "models")
            and callable(getattr(self.client.models, "generate_content", None))
            and self.client.__class__.__name__ == "Client"
        )
        # define offline mode.
        offline_mode = not api_key and (
            self.client is None  # no client at all
            or isinstance(self.client, DummyClient)
            or is_real_google_client  # real client but key missing
        )

        if offline_mode:
            last = contents[-1] if contents else ""
            clean = str(last).strip()

            class RespWrapper:
                def __init__(self, t):
                    self.text = t

            text = f"FAKE_RESPONSE: {clean}"

            # Simple synthetic usage
            joined = "".join(str(c) for c in contents)
            usage = {
                "prompt_tokens": len(joined),
                "response_tokens": 5,
                "total_tokens": len(joined) + 5,
            }

            if usage and self.usage_logging:
                self._log_usage(
                    usage=usage,
                    contents=contents,
                    response_format=response_format,
                    model=self.model,
                )

            return RespWrapper(text), usage

        # ONLINE MODE
        if response_format == "json":
            contents = [
                "Return ONLY a valid JSON object without backticks.",
                *contents,
            ]

        for attempt in range(1, max_retries + 1):
            try:
                response = self.client.models.generate_content(
                    model=self.model,
                    contents=contents,
                )

                usage = None
                meta = getattr(response, "usage_metadata", None)
                if meta:
                    usage = {
                        "prompt_tokens": getattr(
                            meta,
                            "prompt_token_count",
                            None,
                        ),
                        "response_tokens": getattr(
                            meta,
                            "candidates_token_count",
                            None,
                        ),
                        "total_tokens": getattr(
                            meta,
                            "total_token_count",
                            None,
                        ),
                    }

                class RespWrapper:
                    def __init__(self, t):
                        self.text = t

                if usage and self.usage_logging:
                    self._log_usage(
                        usage=usage,
                        contents=contents,
                        response_format=response_format,
                        model=self.model,
                    )
                return RespWrapper(response.text), usage

            except Exception as exception:
                if is_retryable_error(exception):
                    wait = base_delay * (2 ** (attempt - 1))
                    attempt_message = f"(attempt {attempt}/{max_retries})."
                    self.logger.warning(
                        f"Warning: Model overloaded {attempt_message} ",
                    )
                    self.logger.warning(f"Retry in {wait}s...")
                    time.sleep(wait)
                    continue

                self.logger.error(
                    "Non-retryable error occurred.",
                    exc_info=True,
                )
                raise NonRetryableError(str(exception)) from exception

        self.logger.error("Model overloaded. Please try again later.")
        raise RetryableError("Model overloaded after maximum retry attempts.")

    # Public methods.
    def ask_with_image(
        self,
        question: str,
        image: Part,
        response_format: str = "text",
        formatted: bool = False,
    ) -> AgentResponse:

        response, usage = self.safe_generate_content(
            contents=[question, image],
            response_format=response_format,
        )

        # Offline safety: response sometimes may be a dict
        if isinstance(response, dict):
            return AgentResponse(
                text=str(response),
                data=response if response_format == "json" else None,
                usage=usage,
            )

        text = response.text

        if response_format == "json":
            cleaned = text.strip()

            # remove fenced code blocks just like ask()
            if cleaned.startswith("```"):
                cleaned = cleaned.strip("`")
                cleaned = cleaned.replace("json", "", 1).strip()

            try:
                data = self._parse_json_output(cleaned)
            except Exception:
                data = None

            return AgentResponse(text=text, data=data, usage=usage)

        # text mode
        if formatted:
            text = format_output(text)

        return AgentResponse(text=text, data=None, usage=usage)

    def ask(
        self,
        question: str,
        session_id: Optional[str] = None,
        response_format: str = "text",
        formatted: bool = False,
        rag_enabled: bool | None = None,
    ) -> AgentResponse:
        """
        One-shot question API.

        If RAG is enabled:
        - store question
        - embed question
        - retrieve similar chunks
        - prepend context to prompt
        - store reply (+ optionally embed reply)
        """
        #  store session id
        session_id = self._ensure_session_id(session_id)

        enable_rag = self.enable_rag if rag_enabled is None else rag_enabled

        # RAG logic (unchanged)
        if enable_rag and self.rag_store is not None:
            # store question as a chunk
            question_chunk_ids = self.rag_store.add_logical_message(
                content=question,
                role="user",
                session_id=session_id,
                source="ask",
            )
            # embed question
            question_embedding = embed_text(
                question,
                model=self.embedding_model,
            )

            # store embedding
            for chunk_id in question_chunk_ids:
                self.rag_store.add_embedding(
                    chunk_id=chunk_id,
                    embedding=question_embedding,
                    model=self.embedding_model,
                )

            # retrieve similar content
            similar = self.rag_store.search_similar(
                query_embedding=question_embedding,
                model=self.embedding_model,
                top_k=5,
            )

            rag_context = [chunk.content for score, chunk in similar]

            system_prompt = (
                "You are a helpful assistant. Use the context if relevant. "
                "otherwise ignore it."
            )

            contents = [
                system_prompt,
                (
                    "RAG CONTEXT:\n" + "\n---\n".join(rag_context)
                    if rag_context
                    else "CONTEXT:\n(none)"
                ),
                "QUESTION:\n" + question,
            ]
        else:
            contents = [question]

        # Always returns (RespWrapper, usage)
        response, usage = self.safe_generate_content(
            contents,
            response_format=response_format,
        )

        text = response.text

        # Json mode
        if response_format == "json":

            cleaned = text.strip()

            if cleaned.startswith("```"):
                cleaned = cleaned.strip("`").strip()
                if cleaned.startswith("json"):
                    cleaned = cleaned[len("json") :].strip()  # noqa

            data = self._parse_json_output(cleaned)

            # store agent reply in RAG
            if self.enable_rag and self.rag_store is not None:
                self._store_agent_reply(answer=data, session_id=session_id)

            return AgentResponse(
                text=text,
                data=data,
                usage=usage,
            )

        # Text mode
        if self.enable_rag and self.rag_store is not None:
            self._store_agent_reply(answer=text, session_id=session_id)

        if formatted:
            text = format_output(text)

        return AgentResponse(text=text, data=None, usage=usage)

    def _ensure_session_id(self, session_id: Optional[str]) -> str:
        """
        If no session_id is provided, use a stable default or generate one.
        For CLI chat, you might accept a --session flag and pass it through.
        """

        if session_id:
            return session_id

        return "default"

    def _convert_to_json_response(self, response):
        raw = response.text.strip()
        # Remove markdown fences.
        raw = self._strip_markdown(text=raw)

        try:
            objects = json.loads(raw)
            response.json = objects
            return response
        except Exception:
            fallback = {"raw": raw}
            response.json = fallback
            return response

    def _parse_json_output(self, text: str):
        stripped = text.strip()

        # Handle fenced code blocks: ```json ... ```
        if stripped.startswith("```"):
            stripped = stripped.strip("`").strip()
        if stripped.startswith("json"):
            stripped = stripped[len("json") :].strip()  # noqa
        if stripped.endswith("```"):
            stripped = stripped[:-3].strip()

        try:
            return json.loads(stripped)
        except Exception:
            return None

    def _strip_markdown(self, text: str) -> str:
        """
        Remove ```json ... ``` fences if the model returns them.

        """
        if text.startswith("```"):
            text = text.strip("`")
            # remove markdown fences like ```json or ```
            text = text.replace("json", "", 1).strip()
        return text

    def _store_agent_reply(self, answer, session_id):
        # convert answer to text
        text = answer if isinstance(answer, str) else json.dumps(answer)

        reply_chunk_ids = self.rag_store.add_logical_message(
            content=text,
            role="agent",
            session_id=session_id,
            source="ask",
        )

        try:
            reply_emb = embed_text(text, model=self.embedding_model)
            for chunk_id in reply_chunk_ids:
                self.rag_store.add_embedding(
                    chunk_id=chunk_id,
                    embedding=reply_emb,
                    model=self.embedding_model,
                )
        except Exception:
            pass

    def _log_usage(self, usage, contents, response_format, model):
        """
        Append a structured usage record to usage.log.
        """
        try:
            with open(self.usage_log_path, "a") as f:
                record = {
                    "timestamp": time.time(),
                    "model": model,
                    "prompt_tokens": usage.get("prompt_tokens"),
                    "response_tokens": usage.get("response_tokens"),
                    "total_tokens": usage.get("total_tokens"),
                    "response_format": response_format,
                    "prompt_preview": str(contents)[:150],  # for debugging
                }
                f.write(json.dumps(record) + "\n")
        except Exception:
            # usage logging must never crash the agent.
            pass

    @staticmethod
    def try_parse_json(text):
        # Remove ```json fences
        if text.strip().startswith("```"):
            text = text.strip().split("```")[1]

        try:
            data = json.loads(text)
            return {"data": data, "__text__": text}
        except Exception:
            return {"data": None, "__text__": text}

    def store_project_profile(self, project_id: str, profile_dict: dict):
        json_str = json.dumps(profile_dict, ensure_ascii=False)

        self.rag_store.add_logical_message(
            content=json_str,
            role="project_profile",
            session_id=project_id,
            source="project-learning",
        )

        return True

    # Chat mode.
    def chat(
        self,
        session_id: Optional[str] = None,
        enable_rag: Optional[bool] = None,
        rag_top_k: int = 5,
    ) -> str:
        """
        Stateful chat with session-aware memory + RAG.

        Steps:
        - Store user messages (chunked)
        - Embed user messages
        - Retrieve similar chunks
        - Generate response
        - Store + embed assistant responses
        """

        if enable_rag is None:
            enable_rag = self.enable_rag

        # Ensure having a session id.
        session_id = self._ensure_session_id(session_id=session_id)

        self.logger.info(
            "Entering chat mode. Starting chat session"
            f"'{session_id}'. Type 'exit' to quit.",
        )

        while True:
            # remove leading and trailing white spaces.
            user_input = input("You: ").strip()

            if _is_exit_command(user_input.lower()):
                self.logger.info("Chat ended. Goodbye!")
                break

            if enable_rag and self.rag_store is not None:
                # store user message as chunk
                user_message_chunk_ids = self.rag_store.add_logical_message(
                    content=user_input,
                    role="user",
                    session_id=session_id,
                    source="chat",
                )

                # embed user message
                try:
                    # return embedding vector
                    question_embedding = embed_text(
                        user_input,
                        model=self.embedding_model,
                    )

                    # add embedding to the store
                    for chunk_id in user_message_chunk_ids:
                        self.rag_store.add_embedding(
                            chunk_id=chunk_id,
                            embedding=question_embedding,
                            model=self.embedding_model,
                        )
                except Exception:
                    question_embedding = None

                # If embedding failed, skip RAG retrieval
                if question_embedding is None:
                    rag_context = []
                else:

                    # Retrieve RAG context from history.
                    similar = self.rag_store.search_similar(
                        query_embedding=question_embedding,
                        model=self.embedding_model,
                        top_k=rag_top_k,
                    )
                    rag_context = [chunk.content for score, chunk in similar]

                # Build final prompt

                system_prompt = (
                    "You are a helpful assistant. Use session history and "
                    "RAG context below if relevant. If not useful, ignore it."
                )
                final_contents = [
                    system_prompt,
                    (
                        "RAG CONTEXT:\n" + "\n---\n".join(rag_context)
                        if rag_context
                        else "RAG CONTEXT:\n(none)"
                    ),
                    "USER MESSAGE:\n" + user_input,
                ]

            else:
                final_contents = [user_input]

            try:
                # call model
                response, usage = self.safe_generate_content(
                    contents=final_contents,
                )
                answer = response.text
                if usage:
                    self.logger.info(
                        f"[usage] prompt={usage.get('prompt_tokens')} "
                        f"response={usage.get('response_tokens')} "
                        f"total={usage.get('total_tokens')}"
                    )
            except RetryableError as exception:
                self.logger.error(f"Retryable model failure: {exception}")
                continue

            except AgentError as exception:
                self.logger.error(f"Agent error: {exception}")
                continue

            except NonRetryableError as exception:
                self.logger.error(f"Non-retryable model error: {exception}")
                continue

            if enable_rag and self.rag_store is not None:
                # store assistant reply
                reply_chunk_ids = self.rag_store.add_logical_message(
                    content=answer,
                    role="agent",
                    session_id=session_id,
                    source="chat",
                )

                # embed assistant reply
                try:
                    reply_embedding = embed_text(
                        answer,
                        model=self.embedding_model,
                    )
                    for chunk_id in reply_chunk_ids:
                        self.rag_store.add_embedding(
                            chunk_id=chunk_id,
                            embedding=reply_embedding,
                            model=self.embedding_model,
                        )

                except Exception:
                    pass

            # print answer
            self.logger.info(f"Agent: {answer}")


def _is_exit_command(text: str) -> bool:
    return text.strip().lower() in ("exit", "exit()", "quit", "quit()")
