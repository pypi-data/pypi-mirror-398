import pytest

from multimodal_agent.codegen.engine import CodegenEngine


@pytest.fixture
def eng(monkeypatch):
    eng = CodegenEngine()

    def fake_run(prompt):
        return """
import 'package:flutter/material.dart';

class HomeScreen extends StatelessWidget {
  const HomeScreen({ super.key });

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Home')),
      body: const Center(child: Text('Hi')),
    );
  }
}
"""

    monkeypatch.setattr(eng, "run", fake_run)
    return eng


def test_generate_screen(eng):
    out = eng.generate_screen("HomeScreen")
    assert "class HomeScreen" in out
    assert "Scaffold" in out
