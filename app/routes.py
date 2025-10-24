from flask import Blueprint, request, jsonify
from .services.nuclei import run_nuclei_scan, service_get_scan, service_get_findings
from .services.katana import run_katana_pipeline
from .services.analyze import service_analyze_scan

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