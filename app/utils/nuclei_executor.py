from concurrent.futures import ThreadPoolExecutor, as_completed
import logging
import subprocess
from ..models import Finding
import re
from .utils import _parse_json_line_

logger = logging.getLogger(__name__)
_ANSI_RE = re.compile(r"\x1B\[[0-?]*[ -/]*[@-~]")


def _update_status(scan, status, session):
    scan.status = status
    session.commit()


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


def _consume_output(process, scan_id, session):

    if not process.stdout:
        return

    for line in process.stdout:
        clean = _ANSI_RE.sub("", line).strip()
        if not clean:
            continue

        parsed = _parse_json_line_(clean)
        if parsed:
            session.add(Finding(scan_id=scan_id, data=parsed))
            session.commit()


def _start_nuclei_process(target):
    return subprocess.Popen(
        ["nuclei", "-u", target, "-jsonl"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
    )
