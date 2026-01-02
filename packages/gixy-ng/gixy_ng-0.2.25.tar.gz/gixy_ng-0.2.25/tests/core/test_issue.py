"""Tests for Issue and Fix classes."""

from gixy.core.issue import Fix, Issue


class TestFix:
    """Tests for the Fix class."""

    def test_fix_creation(self):
        """Test creating a Fix with all fields."""
        fix = Fix(
            title="Replace $http_host with $host",
            search="$http_host",
            replace="$host",
            description="Use $host which is safer",
        )
        assert fix.title == "Replace $http_host with $host"
        assert fix.search == "$http_host"
        assert fix.replace == "$host"
        assert fix.description == "Use $host which is safer"

    def test_fix_without_description(self):
        """Test creating a Fix without description."""
        fix = Fix(
            title="Set server_tokens off",
            search="server_tokens on",
            replace="server_tokens off",
        )
        assert fix.title == "Set server_tokens off"
        assert fix.description is None

    def test_fix_to_dict(self):
        """Test Fix.to_dict() serialization."""
        fix = Fix(
            title="Replace $http_host with $host",
            search="$http_host",
            replace="$host",
            description="Use $host which is safer",
        )
        result = fix.to_dict()
        assert result == {
            "title": "Replace $http_host with $host",
            "search": "$http_host",
            "replace": "$host",
            "description": "Use $host which is safer",
        }

    def test_fix_to_dict_without_description(self):
        """Test Fix.to_dict() without description field."""
        fix = Fix(
            title="Set server_tokens off",
            search="server_tokens on",
            replace="server_tokens off",
        )
        result = fix.to_dict()
        assert result == {
            "title": "Set server_tokens off",
            "search": "server_tokens on",
            "replace": "server_tokens off",
        }
        assert "description" not in result


class TestIssue:
    """Tests for the Issue class."""

    def test_issue_with_fixes(self):
        """Test creating an Issue with fixes."""
        fix1 = Fix("Fix 1", "search1", "replace1")
        fix2 = Fix("Fix 2", "search2", "replace2")

        issue = Issue(
            plugin=None,
            summary="Test issue",
            fixes=[fix1, fix2],
        )
        assert len(issue.fixes) == 2
        assert issue.fixes[0].title == "Fix 1"
        assert issue.fixes[1].title == "Fix 2"

    def test_issue_with_single_fix(self):
        """Test creating an Issue with a single Fix (not a list)."""
        fix = Fix("Single fix", "search", "replace")

        issue = Issue(
            plugin=None,
            summary="Test issue",
            fixes=fix,
        )
        assert len(issue.fixes) == 1
        assert issue.fixes[0].title == "Single fix"

    def test_issue_without_fixes(self):
        """Test creating an Issue without fixes."""
        issue = Issue(
            plugin=None,
            summary="Test issue",
        )
        assert issue.fixes == []

    def test_issue_with_none_fixes(self):
        """Test creating an Issue with fixes=None."""
        issue = Issue(
            plugin=None,
            summary="Test issue",
            fixes=None,
        )
        assert issue.fixes == []
