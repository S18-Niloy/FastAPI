from fastapi.testclient import TestClient
from app.main import app
from app.auth import create_token

client = TestClient(app)

def test_login_and_latest():
    token = create_token("tester")
    # Call latest when empty
    res = client.post("/ai-task", json={"task":"latest"}, headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    assert res.json()["task"] == "latest"
