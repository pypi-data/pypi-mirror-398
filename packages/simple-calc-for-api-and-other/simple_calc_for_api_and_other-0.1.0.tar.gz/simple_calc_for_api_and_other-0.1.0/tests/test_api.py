from fastapi.testclient import TestClient
import sys
import os
from app.main import app


sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_api_add_endpoint():
    client = TestClient(app)
    response = client.post("/calculate", json={"action": "add", "x": 10, "y": 5})

    assert response.status_code == 200
    assert response.json() == {"result": 15.0}
    pass
