import os
import tempfile

from gixy.core.config import Config
from gixy.core.manager import Manager


def _audit_config(config_text):
    with tempfile.NamedTemporaryFile(mode="w", suffix=".conf", delete=False) as f:
        f.write(config_text)
        f.flush()
        path = f.name

    try:
        config = Config(plugins=["http2_misdirected_request"])
        with Manager(config=config) as manager:
            # Manager.audit ignores file_data for non-stdin paths, but requires it as an arg.
            with open(path) as fdata:
                manager.audit(path, fdata)
            return list(manager.results)
    finally:
        os.unlink(path)


def test_reports_missing_421_for_http2_default_server_reject_handshake():
    config = """
    http {
        server {
            listen 443 ssl default_server;
            http2 on;
            ssl_reject_handshake on;
        }
    }
    """

    plugins = _audit_config(config)
    assert len(plugins) == 1
    assert plugins[0].name == "http2_misdirected_request"
    assert len(plugins[0].issues) == 1
    assert "421" in plugins[0].issues[0].summary


def test_no_report_when_location_returns_421():
    config = """
    http {
        server {
            listen 443 ssl default_server;
            http2 on;
            ssl_reject_handshake on;

            location / {
                return 421;
            }
        }
    }
    """

    plugins = _audit_config(config)
    assert len(plugins) == 0


def test_no_report_without_http2():
    config = """
    http {
        server {
            listen 443 ssl default_server;
            ssl_reject_handshake on;
        }
    }
    """

    plugins = _audit_config(config)
    assert len(plugins) == 0
