from multimodal_agent.codegen.model_template import build_model_prompt
from multimodal_agent.codegen.screen_template import build_screen_prompt
from multimodal_agent.codegen.utils import (
    find_flutter_root,
    model_file_path,
    safe_write_file,
    screen_file_path,
    widget_file_path,
)
from multimodal_agent.codegen.widget_template import build_widget_prompt
from multimodal_agent.core.agent_core import MultiModalAgent


class CodeGenerator:
    """
    Code generation engine.
    This class handles:
      - locating project root
      - building prompt
      - calling the LLM
      - writing generated code
    """

    def __init__(self, agent: MultiModalAgent):
        self.agent = agent
        self.root = find_flutter_root(".")

    # Widget
    def generate_widget(
        self,
        name: str,
        stateful: bool = False,
        override=False,
    ):
        path = widget_file_path(self.root, name)
        prompt = build_widget_prompt(name=name, stateful=stateful)

        response = self.agent.ask(prompt)
        dart_code = response.text.strip()

        safe_write_file(path, dart_code, override=override)
        return path

    # Screen
    def generate_screen(self, name: str, override=False):
        path = screen_file_path(self.root, name)
        prompt = build_screen_prompt(name=name)

        response = self.agent.ask(prompt)
        dart_code = response.text.strip()

        safe_write_file(path, dart_code, override=override)
        return path

    # Model
    def generate_model(self, name: str, override=False):
        path = model_file_path(self.root, name)
        prompt = build_model_prompt(name=name)

        response = self.agent.ask(prompt)
        dart_code = response.text.strip()

        safe_write_file(path, dart_code, override=override)
        return path
