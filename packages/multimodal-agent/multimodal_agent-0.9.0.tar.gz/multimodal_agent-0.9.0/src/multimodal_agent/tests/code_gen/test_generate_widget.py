import pytest

from multimodal_agent.codegen.engine import CodegenEngine


@pytest.fixture
def eng(monkeypatch):
    eng = CodegenEngine()

    def fake_run(prompt):
        # Always return valid widget code
        return """
        import 'package:flutter/material.dart';

        class TestWidget extends StatelessWidget {
          const TestWidget({ super.key });

          @override
          Widget build(BuildContext context) {
            return const Text('Hi');
            }
          }
        """

    monkeypatch.setattr(eng, "run", fake_run)
    return eng


def test_generate_widget_basic(eng):
    raw = eng.generate_widget("TestWidget")
    assert "class TestWidget" in raw


def test_generate_widget_stateful(eng):
    raw = eng.generate_widget("TestWidget", stateful=True)
    # Fake response isn't stateful, we simply check this does not crash.
    assert isinstance(raw, str)
