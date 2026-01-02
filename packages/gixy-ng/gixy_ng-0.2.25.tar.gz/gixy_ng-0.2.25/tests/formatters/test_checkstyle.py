"""Comprehensive tests for the Checkstyle XML formatter."""

import xml.etree.ElementTree as ET

import pytest


class TestCheckstyleFormatterAvailability:
    """Tests for formatter registration and availability."""

    def test_checkstyle_formatter_available(self):
        """Test that checkstyle formatter is registered and available."""
        from gixy.formatters import get_all

        formatters = get_all()
        assert "checkstyle" in formatters

    def test_checkstyle_formatter_instantiation(self):
        """Test that formatter can be instantiated."""
        from gixy.formatters import get_all

        formatter_cls = get_all()["checkstyle"]
        formatter = formatter_cls()
        assert formatter is not None


class TestCheckstyleXMLStructure:
    """Tests for XML structure and validity."""

    @pytest.fixture
    def formatter(self):
        """Create a fresh formatter instance."""
        from gixy.formatters import get_all

        return get_all()["checkstyle"]()

    def test_output_is_valid_xml(self, formatter):
        """Test that output is valid, parseable XML."""
        reports = {"/test/nginx.conf": []}
        stats = {"HIGH": 0, "MEDIUM": 0, "LOW": 0, "UNSPECIFIED": 0}

        output = formatter.format_reports(reports, stats)

        # Should not raise an exception
        root = ET.fromstring(output)
        assert root is not None

    def test_xml_declaration_present(self, formatter):
        """Test that XML declaration is included."""
        reports = {"/test/nginx.conf": []}
        stats = {"HIGH": 0, "MEDIUM": 0, "LOW": 0, "UNSPECIFIED": 0}

        output = formatter.format_reports(reports, stats)

        assert output.startswith('<?xml version="1.0" encoding="UTF-8"?>')

    def test_checkstyle_root_element(self, formatter):
        """Test that root element is 'checkstyle' with version attribute."""
        reports = {"/test/nginx.conf": []}
        stats = {"HIGH": 0, "MEDIUM": 0, "LOW": 0, "UNSPECIFIED": 0}

        output = formatter.format_reports(reports, stats)
        root = ET.fromstring(output)

        assert root.tag == "checkstyle"
        assert root.get("version") == "8.0"

    def test_file_elements_created(self, formatter):
        """Test that file elements are created for each path."""
        reports = {
            "/etc/nginx/nginx.conf": [],
            "/etc/nginx/conf.d/default.conf": [],
        }
        stats = {"HIGH": 0, "MEDIUM": 0, "LOW": 0, "UNSPECIFIED": 0}

        output = formatter.format_reports(reports, stats)
        root = ET.fromstring(output)

        file_elements = root.findall("file")
        assert len(file_elements) == 2

        paths = [f.get("name") for f in file_elements]
        assert "/etc/nginx/nginx.conf" in paths
        assert "/etc/nginx/conf.d/default.conf" in paths

    def test_error_elements_have_required_attributes(self, formatter):
        """Test that error elements have all required Checkstyle attributes."""
        reports = {
            "/test/nginx.conf": [
                {
                    "plugin": "test_plugin",
                    "summary": "Test summary",
                    "severity": "HIGH",
                    "description": "Test description",
                    "help_url": "https://example.com",
                    "reason": "Test reason",
                    "config": "test config",
                    "location": {"line": 42, "file": "/test/nginx.conf"},
                }
            ]
        }
        stats = {"HIGH": 1, "MEDIUM": 0, "LOW": 0, "UNSPECIFIED": 0}

        output = formatter.format_reports(reports, stats)
        root = ET.fromstring(output)

        error = root.find(".//error")
        assert error is not None

        # Check all required Checkstyle attributes
        assert error.get("line") == "42"
        assert error.get("column") == "1"
        assert error.get("severity") == "error"
        assert error.get("message") is not None
        assert error.get("source") is not None


class TestCheckstyleSeverityMapping:
    """Tests for severity level mapping."""

    @pytest.fixture
    def formatter(self):
        from gixy.formatters import get_all

        return get_all()["checkstyle"]()

    @pytest.mark.parametrize(
        "gixy_severity,expected_checkstyle",
        [
            ("HIGH", "error"),
            ("MEDIUM", "warning"),
            ("LOW", "info"),
            ("UNSPECIFIED", "info"),
        ],
    )
    def test_severity_mapping(self, formatter, gixy_severity, expected_checkstyle):
        """Test that gixy severities map correctly to Checkstyle severities."""
        reports = {
            "/test/nginx.conf": [
                {
                    "plugin": "test",
                    "summary": "Test",
                    "severity": gixy_severity,
                    "description": "",
                    "help_url": "",
                    "reason": "",
                    "config": "",
                }
            ]
        }
        stats = {gixy_severity: 1, "HIGH": 0, "MEDIUM": 0, "LOW": 0, "UNSPECIFIED": 0}

        output = formatter.format_reports(reports, stats)
        root = ET.fromstring(output)

        error = root.find(".//error")
        assert error.get("severity") == expected_checkstyle

    def test_unknown_severity_defaults_to_info(self, formatter):
        """Test that unknown severity defaults to 'info'."""
        reports = {
            "/test/nginx.conf": [
                {
                    "plugin": "test",
                    "summary": "Test",
                    "severity": "UNKNOWN_SEVERITY",
                    "description": "",
                    "help_url": "",
                    "reason": "",
                    "config": "",
                }
            ]
        }
        stats = {"HIGH": 0, "MEDIUM": 0, "LOW": 0, "UNSPECIFIED": 0}

        output = formatter.format_reports(reports, stats)
        root = ET.fromstring(output)

        error = root.find(".//error")
        assert error.get("severity") == "info"


class TestCheckstyleMessageFormatting:
    """Tests for message content formatting."""

    @pytest.fixture
    def formatter(self):
        from gixy.formatters import get_all

        return get_all()["checkstyle"]()

    def test_message_includes_plugin_name(self, formatter):
        """Test that message includes the plugin name in brackets."""
        reports = {
            "/test/nginx.conf": [
                {
                    "plugin": "ssrf",
                    "summary": "SSRF vulnerability",
                    "severity": "HIGH",
                    "description": "",
                    "help_url": "",
                    "reason": "User input in proxy_pass",
                    "config": "",
                }
            ]
        }
        stats = {"HIGH": 1, "MEDIUM": 0, "LOW": 0, "UNSPECIFIED": 0}

        output = formatter.format_reports(reports, stats)
        root = ET.fromstring(output)

        error = root.find(".//error")
        message = error.get("message")
        assert message.startswith("[ssrf]")

    def test_message_includes_summary_and_reason(self, formatter):
        """Test that message includes both summary and reason."""
        reports = {
            "/test/nginx.conf": [
                {
                    "plugin": "host_spoofing",
                    "summary": "Host header spoofing",
                    "severity": "MEDIUM",
                    "description": "",
                    "help_url": "",
                    "reason": "Using $http_host instead of $host",
                    "config": "",
                }
            ]
        }
        stats = {"HIGH": 0, "MEDIUM": 1, "LOW": 0, "UNSPECIFIED": 0}

        output = formatter.format_reports(reports, stats)
        root = ET.fromstring(output)

        error = root.find(".//error")
        message = error.get("message")
        assert "Host header spoofing" in message
        assert "Using $http_host instead of $host" in message

    def test_message_without_reason(self, formatter):
        """Test message formatting when reason is empty."""
        reports = {
            "/test/nginx.conf": [
                {
                    "plugin": "test",
                    "summary": "Test summary",
                    "severity": "LOW",
                    "description": "",
                    "help_url": "",
                    "reason": "",
                    "config": "",
                }
            ]
        }
        stats = {"HIGH": 0, "MEDIUM": 0, "LOW": 1, "UNSPECIFIED": 0}

        output = formatter.format_reports(reports, stats)
        root = ET.fromstring(output)

        error = root.find(".//error")
        message = error.get("message")
        # Should not have trailing colon when no reason
        assert message == "[test] Test summary"

    def test_source_attribute_format(self, formatter):
        """Test that source attribute follows gixy.plugin_name format."""
        reports = {
            "/test/nginx.conf": [
                {
                    "plugin": "add_header_redefinition",
                    "summary": "Test",
                    "severity": "MEDIUM",
                    "description": "",
                    "help_url": "",
                    "reason": "",
                    "config": "",
                }
            ]
        }
        stats = {"HIGH": 0, "MEDIUM": 1, "LOW": 0, "UNSPECIFIED": 0}

        output = formatter.format_reports(reports, stats)
        root = ET.fromstring(output)

        error = root.find(".//error")
        assert error.get("source") == "gixy.add_header_redefinition"


class TestCheckstyleLineNumbers:
    """Tests for line number handling."""

    @pytest.fixture
    def formatter(self):
        from gixy.formatters import get_all

        return get_all()["checkstyle"]()

    def test_line_number_from_location(self, formatter):
        """Test that line number is extracted from location."""
        reports = {
            "/test/nginx.conf": [
                {
                    "plugin": "test",
                    "summary": "Test",
                    "severity": "HIGH",
                    "description": "",
                    "help_url": "",
                    "reason": "",
                    "config": "",
                    "location": {"line": 123, "file": "/test/nginx.conf"},
                }
            ]
        }
        stats = {"HIGH": 1, "MEDIUM": 0, "LOW": 0, "UNSPECIFIED": 0}

        output = formatter.format_reports(reports, stats)
        root = ET.fromstring(output)

        error = root.find(".//error")
        assert error.get("line") == "123"

    def test_line_defaults_to_one_when_missing(self, formatter):
        """Test that line defaults to 1 when location is missing."""
        reports = {
            "/test/nginx.conf": [
                {
                    "plugin": "test",
                    "summary": "Test",
                    "severity": "HIGH",
                    "description": "",
                    "help_url": "",
                    "reason": "",
                    "config": "",
                }
            ]
        }
        stats = {"HIGH": 1, "MEDIUM": 0, "LOW": 0, "UNSPECIFIED": 0}

        output = formatter.format_reports(reports, stats)
        root = ET.fromstring(output)

        error = root.find(".//error")
        assert error.get("line") == "1"

    def test_line_defaults_when_location_is_none(self, formatter):
        """Test line defaults to 1 when location is explicitly None."""
        reports = {
            "/test/nginx.conf": [
                {
                    "plugin": "test",
                    "summary": "Test",
                    "severity": "HIGH",
                    "description": "",
                    "help_url": "",
                    "reason": "",
                    "config": "",
                    "location": None,
                }
            ]
        }
        stats = {"HIGH": 1, "MEDIUM": 0, "LOW": 0, "UNSPECIFIED": 0}

        output = formatter.format_reports(reports, stats)
        root = ET.fromstring(output)

        error = root.find(".//error")
        assert error.get("line") == "1"

    def test_column_always_one(self, formatter):
        """Test that column is always 1 (nginx doesn't track columns)."""
        reports = {
            "/test/nginx.conf": [
                {
                    "plugin": "test",
                    "summary": "Test",
                    "severity": "HIGH",
                    "description": "",
                    "help_url": "",
                    "reason": "",
                    "config": "",
                    "location": {"line": 50, "file": "/test/nginx.conf"},
                }
            ]
        }
        stats = {"HIGH": 1, "MEDIUM": 0, "LOW": 0, "UNSPECIFIED": 0}

        output = formatter.format_reports(reports, stats)
        root = ET.fromstring(output)

        error = root.find(".//error")
        assert error.get("column") == "1"


class TestCheckstyleMultipleIssues:
    """Tests for handling multiple issues."""

    @pytest.fixture
    def formatter(self):
        from gixy.formatters import get_all

        return get_all()["checkstyle"]()

    def test_multiple_issues_in_same_file(self, formatter):
        """Test handling multiple issues in the same file."""
        reports = {
            "/test/nginx.conf": [
                {
                    "plugin": "ssrf",
                    "summary": "SSRF",
                    "severity": "HIGH",
                    "description": "",
                    "help_url": "",
                    "reason": "reason1",
                    "config": "",
                    "location": {"line": 10, "file": "/test/nginx.conf"},
                },
                {
                    "plugin": "host_spoofing",
                    "summary": "Host spoofing",
                    "severity": "MEDIUM",
                    "description": "",
                    "help_url": "",
                    "reason": "reason2",
                    "config": "",
                    "location": {"line": 25, "file": "/test/nginx.conf"},
                },
                {
                    "plugin": "version_disclosure",
                    "summary": "Version disclosed",
                    "severity": "LOW",
                    "description": "",
                    "help_url": "",
                    "reason": "reason3",
                    "config": "",
                    "location": {"line": 5, "file": "/test/nginx.conf"},
                },
            ]
        }
        stats = {"HIGH": 1, "MEDIUM": 1, "LOW": 1, "UNSPECIFIED": 0}

        output = formatter.format_reports(reports, stats)
        root = ET.fromstring(output)

        errors = root.findall(".//error")
        assert len(errors) == 3

        # Check all sources are present
        sources = [e.get("source") for e in errors]
        assert "gixy.ssrf" in sources
        assert "gixy.host_spoofing" in sources
        assert "gixy.version_disclosure" in sources

    def test_issues_across_multiple_files(self, formatter):
        """Test handling issues in different files."""
        reports = {
            "/etc/nginx/nginx.conf": [
                {
                    "plugin": "ssrf",
                    "summary": "SSRF",
                    "severity": "HIGH",
                    "description": "",
                    "help_url": "",
                    "reason": "",
                    "config": "",
                    "location": {"line": 10, "file": "/etc/nginx/nginx.conf"},
                }
            ],
            "/etc/nginx/conf.d/api.conf": [
                {
                    "plugin": "host_spoofing",
                    "summary": "Spoofing",
                    "severity": "MEDIUM",
                    "description": "",
                    "help_url": "",
                    "reason": "",
                    "config": "",
                    "location": {"line": 5, "file": "/etc/nginx/conf.d/api.conf"},
                }
            ],
        }
        stats = {"HIGH": 1, "MEDIUM": 1, "LOW": 0, "UNSPECIFIED": 0}

        output = formatter.format_reports(reports, stats)
        root = ET.fromstring(output)

        files = root.findall("file")
        assert len(files) == 2

        # Each file should have one error
        for file_elem in files:
            errors = file_elem.findall("error")
            assert len(errors) == 1


class TestCheckstyleEmptyReports:
    """Tests for empty/no-issue scenarios."""

    @pytest.fixture
    def formatter(self):
        from gixy.formatters import get_all

        return get_all()["checkstyle"]()

    def test_no_issues_produces_empty_file_elements(self, formatter):
        """Test that files with no issues still get file elements."""
        reports = {"/test/nginx.conf": []}
        stats = {"HIGH": 0, "MEDIUM": 0, "LOW": 0, "UNSPECIFIED": 0}

        output = formatter.format_reports(reports, stats)
        root = ET.fromstring(output)

        files = root.findall("file")
        assert len(files) == 1
        assert files[0].get("name") == "/test/nginx.conf"

        # No error children
        errors = files[0].findall("error")
        assert len(errors) == 0

    def test_empty_reports_dict(self, formatter):
        """Test handling completely empty reports."""
        reports = {}
        stats = {"HIGH": 0, "MEDIUM": 0, "LOW": 0, "UNSPECIFIED": 0}

        output = formatter.format_reports(reports, stats)
        root = ET.fromstring(output)

        # Should have valid XML with no file elements
        assert root.tag == "checkstyle"
        files = root.findall("file")
        assert len(files) == 0


class TestCheckstyleSpecialCharacters:
    """Tests for XML special character handling."""

    @pytest.fixture
    def formatter(self):
        from gixy.formatters import get_all

        return get_all()["checkstyle"]()

    def test_xml_special_chars_in_message(self, formatter):
        """Test that XML special characters are properly escaped."""
        reports = {
            "/test/nginx.conf": [
                {
                    "plugin": "test",
                    "summary": "Test <script>alert('xss')</script>",
                    "severity": "HIGH",
                    "description": "",
                    "help_url": "",
                    "reason": "Contains & and <> characters",
                    "config": "",
                }
            ]
        }
        stats = {"HIGH": 1, "MEDIUM": 0, "LOW": 0, "UNSPECIFIED": 0}

        output = formatter.format_reports(reports, stats)

        # Should be valid XML (would raise if not properly escaped)
        root = ET.fromstring(output)

        error = root.find(".//error")
        message = error.get("message")
        assert "<script>" in message or "&lt;script&gt;" in output
        assert "&" in message or "&amp;" in output

    def test_quotes_in_message(self, formatter):
        """Test that quotes are properly handled."""
        reports = {
            "/test/nginx.conf": [
                {
                    "plugin": "test",
                    "summary": 'Test "quoted" value',
                    "severity": "HIGH",
                    "description": "",
                    "help_url": "",
                    "reason": "Variable '$http_host' used",
                    "config": "",
                }
            ]
        }
        stats = {"HIGH": 1, "MEDIUM": 0, "LOW": 0, "UNSPECIFIED": 0}

        output = formatter.format_reports(reports, stats)

        # Should be valid XML
        root = ET.fromstring(output)
        error = root.find(".//error")
        assert error is not None

    def test_special_chars_in_filepath(self, formatter):
        """Test handling special characters in file paths."""
        reports = {
            "/etc/nginx/sites-enabled/example.com.conf": [
                {
                    "plugin": "test",
                    "summary": "Test",
                    "severity": "HIGH",
                    "description": "",
                    "help_url": "",
                    "reason": "",
                    "config": "",
                }
            ]
        }
        stats = {"HIGH": 1, "MEDIUM": 0, "LOW": 0, "UNSPECIFIED": 0}

        output = formatter.format_reports(reports, stats)
        root = ET.fromstring(output)

        file_elem = root.find("file")
        assert file_elem.get("name") == "/etc/nginx/sites-enabled/example.com.conf"


class TestCheckstyleIncludedFiles:
    """Tests for handling issues in included files."""

    @pytest.fixture
    def formatter(self):
        from gixy.formatters import get_all

        return get_all()["checkstyle"]()

    def test_issue_in_included_file(self, formatter):
        """Test that issues report the correct file from location."""
        reports = {
            "/etc/nginx/nginx.conf": [
                {
                    "plugin": "ssrf",
                    "summary": "SSRF",
                    "severity": "HIGH",
                    "description": "",
                    "help_url": "",
                    "reason": "",
                    "config": "",
                    "location": {
                        "line": 15,
                        "file": "/etc/nginx/conf.d/included.conf",
                    },
                }
            ]
        }
        stats = {"HIGH": 1, "MEDIUM": 0, "LOW": 0, "UNSPECIFIED": 0}

        output = formatter.format_reports(reports, stats)
        root = ET.fromstring(output)

        # Should create file element for the included file
        files = root.findall("file")
        file_names = [f.get("name") for f in files]

        # The included file should be present
        assert "/etc/nginx/conf.d/included.conf" in file_names


class TestCheckstyleRealWorldScenarios:
    """Integration-style tests with realistic data."""

    @pytest.fixture
    def formatter(self):
        from gixy.formatters import get_all

        return get_all()["checkstyle"]()

    def test_realistic_ssrf_issue(self, formatter):
        """Test formatting a realistic SSRF issue."""
        reports = {
            "/etc/nginx/sites-enabled/api.conf": [
                {
                    "plugin": "ssrf",
                    "summary": "Possible SSRF vulnerability",
                    "severity": "HIGH",
                    "description": "Server Side Request Forgery",
                    "help_url": "https://gixy.getpagespeed.com/plugins/ssrf/",
                    "reason": 'Variable "$backend" can be controlled by user',
                    "config": "proxy_pass http://$backend;",
                    "location": {
                        "line": 42,
                        "file": "/etc/nginx/sites-enabled/api.conf",
                    },
                }
            ]
        }
        stats = {"HIGH": 1, "MEDIUM": 0, "LOW": 0, "UNSPECIFIED": 0}

        output = formatter.format_reports(reports, stats)
        root = ET.fromstring(output)

        error = root.find(".//error")
        assert error.get("line") == "42"
        assert error.get("severity") == "error"
        assert "ssrf" in error.get("source")
        assert "$backend" in error.get("message")

    def test_realistic_multi_issue_config(self, formatter):
        """Test formatting multiple issues like a real scan would produce."""
        reports = {
            "/etc/nginx/nginx.conf": [
                {
                    "plugin": "version_disclosure",
                    "summary": "Server version disclosed",
                    "severity": "LOW",
                    "description": "",
                    "help_url": "",
                    "reason": "server_tokens is on",
                    "config": "server_tokens on;",
                    "location": {"line": 3, "file": "/etc/nginx/nginx.conf"},
                },
                {
                    "plugin": "host_spoofing",
                    "summary": "Host header spoofing possible",
                    "severity": "MEDIUM",
                    "description": "",
                    "help_url": "",
                    "reason": "Using $http_host",
                    "config": "proxy_set_header Host $http_host;",
                    "location": {"line": 28, "file": "/etc/nginx/nginx.conf"},
                },
                {
                    "plugin": "ssrf",
                    "summary": "SSRF vulnerability",
                    "severity": "HIGH",
                    "description": "",
                    "help_url": "",
                    "reason": "User controls backend",
                    "config": "proxy_pass http://$arg_url;",
                    "location": {"line": 35, "file": "/etc/nginx/nginx.conf"},
                },
            ]
        }
        stats = {"HIGH": 1, "MEDIUM": 1, "LOW": 1, "UNSPECIFIED": 0}

        output = formatter.format_reports(reports, stats)
        root = ET.fromstring(output)

        errors = root.findall(".//error")
        assert len(errors) == 3

        # Check severities are correctly mapped
        severities = [e.get("severity") for e in errors]
        assert "error" in severities  # HIGH
        assert "warning" in severities  # MEDIUM
        assert "info" in severities  # LOW

    def test_output_consumable_by_ci_tools(self, formatter):
        """Test that output format matches what CI tools expect."""
        reports = {
            "/etc/nginx/nginx.conf": [
                {
                    "plugin": "test",
                    "summary": "Test issue",
                    "severity": "HIGH",
                    "description": "",
                    "help_url": "",
                    "reason": "Test reason",
                    "config": "",
                    "location": {"line": 10, "file": "/etc/nginx/nginx.conf"},
                }
            ]
        }
        stats = {"HIGH": 1, "MEDIUM": 0, "LOW": 0, "UNSPECIFIED": 0}

        output = formatter.format_reports(reports, stats)

        # Verify format matches Checkstyle 8.0 schema expectations
        assert '<?xml version="1.0" encoding="UTF-8"?>' in output
        assert "<checkstyle" in output
        assert 'version="8.0"' in output
        assert "<file" in output
        assert 'name="' in output
        assert "<error" in output
        assert 'line="' in output
        assert 'column="' in output
        assert 'severity="' in output
        assert 'message="' in output
        assert 'source="' in output
