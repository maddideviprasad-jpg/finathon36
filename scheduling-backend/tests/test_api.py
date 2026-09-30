import pytest
from fastapi.testclient import TestClient
import time
from app.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_schedule_generation_pipeline():
    request_data = {
        "employees": [
            {
                "id": "e1",
                "name": "Alice",
                "roles": ["manager"],
                "max_hours": 40.0
            }
        ],
        "shifts": [
            {
                "id": "s1",
                "start_time": "2023-10-25T08:00:00Z",
                "end_time": "2023-10-25T16:00:00Z",
                "required_roles": ["manager"]
            },
            {
                "id": "s2",
                "start_time": "2023-10-26T08:00:00Z",
                "end_time": "2023-10-26T16:00:00Z",
                "required_roles": ["cashier"]
            }
        ],
        "constraints": {
            "max_consecutive_shifts": 5,
            "min_rest_hours": 12
        }
    }

    response = client.post("/api/v1/schedules/generate", json=request_data)
    assert response.status_code == 202
    data = response.json()
    assert "task_id" in data
    assert data["status"] == "PENDING"
    
    task_id = data["task_id"]

    max_retries = 5
    for _ in range(max_retries):
        time.sleep(1)
        get_response = client.get(f"/api/v1/schedules/{task_id}")
        assert get_response.status_code == 200
        get_data = get_response.json()
        
        if get_data.get("status") == "success":
            result = get_data
            assert result["status"] == "success"
            assert len(result["assignments"]) > 0
            assert len(result["conflicts"]) > 0
            break
        elif get_data["status"] == "FAILED":
            pytest.fail(f"Task failed: {get_data.get('error')}")
    else:
        pytest.fail("Task did not complete within the expected time")