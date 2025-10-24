import logging
import re
import json

logger = logging.getLogger(__name__)
_ANSI_RE = re.compile(r"\x1B\[[0-?]*[ -/]*[@-~]")

def _log_stderr(stderr_pipe):
    if not stderr_pipe:
        return
    for line in stderr_pipe:
        clean = _ANSI_RE.sub("", line).strip()
        if clean:
            logger.error(clean)


def _parse_json_line_(line):
    if not line.strip():
        return None
     
    clean = _ANSI_RE.sub("", line).strip()
    try:
        
        return json.loads(clean)
    except json.JSONDecodeError:
        return None