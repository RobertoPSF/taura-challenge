import io
import subprocess
from unittest.mock import MagicMock, patch
from app.utils import katana_executor as executor


def test_consume_output_katana_parses_urls():
    process = MagicMock()
    process.stdout = io.StringIO("https://example.com\nhttp://test.com\n")

    urls = executor._consume_output_katana(process)
    assert urls == ["https://example.com", "http://test.com"]


def test_consume_output_katana_parses_json_urls():
    process = MagicMock()
    process.stdout = io.StringIO('{"url": "https://json.com"}\n')

    urls = executor._consume_output_katana(process)
    assert urls == ["https://json.com"]


@patch("subprocess.Popen")
def test_run_katana_collects_urls(mock_popen):
    fake_output = io.StringIO("https://a.com\nhttps://b.com\n")
    mock_process = MagicMock(stdout=fake_output, stderr=io.StringIO())
    mock_popen.return_value = mock_process

    urls = executor._run_katana("https://target.com")

    assert urls == ["https://a.com", "https://b.com"]
    mock_popen.assert_called_once()
    args, kwargs = mock_popen.call_args
    assert "katana" in args[0][0]


@patch("app.utils.katana_executor._safe_nuclei_call")
def test_run_nuclei_in_parallel(mock_safe_nuclei):
    app = MagicMock()
    Session = MagicMock()
    urls = [f"https://example{i}.com" for i in range(3)]

    executor._run_nuclei_in_parallel("scan123", urls, app, Session)

    assert mock_safe_nuclei.call_count == len(urls)

def test_log_katana_stderr_logs_error(caplog):
    caplog.set_level("ERROR")
    stderr = io.StringIO("\x1b[31merror occurred\n")

    executor._log_stderr(stderr)

    assert any("error occurred" in rec.message for rec in caplog.records)


def test_consume_output_katana_ignores_non_urls():
    process = MagicMock()
    process.stdout = io.StringIO("not a url\n[INF] something\n")

    urls = executor._consume_output_katana(process)
    assert urls == []


@patch("subprocess.Popen")
def test_run_katana_no_stdout_returns_empty(mock_popen):
    mock_process = MagicMock(stdout=None, stderr=io.StringIO())
    mock_popen.return_value = mock_process

    urls = executor._run_katana("http://no-stdout.test")
    assert urls == []


def test_run_nuclei_in_parallel_with_empty_urls_does_nothing():
    app = MagicMock()
    Session = MagicMock()
    urls = []

    with patch("app.utils.katana_executor._safe_nuclei_call") as mock_safe:
        executor._run_nuclei_in_parallel("scanX", urls, app, Session)
        mock_safe.assert_not_called()


def test_safe_nuclei_call_invokes_worker():
    with patch("app.services.nuclei._worker") as mock_worker:
        app = MagicMock()
        Session = MagicMock()
        executor._safe_nuclei_call("scan1", "http://u.test", app, Session)
        mock_worker.assert_called_once()

