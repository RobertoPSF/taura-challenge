from concurrent.futures import ThreadPoolExecutor, as_completed
import logging
import subprocess
import threading
import re
from .utils import _log_stderr, _parse_json_line_

logger = logging.getLogger(__name__)
_ANSI_RE = re.compile(r"\x1B\[[0-?]*[ -/]*[@-~]")
NUCLEI_MAX_THREADS = 5


def _run_katana(domain):
    process = subprocess.Popen(
        ["katana", "-u", domain, "-silent", "-jc"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
    )
    threading.Thread(target=_log_stderr, args=(process.stderr,), daemon=True).start()

    urls = _consume_output_katana(process)

    process.wait()
    return urls
    

def _consume_output_katana(process):
    urls = []
    if not process.stdout:
        return urls

    for line in process.stdout:
        clean = _ANSI_RE.sub("", line).strip()
        if not clean:
            continue

        parsed = _parse_json_line_(clean)
        if parsed and "url" in parsed:
            urls.append(parsed["url"])
            continue

        if clean.startswith("http://") or clean.startswith("https://"):
            urls.append(clean)

    return urls


def _run_nuclei_in_parallel(scan_id, urls, app, Session):
    total = len(urls)
    if total == 0:
        return
    
    with ThreadPoolExecutor(max_workers=NUCLEI_MAX_THREADS) as executor:
        futures = [
            executor.submit(_safe_nuclei_call, scan_id, url, app, Session)
            for url in urls
        ]

        for i, future in enumerate(as_completed(futures), start=1):
            try:
                future.result()
            except Exception as e:
                logger.error("Error scanning URL (%d/%d): %s", i, total, e)


def _safe_nuclei_call(scan_id, url, app, Session):
    try:
        from ..services.nuclei import _worker as nuclei_worker
        nuclei_worker(scan_id, url, app, Session)
    except Exception as e:
        logger.error("Nuclei worker failed for %s: %s", url, e)