import json
import os
from flask import jsonify
from app.models import Scan, Finding, db
import logging
from openai import OpenAI

logger = logging.getLogger(__name__)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def service_analyze_scan(scan_id):
    scan = db.session.get(Scan, scan_id)
    if not scan:
        return jsonify({"error": "Scan not found"})

    findings = [f.data for f in db.session.query(Finding).filter_by(scan_id=scan_id).all()]
    analysis = analyze_findings_with_ai(findings)

    return jsonify({
        "scan_id": scan_id,
        "summary": analysis["summary"],
        "severity": analysis["severity"],
        "recommendations": analysis["recommendations"]
    })


def analyze_findings_with_ai(findings):
    if not findings:
        return {
            "summary": "No vulnerabilities found.",
            "severity": "none",
            "recommendations": "No actions required."
        }

    findings_text = json.dumps(findings, indent=2)[:8000]

    prompt = f"""
You are a security analyst. You received the results of a vulnerability scan.
Analyze the findings below and produce a structured JSON summary with the following fields:
- summary: general summary
- severity: one of the options (low, medium, high, critical)
- recommendations: suggested actions to remediate the issues.

Findings:
{findings_text}
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a specialized information security assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
        )

        content = response.choices[0].message.content.strip()

        try:
            result = json.loads(content)
        except json.JSONDecodeError:
            logger.warning("AI response is not valid JSON. Returning as text.")
            result = {
                "summary": content,
                "severity": "unknown",
                "recommendations": "Unstructured text analysis."
            }

        return result

    except Exception as e:
        logger.exception("Error calling OpenAI: %s", e)
        return {
            "summary": "Error analyzing findings with AI.",
            "severity": "unknown",
            "recommendations": str(e)
        }