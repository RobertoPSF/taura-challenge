import threading
import logging
from datetime import datetime, timezone
from flask import current_app, jsonify
from ..models import db, Scan, Finding
from ..utils.executor import _update_status, _finalize_scan, _consume_output, _start_nuclei_process, _log_stderr
from sqlalchemy.orm import scoped_session, sessionmaker

logger = logging.getLogger(__name__)


def _worker(scan_id, target, app):
    with app.app_context():
        scan = Scan.query.get(scan_id)
        if not scan:
            logger.error("Scan id %s not found", scan_id)
            return
        
        Session = scoped_session(sessionmaker(bind=db.engine))
        session = Session()

        _update_status(scan, "scanning", session)

        try:

            process = _start_nuclei_process(target)

            threading.Thread(
                target=_log_stderr, args=(process.stderr,), daemon=True
            ).start()

            _consume_output(process, scan_id, session)

            _finalize_scan(process, scan, session)
        except Exception as e:
            logger.exception("Error trying to execute scan %s: %s", scan_id, e)
            _update_status(scan, "failed", session)
        finally:
            scan.completed_at = datetime.now(timezone.utc)
            db.session.commit()
            db.session.remove()


def run_nuclei_scan(target):
    app = current_app._get_current_object()

    scan = Scan(target=target)
    db.session.add(scan)
    db.session.commit()

    threading.Thread(target=_worker, args=(scan.id, target, app), daemon=True).start()

    return jsonify({
        "scan_id": scan.id,
        "status": scan.status,
        "target": scan.target
    })


def service_get_scan(scan_id):

    scan = Scan.query.get(scan_id)

    if not scan:
        return jsonify({"error": "Scan not found"}), 404
    findings_count = Finding.query.filter_by(scan_id=scan_id).count()

    return jsonify({
        "scan_id": scan.id,
        "status": scan.status,
        "target": scan.target,
        "findings_count": findings_count,
        "created_at": scan.created_at.isoformat().replace('+00:00', 'Z'),
        "completed_at": scan.completed_at.isoformat().replace('+00:00', 'Z') if scan.completed_at else None
    })

def service_get_findings(scan_id):
    findings = Finding.query.filter_by(scan_id=scan_id).all()

    return jsonify({
        "scan_id": scan_id,
        "total": len(findings),
        "findings": [f.data for f in findings]
    })