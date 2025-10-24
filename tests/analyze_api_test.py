from unittest.mock import patch
from app.models import db, Scan, Finding


@patch("app.services.analyze.analyze_findings_with_ai")
def test_analyze_scan_route_success(mock_analyze, client, test_app):
    with test_app.app_context():
        scan = Scan(target="https://example.com", status="completed")
        db.session.add(scan)
        db.session.commit()

        finding = Finding(scan_id=scan.id, data={"info": {"name": "XSS"}})
        db.session.add(finding)
        db.session.commit()

        scan_id = scan.id

    mock_analyze.return_value = {
        "summary": "All good",
        "severity": "low",
        "recommendations": "Patch XSS"
    }

    res = client.post(f"/api/scan/{scan_id}/analyze")
    assert res.status_code == 200
    assert res.json["severity"] == "low"
    assert res.json["summary"] == "All good"
    assert res.json["recommendations"] == "Patch XSS"
    mock_analyze.assert_called_once()


def test_analyze_scan_route_not_found(client):
    res = client.post("/api/scan/999/analyze")
    assert res.status_code == 200
    assert "error" in res.json
