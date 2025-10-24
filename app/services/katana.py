import threading
import logging
from datetime import datetime, timezone
from flask import current_app, jsonify
from ..models import db, Scan
from ..utils.katana_executor import _run_katana, _run_nuclei_in_parallel

logger = logging.getLogger(__name__)


def run_katana_pipeline(domain):
    app = current_app._get_current_object()
    from sqlalchemy.orm import scoped_session, sessionmaker
    Session = scoped_session(sessionmaker(bind=db.engine))
    session = Session()

    scan = Scan(target=domain, status="crawling")
    session.add(scan)
    session.commit()

    threading.Thread(target=_worker, args=(scan.id, domain, app, Session), daemon=True).start()
    Session.remove()

    return jsonify({
        "scan_id": scan.id,
        "status": scan.status,
        "target": domain
    }), 202


def _worker(scan_id, domain, app, Session):
    with app.app_context():
        session = Session()
        try:
            scan = session.get(Scan, scan_id)
            if not scan:
                logger.error("Scan id %s not found", scan_id)
                return

            urls = _run_katana(domain)
            urls_count = len(urls)

            scan.status = "scanning"
            scan.urls_found = urls_count
            session.commit()

            _run_nuclei_in_parallel(scan_id, urls, app, Session)

            scan.status = "completed"
            scan.completed_at = datetime.now(timezone.utc)
            session.commit()

        except Exception as e:
            logger.exception("Error running Katana pipeline: %s", e)
            try:
                scan = session.get(Scan, scan_id)
                if scan:
                    scan.status = "failed"
                    session.commit()
            finally:
                logger.exception("Failed to mark scan as failed for %s", scan_id)
        finally:
            Session.remove()
