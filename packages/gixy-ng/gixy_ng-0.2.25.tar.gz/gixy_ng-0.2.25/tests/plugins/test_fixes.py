"""Tests for plugin quick fixes.

These tests ensure that plugins provide correct fix suggestions in their JSON output.
This prevents regressions in the quick fix functionality used by IDE integrations.
"""

import json

from gixy.core.config import Config
from gixy.core.manager import Manager
from gixy.formatters.json import JsonFormatter


def get_issues_with_fixes(config_content):
    """Helper to run gixy and get issues with fixes from JSON output."""
    manager = Manager(config=Config())

    # Create a temporary config and audit it
    import tempfile
    import os

    with tempfile.NamedTemporaryFile(mode="w", suffix=".conf", delete=False) as f:
        f.write(config_content)
        f.flush()
        temp_path = f.name

    try:
        with open(temp_path) as config_file:
            manager.audit(temp_path, config_file)

        formatter = JsonFormatter()
        formatter.feed(temp_path, manager)
        json_output = formatter.flush()

        return json.loads(json_output)
    finally:
        os.unlink(temp_path)


class TestVersionDisclosureFixes:
    """Tests for version_disclosure plugin fixes."""

    def test_server_tokens_on_has_fix(self):
        """Test that server_tokens on provides a fix to set it off."""
        config = "server { server_tokens on; }"
        issues = get_issues_with_fixes(config)

        version_issues = [i for i in issues if i["plugin"] == "version_disclosure"]
        assert len(version_issues) >= 1

        issue = version_issues[0]
        assert "fixes" in issue
        assert len(issue["fixes"]) >= 1

        fix = issue["fixes"][0]
        assert fix["title"] == "Set server_tokens off"
        assert fix["search"] == "server_tokens on"
        assert fix["replace"] == "server_tokens off"

    def test_server_tokens_build_has_fix(self):
        """Test that server_tokens build provides a fix."""
        config = "server { server_tokens build; }"
        issues = get_issues_with_fixes(config)

        version_issues = [i for i in issues if i["plugin"] == "version_disclosure"]
        assert len(version_issues) >= 1

        issue = version_issues[0]
        assert "fixes" in issue
        fix = issue["fixes"][0]
        assert fix["search"] == "server_tokens build"
        assert fix["replace"] == "server_tokens off"

    def test_server_tokens_on_at_http_level_no_double_report(self):
        """Regression test: server_tokens on at http level should NOT
        cause 'missing' reports at server level.

        Bug: When server_tokens on was at http level, the plugin reported
        both 'server_tokens on' AND 'missing server_tokens' for each server.
        """
        config = """
        http {
            server_tokens on;
            server {
                listen 80;
            }
        }
        """
        issues = get_issues_with_fixes(config)

        version_issues = [i for i in issues if i["plugin"] == "version_disclosure"]

        # Should have exactly 1 issue (for server_tokens on), NOT 2
        assert len(version_issues) == 1, (
            f"Expected 1 issue for 'server_tokens on', got {len(version_issues)}: "
            f"{[i['reason'] for i in version_issues]}"
        )

        # The issue should be about the 'on' value, not 'missing'
        assert (
            "on" in version_issues[0]["reason"].lower()
            or "disclosure" in version_issues[0]["reason"].lower()
        )
        assert "missing" not in version_issues[0]["reason"].lower()

    def test_server_tokens_missing_everywhere_reports_once_per_server(self):
        """When server_tokens is missing entirely, report for each server."""
        config = """
        http {
            server {
                listen 80;
            }
        }
        """
        issues = get_issues_with_fixes(config)

        version_issues = [i for i in issues if i["plugin"] == "version_disclosure"]

        # Should have 1 issue for the missing directive
        assert len(version_issues) == 1
        assert "missing" in version_issues[0]["reason"].lower()


class TestHostSpoofingFixes:
    """Tests for host_spoofing plugin fixes."""

    def test_http_host_has_fix(self):
        """Test that $http_host provides a fix to use $host."""
        config = "server { proxy_set_header Host $http_host; }"
        issues = get_issues_with_fixes(config)

        host_issues = [i for i in issues if i["plugin"] == "host_spoofing"]
        assert len(host_issues) == 1

        issue = host_issues[0]
        assert "fixes" in issue
        assert len(issue["fixes"]) >= 1

        fix = issue["fixes"][0]
        assert fix["title"] == "Replace $http_host with $host"
        assert fix["search"] == "$http_host"
        assert fix["replace"] == "$host"


class TestValidReferersFixes:
    """Tests for valid_referers plugin fixes."""

    def test_none_referer_has_fix(self):
        """Test that valid_referers with none provides a fix to remove it."""
        config = "server { location / { valid_referers none server_names; } }"
        issues = get_issues_with_fixes(config)

        referer_issues = [i for i in issues if i["plugin"] == "valid_referers"]
        assert len(referer_issues) == 1

        issue = referer_issues[0]
        assert "fixes" in issue
        assert len(issue["fixes"]) >= 1

        fix = issue["fixes"][0]
        assert "none" in fix["title"].lower() or "remove" in fix["title"].lower()
        # The fix should remove 'none' from the directive
        assert "none" not in fix["replace"]


class TestErrorLogOffFixes:
    """Tests for error_log_off plugin fixes."""

    def test_error_log_off_has_multiple_fixes(self):
        """Test that error_log off provides multiple fix options."""
        config = "server { error_log off; }"
        issues = get_issues_with_fixes(config)

        error_issues = [i for i in issues if i["plugin"] == "error_log_off"]
        assert len(error_issues) == 1

        issue = error_issues[0]
        assert "fixes" in issue
        # Should have at least 2 options (file path and /dev/null)
        assert len(issue["fixes"]) >= 2

        # First fix should be to use a proper file path
        fix1 = issue["fixes"][0]
        assert fix1["search"] == "error_log off"
        assert "/var/log" in fix1["replace"] or "error_log" in fix1["replace"]


class TestResolverExternalFixes:
    """Tests for resolver_external plugin fixes."""

    def test_external_dns_has_fix(self):
        """Test that external DNS resolver provides a fix to use local."""
        config = "server { resolver 8.8.8.8; }"
        issues = get_issues_with_fixes(config)

        resolver_issues = [i for i in issues if i["plugin"] == "resolver_external"]
        assert len(resolver_issues) == 1

        issue = resolver_issues[0]
        assert "fixes" in issue
        assert len(issue["fixes"]) >= 1

        # Should suggest local resolver
        fix = issue["fixes"][0]
        assert "127.0.0" in fix["replace"] or "local" in fix["title"].lower()


class TestLowKeepaliveRequestsFixes:
    """Tests for low_keepalive_requests plugin fixes."""

    def test_low_value_has_fix(self):
        """Test that low keepalive_requests value provides a fix."""
        config = "server { keepalive_requests 100; }"
        issues = get_issues_with_fixes(config)

        keepalive_issues = [
            i for i in issues if i["plugin"] == "low_keepalive_requests"
        ]
        assert len(keepalive_issues) == 1

        issue = keepalive_issues[0]
        assert "fixes" in issue
        assert len(issue["fixes"]) >= 1

        fix = issue["fixes"][0]
        assert fix["search"] == "keepalive_requests 100"
        assert "1000" in fix["replace"] or "10000" in fix["replace"]


class TestAllowWithoutDenyFixes:
    """Tests for allow_without_deny plugin fixes."""

    def test_allow_without_deny_has_fix(self):
        """Test that allow without deny provides a fix to add deny all."""
        config = "server { location / { allow 192.168.1.0/24; } }"
        issues = get_issues_with_fixes(config)

        allow_issues = [i for i in issues if i["plugin"] == "allow_without_deny"]
        assert len(allow_issues) == 1

        issue = allow_issues[0]
        assert "fixes" in issue
        assert len(issue["fixes"]) >= 1

        fix = issue["fixes"][0]
        assert "deny all" in fix["replace"]


class TestFixesJsonFormat:
    """Tests for the JSON format of fixes."""

    def test_fix_has_required_fields(self):
        """Test that all fixes have required fields."""
        config = "server { server_tokens on; }"
        issues = get_issues_with_fixes(config)

        for issue in issues:
            if "fixes" in issue:
                for fix in issue["fixes"]:
                    assert "title" in fix, "Fix missing 'title' field"
                    assert "search" in fix, "Fix missing 'search' field"
                    assert "replace" in fix, "Fix missing 'replace' field"
                    # description is optional
                    assert isinstance(fix["title"], str)
                    assert isinstance(fix["search"], str)
                    assert isinstance(fix["replace"], str)

    def test_fix_description_is_optional(self):
        """Test that fix description field is optional."""
        config = "server { server_tokens on; }"
        issues = get_issues_with_fixes(config)

        # Just verify the JSON is valid and fixes can have or not have description
        for issue in issues:
            if "fixes" in issue:
                for fix in issue["fixes"]:
                    # description can be present or not
                    if "description" in fix:
                        assert isinstance(fix["description"], str)
