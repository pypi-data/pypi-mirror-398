from multimodal_agent.codegen.model_template import build_model_prompt
from multimodal_agent.codegen.screen_template import build_screen_prompt
from multimodal_agent.codegen.widget_template import build_widget_prompt


def test_widget_prompt_contains_class_name():
    prompt = build_widget_prompt("MyWidget", stateful=False)
    print(prompt)
    assert "MyWidget" in prompt
    assert "StatelessWidget" in prompt


def test_widget_prompt_stateful():
    prompt = build_widget_prompt("MyWidget", stateful=True)
    print(prompt)
    assert "StatefulWidget" in prompt
    assert "createState" in prompt


def test_screen_prompt_contains_scaffold():
    prompt = build_screen_prompt("HomeScreen")
    print(prompt)
    assert "HomeScreen" in prompt
    assert "Scaffold" in prompt


def test_model_prompt_contains_class_name():
    prompt = build_model_prompt("UserModel")
    print(prompt)
    assert "UserModel" in prompt
    assert "fromJson" in prompt
    assert "copyWith" in prompt
