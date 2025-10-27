import json
from unittest.mock import patch

@patch("app.routes.run_katana_pipeline")
def test_start_katana_scan(mock_run_pipeline, client):
    mock_run_pipeline.return_value = (
        {"scan_id": "abc123", "status": "crawling", "target": "example.com"},
        202
    )

    payload = {"domain": "example.com", "crawl": True}
    res = client.post("/api/scan", json=payload)

    assert res.status_code == 202
    assert "scan_id" in res.json
    assert res.json["status"] == "crawling"
    mock_run_pipeline.assert_called_once_with("example.com")


@patch("app.routes.run_katana_pipeline")
def test_start_katana_scan_missing_domain(client):
    payload = {"crawl": True}
    res = client.post("/api/scan", json=payload)
    assert res.status_code == 400
    assert "error" in res.json


@patch("app.routes.run_katana_pipeline")
def test_start_katana_scan_missing_crawling(client):
    payload = {"domain": "example.com"}
    res = client.post("/api/scan", json=payload)
    assert res.status_code == 400
    assert "error" in res.json
