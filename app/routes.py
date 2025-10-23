from flask import Blueprint, jsonify

bp = Blueprint("api", __name__)

@bp.route("/health", methods=["GET"])
def health_check():
    return jsonify({"status": "healthy"}), 200