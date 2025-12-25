from unittest.mock import patch

from fastapi.testclient import TestClient

from multimodal_agent.server import app

client = TestClient(app)


def test_generate_enum_success():
    with patch(
        "multimodal_agent.codegen.engine.CodegenEngine.generate_enum",
        return_value="enum OrderStatus { pending, shipped }",
    ):
        resp = client.post(
            "/generate/enum",
            json={"name": "OrderStatus", "description": ""},
        )

    assert resp.status_code == 200
    data = resp.json()
    assert "code" in data
    assert "enum OrderStatus" in data["code"]


def test_generate_enum_invalid_name():
    resp = client.post(
        "/generate/enum",
        json={"name": "1BadEnum"},
    )

    assert resp.status_code == 400
    assert "Name must start with a letter" in resp.text
