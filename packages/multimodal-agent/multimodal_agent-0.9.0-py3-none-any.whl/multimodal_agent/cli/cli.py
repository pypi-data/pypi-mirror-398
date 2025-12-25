import argparse
import json
import os

import uvicorn
import yaml
from dotenv import load_dotenv

from multimodal_agent.cli.history import handle_history
from multimodal_agent.cli.printing import print_markdown_with_meta
from multimodal_agent.codegen.engine import CodegenEngine
from multimodal_agent.config import get_config, set_config_field
from multimodal_agent.errors import AgentError
from multimodal_agent.logger import get_logger
from multimodal_agent.project_scanner import (
    scan_project,
)
from multimodal_agent.rag.rag_store import SQLiteRAGStore, default_db_path
from multimodal_agent.utils import load_image_as_part
from multimodal_agent.version import __version__

# Load .env from the project root
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
ENV_PATH = os.path.join(ROOT_DIR, ".env")
load_dotenv(ENV_PATH)

logger = get_logger(__name__)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="agent",
        description="Multimodal Agent powered by Google Gemini",
    )
    # parser debug field
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging",
    )

    # parser model field.
    parser.add_argument(
        "--model",
        type=str,
        default="gemini-2.5-flash",
        help="Specify which model to use",
    )
    # parser version field.
    parser.add_argument(
        "--version",
        action="store_true",
        help="Show version and exit",
    )

    subparsers = parser.add_subparsers(dest="command")

    # agent ask command
    ask_parser = subparsers.add_parser("ask", help="Ask a text-only question")
    ask_parser.add_argument("prompt", type=str, help="Your question")
    ask_parser.add_argument(
        "--no-rag",
        action="store_true",
        help="Disable RAG (ignore local memory)",
    )

    # format
    ask_parser.add_argument(
        "--format",
        action="store_true",
        help="Format output syntax.",
    )

    ask_parser.add_argument(
        "--json",
        action="store_true",
        help="Return output as JSON.",
    )

    ask_parser.add_argument(
        "--session", type=str, default=None, help="Session ID for this query"
    )

    # agent image command
    image_parser = subparsers.add_parser("image", help="Ask with image + text")
    image_parser.add_argument(
        "image_path",
        type=str,
        help="Path to local image",
    )
    image_parser.add_argument("prompt", type=str, help="Your question")
    image_parser.add_argument(
        "--session",
        type=str,
        default=None,
        help="Session ID for this query",
    )

    # agent gen <type> <name>
    gen_parser = subparsers.add_parser(
        "gen",
        help="Generate Flutter code (widget/screen/model)",
    )

    gen_sub = gen_parser.add_subparsers(
        dest="gen_cmd",
        required=True,
        help="Generation command",
    )

    # gen widget <name>
    gen_widget = gen_sub.add_parser("widget", help="Generate a Flutter widget")
    gen_widget.add_argument("name")
    gen_widget.add_argument(
        "--override",
        action="store_true",
        help="Overwrite file if it exists",
    )
    gen_widget.add_argument(
        "--stateful",
        action="store_true",
        help="Generate a stateful widget",
    )

    gen_widget.add_argument(
        "--desc",
        type=str,
        default="",
        help="Optional description of the desired widget UI.",
    )

    # gen screen <name>
    gen_screen = gen_sub.add_parser("screen", help="Generate a Flutter screen")
    gen_screen.add_argument("name")
    gen_screen.add_argument(
        "--override",
        action="store_true",
        help="Overwrite file if exists",
    )
    gen_screen.add_argument(
        "--desc",
        type=str,
        default="",
        help="Optional description of the desired screen UI.",
    )

    # gen model <name>
    gen_model = gen_sub.add_parser("model", help="Generate a Dart model class")
    gen_model.add_argument("name")
    gen_model.add_argument(
        "--override",
        action="store_true",
        help="Overwrite if exists",
    )
    gen_model.add_argument(
        "--desc",
        type=str,
        default="",
        help="Optional description of the model (fields / purpose).",
    )

    # gen enum <name>
    gen_enum = gen_sub.add_parser("enum", help="Generate a Dart Enum")
    gen_enum.add_argument("name")
    gen_enum.add_argument(
        "--override",
        action="store_true",
        help="OverWrite if exists",
    )
    gen_enum.add_argument(
        "--desc",
        type=str,
        default="",
        help="Optional description of the enum",
    )

    # gen repository <name>
    gen_repository = gen_sub.add_parser(
        "repository",
        help="Generate a Dart repository abstraction",
    )
    gen_repository.add_argument("name")
    gen_repository.add_argument(
        "--entity",
        type=str,
        default=None,
        help="Entity name the repository manages",
    )
    gen_repository.add_argument(
        "--override",
        action="store_true",
        help="Overwrite if exists",
    )
    gen_repository.add_argument(
        "--desc",
        type=str,
        default="",
        help="Optional description of the repository",
    )

    # format
    image_parser.add_argument(
        "--format",
        action="store_true",
        help="Format output syntax.",
    )

    image_parser.add_argument(
        "--json",
        action="store_true",
        help="Return output as JSON.",
    )

    # chat.
    chat_parser = subparsers.add_parser(
        "chat",
        help="Start interactive chat mode",
    )
    chat_parser.add_argument(
        "--no-rag",
        action="store_true",
        help="Disable RAG (ignore local memory)",
    )
    chat_parser.add_argument(
        "--session",
        type=str,
        default=None,
        help="Session ID for this chat session",
    )

    # history parent command
    history_parser = subparsers.add_parser(
        "history",
        help="Manage agent memory / history",
    )

    history_subparsers = history_parser.add_subparsers(
        dest="history_cmd",
        required=True,
    )

    # history show
    show_parser = history_subparsers.add_parser(
        "show",
        help="Show recent chunks stored in memory",
    )

    show_parser.add_argument(
        "--limit",
        type=int,
        default=50,
        help="Number of recent entries to show",
    )

    show_parser.add_argument(
        "--session",
        type=str,
        default=None,
        help="Filter by session id",
    )

    show_parser.add_argument(
        "--clean",
        action="store_true",
        help="Hide noise messages (FAKE_RESPONSE, project_profile, and test messages).",  # noqa
    )

    # history clear
    history_subparsers.add_parser(
        "clear",
        help="Filter by session id",
    )

    # summary parser
    summary_parser = history_subparsers.add_parser(
        "summary",
        help="Summarize memory using the agent",
    )
    summary_parser.add_argument(
        "--session",
        type=str,
        default=None,
        help="Filter by session id",
    )

    summary_parser.add_argument(
        "--limit",
        type=int,
        default=50,
    )

    # delete
    delete_parser = history_subparsers.add_parser(
        "delete",
        help="Delete a specific memory chunk by ID",
    )
    delete_parser.add_argument("chunk_id", type=int)

    # learning
    learning_parser = subparsers.add_parser("learn-project")
    learning_parser.add_argument("path")
    learning_parser.add_argument("--project-id", "-p")
    learning_parser.add_argument("--no-store", action="store_true")

    # list projects
    subparsers.add_parser("list-projects")

    show_parser = subparsers.add_parser("show-project")
    show_parser.add_argument("project_id")

    inspect_parser = subparsers.add_parser("inspect-project")
    inspect_parser.add_argument("path")

    # server
    server_parser = subparsers.add_parser(
        "server",
        help="Run agent API server",
    )
    server_parser.add_argument("--port", type=int, default=8000)

    # config
    config_parser = subparsers.add_parser(
        "config",
        help="Manage agent configuration",
    )
    config_sub = config_parser.add_subparsers(dest="config_cmd")

    # agent config set-key <key>
    set_key = config_sub.add_parser("set-key", help="Set API key")
    set_key.add_argument("key")

    # agent config set-model <model>
    set_model = config_sub.add_parser("set-model", help="Set model")
    set_model.add_argument(
        "model",
        help="Model name to save as chat model",
    )

    # agent config set-image-model
    set_image_model = config_sub.add_parser(
        "set-image-model",
        help="set the image model",
    )

    set_image_model.add_argument(
        "model",
        help="Model name to save as image model",
    )

    # agent config set-embed-model
    set_embed_model = config_sub.add_parser(
        "set-embed-model",
        help="set the embedding model",
    )
    set_embed_model.add_argument(
        "model",
        help="Model name to save as embedding model",
    )

    # agent config show
    config_sub.add_parser("show", help="Show current config")

    return parser


def handle_text(
    agent,
    question,
    debug=False,
    response_format="text",
    formatted: bool = False,
):
    try:
        response = agent.ask(
            question,
            response_format=response_format,
            formatted=formatted,
        )
    except Exception as e:
        logger.error(f"[ask] Model failed: {e}")
        print("Error: model failed to generate an answer.")
        return 1

    # chat output.
    if hasattr(response, "text"):
        text = response.text
    else:
        text = str(response)

    print_markdown_with_meta(
        sections=[
            ("Question", question),
            ("Answer", text),
        ],
        meta={
            "type": "ask",
            "command": "ask",
        },
    )

    if debug and hasattr(response, "usage") and response.usage:
        print(
            f"[usage] prompt={response.usage.get('prompt_tokens')} "
            f"response={response.usage.get('response_tokens')} "
            f"total={response.usage.get('total_tokens')}"
        )

    return 0


def handle_image(
    agent,
    image,
    question,
    debug=False,
    response_format="text",
    formatted: bool = False,
):
    try:
        response = agent.ask_with_image(
            question,
            image,
            response_format=response_format,
            formatted=formatted,
        )
    except Exception as e:
        logger.error(f"[image] Model failed: {e}")
        print("Error: model failed to generate an answer.")
        return 1

    # Extract text
    if hasattr(response, "text"):
        text = response.text
    else:
        text = str(response)

    print_markdown_with_meta(
        sections=[
            ("Question", question),
            ("Answer", text),
        ],
        meta={
            "type": "image",
            "command": "image",
        },
    )

    if debug and hasattr(response, "usage") and response.usage:
        print(
            f"[usage] prompt={response.usage.get('prompt_tokens')} "
            f"response={response.usage.get('response_tokens')} "
            f"total={response.usage.get('total_tokens')}"
        )

    return 0


def test_main(argv=None):
    """
    Wrapper used by tests: behaves like a Click command but delegates to
    argparse.
    """
    parser = build_parser()
    args = parser.parse_args(argv or [])
    return _main(args, parser)


def main():
    parser = build_parser()
    args = parser.parse_args()
    return _main(args, parser)


def _main(args, parser):
    from multimodal_agent.core.agent_core import MultiModalAgent

    if args.version:
        print(f"multimodal-agent version {__version__}")
        return 0

    if args.debug:
        os.environ["LOGLEVEL"] = "DEBUG"
        logger.setLevel("DEBUG")

    if not args.command:
        parser.print_help()
        return 0

    needs_agent = args.command in {
        "ask",
        "image",
        "chat",
        "server",
        "learn-project",
        "list-projects",
        "show-project",
    }
    agent = None

    if needs_agent:
        # Create agent instance
        enable_rag = not getattr(args, "no_rag", False)
        # create agent instance
        agent = MultiModalAgent(model=args.model, enable_rag=enable_rag)

    try:
        # asking question in text.
        if args.command == "ask":
            formatted = getattr(args, "format", False)
            json_mode = getattr(args, "json", False)
            response_format = "json" if json_mode else "text"

            return handle_text(
                agent,
                question=args.prompt,
                debug=args.debug,
                response_format=response_format,
                formatted=formatted,
            )
        # Image questions.
        elif args.command == "image":

            try:
                image_as_part = load_image_as_part(args.image_path)
            except Exception as exception:
                logger.error(
                    f"Cannot read image: {args.image_path}: {exception}",
                )
                print("Error: could not load image.")
                return 1

            formatted = getattr(args, "format", False)
            json_mode = getattr(args, "json", False)
            response_format = "json" if json_mode else "text"
            return handle_image(
                agent,
                image=image_as_part,
                question=args.prompt,
                debug=args.debug,
                response_format=response_format,
                formatted=formatted,
            )

        # chat mode.
        elif args.command == "chat":
            agent.chat(session_id=args.session)
            return 0

        # history mode.
        elif args.command == "history":
            db_path = os.environ.get("MULTIMODAL_AGENT_DB", default_db_path())
            store = SQLiteRAGStore(db_path=db_path)

            return handle_history(args, store)

        # server mode.
        elif args.command == "server":
            uvicorn.run(
                "multimodal_agent.server:app",
                host="127.0.0.1",
                port=args.port,
                reload=False,
            )
            return 0

        # learn project.
        elif args.command == "learn-project":
            profile = scan_project(args.path)
            print(json.dumps(profile.to_dict(), indent=2))

            if not args.no_store:
                project_id = (
                    args.project_id or f"project:{profile.package_name}"
                )  # noqa
                agent.rag_store.add_logical_message(
                    content=json.dumps(profile.to_dict()),
                    role="project_profile",
                    session_id=project_id,
                    source="project-learning",
                )
                print(f"Stored as: {project_id}")
            return 0

        # LIST PROJECTS
        elif args.command == "list-projects":
            rows = agent.rag_store.get_project_profiles()
            print("Stored Project Profiles")
            for row in rows:
                print(f"- {row['session_id']} (created {row['created_at']})")
            return 0

        # SHOW PROJECT
        elif args.command == "show-project":
            db_path = os.environ.get("MULTIMODAL_AGENT_DB", default_db_path())
            store = SQLiteRAGStore(db_path=db_path)
            project_id = args.project_id
            if not project_id.startswith("project:"):
                project_id = f"project:{project_id}"
            profile = store.load_project_profile(project_id)
            if profile is None:
                print("Profile not found")
                return 0

            print(json.dumps(profile, indent=2))
            return 0

        # INSPECT PROJECT
        elif args.command == "inspect-project":
            profile = scan_project(args.path)
            print(json.dumps(profile.to_dict(), indent=2))
            return 0

        # agent gen ...
        if args.command == "gen":
            engine = CodegenEngine(model=getattr(args, "model", None))

            # Widget
            if args.gen_cmd == "widget":
                out = engine.generate_and_write(
                    kind="widget",
                    name=args.name,
                    root=os.getcwd(),
                    override=args.override,
                    stateful=getattr(args, "stateful", False),
                    description=getattr(args, "desc", ""),
                )
                print(f"Widget generated at {out}")
                return 0

            # Screen
            if args.gen_cmd == "screen":
                out = engine.generate_and_write(
                    kind="screen",
                    name=args.name,
                    root=os.getcwd(),
                    override=args.override,
                    description=getattr(args, "desc", ""),
                )
                print(f"Screen generated at {out}")
                return 0

            # Model
            if args.gen_cmd == "model":
                out = engine.generate_and_write(
                    kind="model",
                    name=args.name,
                    root=os.getcwd(),
                    override=args.override,
                    description=getattr(args, "desc", ""),
                )
                print(f"Model generated at {out}")
                return 0

            if args.gen_cmd == "enum":
                out = engine.generate_and_write(
                    kind="enum",
                    name=args.name,
                    root=os.getcwd(),
                    override=args.override,
                    description=getattr(args, "desc", ""),
                )
                print(f"Enum generated at {out}")
                return 0

            if args.gen_cmd == "repository":
                out = engine.generate_and_write(
                    kind="repository",
                    name=args.name,
                    root=os.getcwd(),
                    override=args.override,
                    description=getattr(args, "desc", ""),
                    entity=getattr(args, "entity", None),
                )
                print(f"Repository generated at {out}")
                return 0

        elif args.command == "config":

            if args.config_cmd == "set-key":
                set_config_field("api_key", args.key)
                print("API key updated.")
                return 0

            if args.config_cmd == "set-model":
                set_config_field("chat_model", args.model)
                print(f"Model updated to {args.model}")
                return 0

            if args.config_cmd == "set-image-model":
                set_config_field("image_model", args.model)
                print(f"Image model updated to {args.model}")
                return 0
            if args.config_cmd == "set-embed-model":
                set_config_field("embedding_model", args.model)
                print(f"Embedding model updated to {args.model}")
                return 0

            if args.config_cmd == "show":
                print(yaml.dump(get_config(), sort_keys=False))
                return 0

    except AgentError as exception:
        logger.error(f"Agent failed: {exception}")
        return 1

    return 0
