class Fix:
    """
    Represents a suggested fix for an issue.

    Fixes can be used by IDE integrations to offer quick-fix functionality.

    Attributes:
        title: Human-readable title for the fix (shown in IDE menus).
        search: Text pattern to find in the problematic line.
        replace: Text to replace the search pattern with.
        description: Optional longer description of what the fix does.
    """

    def __init__(self, title, search, replace, description=None):
        self.title = title
        self.search = search
        self.replace = replace
        self.description = description

    def to_dict(self):
        """Convert fix to dictionary for JSON serialization."""
        result = {
            "title": self.title,
            "search": self.search,
            "replace": self.replace,
        }
        if self.description:
            result["description"] = self.description
        return result


class Issue:
    """
    Represents a security issue found by a plugin.

    Attributes:
        plugin: The plugin that found this issue.
        summary: Short description of the issue.
        description: Detailed description of the issue.
        severity: Severity level (HIGH, MEDIUM, LOW, UNSPECIFIED).
        reason: Specific reason for this instance of the issue.
        help_url: URL to documentation about this issue.
        directives: List of directives involved in the issue.
        fixes: List of Fix objects with suggested remediations.
    """

    def __init__(
        self,
        plugin,
        summary=None,
        description=None,
        severity=None,
        reason=None,
        help_url=None,
        directives=None,
        fixes=None,
    ):
        self.plugin = plugin
        self.summary = summary
        self.description = description
        self.severity = severity
        self.reason = reason
        self.help_url = help_url
        if not directives:
            self.directives = []
        elif not hasattr(directives, "__iter__"):
            self.directives = [directives]
        else:
            self.directives = directives

        # Fixes for IDE integrations
        if not fixes:
            self.fixes = []
        elif isinstance(fixes, Fix):
            self.fixes = [fixes]
        else:
            self.fixes = list(fixes)
