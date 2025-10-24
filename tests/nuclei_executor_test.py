import io
import json
from unittest.mock import MagicMock, patch
from app.utils import nuclei_executor as executor
import subprocess
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from app.utils import nuclei_executor as executor


def test_parse_json_line_valid():
    data = {"info": {"name": "XSS"}, "type": "vulnerability"}
    line = json.dumps(data)
    parsed = executor._parse_json_line_(line)
    assert parsed["info"]["name"] == "XSS"


def test_parse_json_line_invalid():
    assert executor._parse_json_line_("not json") is None


@patch("subprocess.Popen")
def test_start_nuclei_process(mock_popen):
    mock_process = MagicMock()
    mock_popen.return_value = mock_process

    process = executor._start_nuclei_process("https://example.com")

    assert process is mock_process
    mock_popen.assert_called_once()
    args, kwargs = mock_popen.call_args
    assert "nuclei" in args[0][0]
    assert "-u" in args[0]


def test_consume_output_adds_findings(mocker, test_app):
    fake_output = io.StringIO(json.dumps({"info": {"name": "SQLi"}}) + "\n")
    process = MagicMock(stdout=fake_output)

    session = mocker.MagicMock()
    executor._consume_output(process, scan_id="123", session=session)

    session.add.assert_called()
    session.commit.assert_called()

def test_update_status_sets_status_and_commits():
    scan = SimpleNamespace(status=None)
    session = MagicMock()

    executor._update_status(scan, "scanning", session)

    assert scan.status == "scanning"
    session.commit.assert_called_once()


def test_finalize_scan_completed_calls_wait_and_sets_completed(caplog):
    process = MagicMock()
    process.wait.return_value = 0
    process.stderr = None

    scan = SimpleNamespace(status=None)
    session = MagicMock()

    executor._finalize_scan(process, scan, session)

    assert scan.status == "completed"
    session.commit.assert_called()


def test_finalize_scan_failed_logs_stderr(caplog):
    process = MagicMock()
    process.wait.return_value = 2
    stderr = MagicMock()
    stderr.read.return_value = "some error\n"
    process.stderr = stderr

    scan = SimpleNamespace(status=None)
    session = MagicMock()

    caplog.clear()
    caplog.set_level("ERROR")

    executor._finalize_scan(process, scan, session)

    assert scan.status == "failed"
    assert any("Nuclei finished with an error" in rec.message for rec in caplog.records)


def test_finalize_scan_timeout_kills_process_and_logs(caplog):
    process = MagicMock()
    process.wait.side_effect = subprocess.TimeoutExpired(cmd="nuclei", timeout=600)
    process.kill = MagicMock()
    process.stderr = None

    scan = SimpleNamespace(status=None)
    session = MagicMock()

    caplog.clear()
    caplog.set_level("ERROR")

    executor._finalize_scan(process, scan, session)

    process.kill.assert_called_once()
    assert any("Nuclei scan timeout" in rec.message for rec in caplog.records)
    assert scan.status == "failed"


def test_consume_output_adds_findings_and_ignores_blank_lines():
    lines = ["\x1b[0m{\"info\": {\"name\": \"SQLi\"}}\n", "\n", "   \n"]
    process = SimpleNamespace(stdout=lines)

    session = MagicMock()

    executor._consume_output(process, scan_id="scan123", session=session)

    assert session.add.called
    assert session.commit.called


def test_start_nuclei_process_invokes_popen():
    with patch("app.utils.nuclei_executor.subprocess.Popen") as mock_popen:
        mock_process = MagicMock()
        mock_popen.return_value = mock_process

        proc = executor._start_nuclei_process("https://example.com")

        assert proc is mock_process
        mock_popen.assert_called_once()
        args, kwargs = mock_popen.call_args
        assert isinstance(args[0], list)
        assert "nuclei" in args[0][0]
