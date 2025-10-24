from unittest.mock import patch

def test_health_check(client):
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json["status"] == "healthy"


@patch("app.routes.run_nuclei_scan")
def test_start_scan_success(mock_run_nuclei_scan, client):
    mock_run_nuclei_scan.return_value = {
        "scan_id": "123",
        "status": "running",
        "target": "https://example.com"
    }

    payload = {"target": "https://example.com"}
    res = client.post("/api/scan", json=payload)
    assert res.status_code == 202
    assert mock_run_nuclei_scan.called
    assert res.json["target"] == "https://example.com"


def test_start_scan_missing_target(client):
    res = client.post("/api/scan", json={})
    assert res.status_code == 400
    assert "error" in res.json
