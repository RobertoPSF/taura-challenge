from flask import Blueprint, request, jsonify
from .services.nuclei import run_nuclei_scan, service_get_scan, service_get_findings
from .services.katana import run_katana_pipeline
from .services.analyze import service_analyze_scan
from pathlib import Path

bp = Blueprint("api", __name__)

@bp.route("/health", methods=["GET"])
def health_check():
    return jsonify({"status": "healthy"}), 200


@bp.route("/api/scan", methods=["POST"])
def start_scan():
    data = request.get_json()
    target = data.get("target")
    domain = data.get("domain")
    crawl = data.get("crawl", False)

    if crawl and domain:
        return run_katana_pipeline(domain)
    elif target:
        return run_nuclei_scan(target), 202
    elif not target:
        return jsonify({"error": "target is required"}), 400


@bp.route("/api/scan/<scan_id>", methods=["GET"])
def get_scan(scan_id):

    if not scan_id:
        return jsonify({"error": "scan_id is required"}), 400
    
    return service_get_scan(scan_id), 200


@bp.route("/api/scan/<scan_id>/findings", methods=["GET"])
def get_findings(scan_id):

    if not scan_id:
        return jsonify({"error": "scan_id is required"}), 400
    
    return service_get_findings(scan_id), 200

@bp.route("/api/scan/<scan_id>/analyze", methods=["POST"])
def analyze_scan(scan_id):
    
    if not scan_id:
        return jsonify({"error": "scan_id is required"}), 400
    
    return service_analyze_scan(scan_id), 200


@bp.route("/openapi.json", methods=["GET"])
def openapi_json():
    root = Path(__file__).resolve().parents[1]
    spec_path = root / "api.yaml"
    if not spec_path.exists():
        return jsonify({"error": "OpenAPI spec not found"}), 404
    try:
        try:
            import yaml
        except Exception:
            return jsonify({"error": "PyYAML is not installed on the environment"}), 500

        with spec_path.open("r", encoding="utf-8") as fh:
            doc = yaml.safe_load(fh)
        return jsonify(doc)
    except Exception as e:
        return jsonify({"error": f"Failed to load OpenAPI spec: {e}"}), 500


@bp.route("/docs", methods=["GET"])
def swagger_ui():
        html = """
<!doctype html>
<html>
    <head>
        <meta charset="utf-8" />
        <title>API Docs - Taura Challenge</title>
        <link rel="stylesheet" href="https://unpkg.com/swagger-ui-dist@4/swagger-ui.css" />
    </head>
    <body>
        <div id="swagger-ui"></div>
        <script src="https://unpkg.com/swagger-ui-dist@4/swagger-ui-bundle.js"></script>
        <script>
            window.ui = SwaggerUIBundle({
                url: '/openapi.json',
                dom_id: '#swagger-ui',
            });
        </script>
    </body>
</html>
"""
        return html, 200