import logging
import subprocess
import json
from ..models import db, Finding
import re
from ..models import db

logger = logging.getLogger(__name__)

_ANSI_RE = re.compile(r"\x1B\[[0-?]*[ -/]*[@-~]")


def _update_status(scan, status, session):
    scan.status = status
    db.session.commit()


def _finalize_scan(process, scan, session):
    try:
        returncode = process.wait(timeout=600)
    except subprocess.TimeoutExpired:
        logger.error("Nuclei scan timeout")
        process.kill()
        returncode = -1
    status = "completed" if returncode == 0 else "failed"

    if status == "failed" and process.stderr:
        stderr = process.stderr.read().strip()
        if stderr:
            logger.error("Nuclei finished with an error: %s", stderr)

    _update_status(scan, status, session)


def _parse_json_line(line):
    if not line.strip():
        return None

    clean = _ANSI_RE.sub("", line).strip()
    try:
        return json.loads(clean)
    except json.JSONDecodeError:
        return None
    

def _log_stderr(stderr_pipe):
    if not stderr_pipe:
        return
    for line in stderr_pipe:
        clean = _ANSI_RE.sub("", line).strip()
        if clean:
            logger.warning(clean)


def _consume_output(process, scan_id, session):

    if not process.stdout:
        return

    for line in process.stdout:
        clean = _ANSI_RE.sub("", line).strip()
        if not clean:
            continue

        parsed = _parse_json_line(clean)
        if parsed:
            db.session.add(Finding(scan_id=scan_id, data=parsed))
            db.session.commit()
            logger.info(parsed.get("info", {}).get("name", "vuln"))


def _start_nuclei_process(target):
    return subprocess.Popen(
        ["nuclei", "-u", target, "-jsonl"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
    )