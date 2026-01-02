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
        config = Config(plugins=["hsts_header"])
        with Manager(config=config) as manager:
            # Manager.audit ignores file_data for non-stdin paths, but requires it as an arg.
            with open(path) as fdata:
                manager.audit(path, fdata)
            return list(manager.results)
    finally:
        os.unlink(path)


def test_missing_hsts_is_reported_for_normal_https_server():
    config = """
    http {
        server {
            listen 443 ssl;

            # Intentionally missing Strict-Transport-Security
            location / {
                return 200 "ok";
            }
        }
    }
    """

    plugins = _audit_config(config)
    assert len(plugins) == 1
    assert plugins[0].name == "hsts_header"

    summaries = [issue.summary for issue in plugins[0].issues]
    assert "Missing HSTS header" in summaries


def test_ssl_reject_handshake_server_does_not_require_hsts():
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
