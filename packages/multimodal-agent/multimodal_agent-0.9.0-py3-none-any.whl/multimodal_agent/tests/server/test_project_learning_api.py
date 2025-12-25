import json

from fastapi.testclient import TestClient

from multimodal_agent.server.server import agent, app

client = TestClient(app)


def test_learn_project_endpoint(tmp_path):
    # create mock pubspec.yaml
    project = tmp_path / "project"
    project.mkdir()
    (project / "pubspec.yaml").write_text("name: test_project\n")

    response = client.post(
        "/learn/project",
        json={"path": str(project)},
    )
    assert response.status_code == 200

    data = response.json()
    assert data["message"] == "Project learned"
    assert "project_id" in data


def test_load_project_profile():
    # Pre-store a fake project profile directly
    proj_id = "project:test"
    agent.rag_store.add_logical_message(
        content=json.dumps({"name": "test"}),
        role="project_profile",
        session_id=proj_id,
        source="project-learning",
    )

    response = client.get(f"/project/{proj_id}")
    assert response.status_code == 200

    data = response.json()
    assert data["id"] == proj_id
    assert data["profile"]["name"] == "test"
