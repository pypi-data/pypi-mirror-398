import pytest

from multimodal_agent.codegen.engine import CodegenEngine


@pytest.fixture
def eng(monkeypatch):
    eng = CodegenEngine()

    def fake_run(prompt):
        return """
class UserModel {
  const UserModel({ required this.id });

  final String id;

  factory UserModel.fromJson(Map<String, dynamic> json) {
    return UserModel(id: json['id'] as String);
  }

  Map<String, dynamic> toJson() => {'id': id};
}
"""

    monkeypatch.setattr(eng, "run", fake_run)
    return eng


def test_generate_model(eng):
    out = eng.generate_model("UserModel")
    assert "class UserModel" in out
    assert "fromJson" in out
    assert "toJson" in out
