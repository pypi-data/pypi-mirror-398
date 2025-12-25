from unittest.mock import patch

from fastapi.testclient import TestClient

from multimodal_agent.server import app

client = TestClient(app)


def test_generate_repository_success():
    with patch(
        "multimodal_agent.codegen.engine.CodegenEngine.generate_repository",
        return_value="abstract class UserRepository {}",
    ):
        resp = client.post(
            "/generate/repository",
            json={
                "name": "UserRepository",
                "entity": "User",
            },
        )

    assert resp.status_code == 200
    data = resp.json()
    assert "code" in data
    assert "UserRepository" in data["code"]


def test_generate_repository_invalid_name():
    resp = client.post(
        "/generate/repository",
        json={"name": "_Repo"},
    )

    assert resp.status_code == 400
