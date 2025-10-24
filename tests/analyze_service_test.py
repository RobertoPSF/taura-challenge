import json
import pytest
from unittest.mock import patch, MagicMock
from app.services.analyze import analyze_findings_with_ai, service_analyze_scan
from app.models import Scan, Finding


def test_analyze_findings_with_ai_no_findings():
    result = analyze_findings_with_ai([])
    assert result["severity"] == "none"
    assert "No vulnerabilities" in result["summary"]


@patch("app.services.analyze.client.chat.completions.create")
def test_analyze_findings_with_ai_valid_json(mock_openai):
    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=MagicMock(content=json.dumps({
        "summary": "Test summary",
        "severity": "low",
        "recommendations": "Fix the issue"
    })))]
    mock_openai.return_value = mock_response

    findings = [{"info": {"name": "XSS"}}]
    result = analyze_findings_with_ai(findings)

    assert result["summary"] == "Test summary"
    assert result["severity"] == "low"
    assert result["recommendations"] == "Fix the issue"
    mock_openai.assert_called_once()


@patch("app.services.analyze.client.chat.completions.create")
def test_analyze_findings_with_ai_invalid_json(mock_openai, caplog):
    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=MagicMock(content="Not a JSON response"))]
    mock_openai.return_value = mock_response

    findings = [{"info": {"name": "XSS"}}]
    result = analyze_findings_with_ai(findings)

    assert result["severity"] == "unknown"
    assert "Unstructured" in result["recommendations"]
    assert "AI response is not valid JSON" in caplog.text


@patch("app.services.analyze.client.chat.completions.create", side_effect=Exception("API down"))
def test_analyze_findings_with_ai_exception(mock_openai):
    findings = [{"info": {"name": "SQLi"}}]
    result = analyze_findings_with_ai(findings)
    assert result["severity"] == "unknown"
    assert "Error analyzing findings" in result["summary"]
