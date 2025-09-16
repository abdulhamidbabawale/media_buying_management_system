from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_create_client():
    with TestClient(app) as client:
      response = client.post("/api/v1/clients/", json={
                                             "name": "johnny3",
                                             "industry": "driving",
                                             "settings": {},
                                             "api_keys_refs": {}
                                           })
      assert response.status_code == 200
