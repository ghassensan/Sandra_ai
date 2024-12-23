from fastapi.testclient import TestClient
from sandra_ai.main import app

client = TestClient(app)


def test_health_check() -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "👍"}
