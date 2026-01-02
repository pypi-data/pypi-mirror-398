import re

import gixy
from gixy.plugins.plugin import Plugin

# =============================================================================
# Value-Aware Security Header Classification
# =============================================================================
# Instead of blindly classifying headers as "secure" or "not secure", we
# analyze the ACTUAL VALUE to determine security intent.
#
# Example: Cache-Control
#   - "no-store" → Security-protective (prevents sensitive data caching)
#   - "public, max-age=3600" → Performance optimization (not security)
#
# This eliminates false positives while catching real security regressions.
# =============================================================================

CONDITIONAL_SECURITY_HEADERS = {
    # Cache-Control: only security-protective when it restricts caching
    "cache-control": {
        "patterns": ["no-store", "no-cache", "private", "must-revalidate"],
        "use_regex": False,
    },
    # Pragma: legacy cache control
    "pragma": {
        "patterns": ["no-cache"],
        "use_regex": False,
    },
    # Expires: security-protective when set to prevent caching (0, -1, epoch)
    "expires": {
        # Matches: "0", "-1", negative numbers, or epoch date "1970"
        "patterns": [r"^0$", r"^-\d+$", r"1970"],
        "use_regex": True,
    },
    # Content-Disposition: "attachment" prevents inline execution (XSS prevention)
    "content-disposition": {
        "patterns": ["attachment"],
        "use_regex": False,
    },
    # X-Download-Options: "noopen" prevents automatic execution in IE
    "x-download-options": {
        "patterns": ["noopen"],
        "use_regex": False,
    },
}


def is_security_protective_value(header_name, values):
    """
    Determine if a header's value(s) indicate security-protective intent.

    Returns True if any of the header values match security patterns,
    meaning dropping this header would be a security regression.

    Args:
        header_name: The header name (will be lowercased)
        values: List of header values from the parent context

    Returns:
        bool: True if dropping this header is a security concern
    """
    header_lower = header_name.lower()

    if header_lower not in CONDITIONAL_SECURITY_HEADERS:
        return False

    rules = CONDITIONAL_SECURITY_HEADERS[header_lower]
    patterns = rules["patterns"]
    use_regex = rules.get("use_regex", False)

    for value in values:
        value_lower = value.lower()

        for pattern in patterns:
            if use_regex:
                if re.search(pattern, value_lower, re.IGNORECASE):
                    return True
            else:
                # Simple substring match (case-insensitive)
                if pattern.lower() in value_lower:
                    return True

    return False


class add_header_redefinition(Plugin):
    """
    Detects when nested add_header directives silently drop parent headers.

    Insecure example:
        server {
            add_header X-Content-Type-Options nosniff;
            location / {
                add_header X-Frame-Options DENY;
            }
        }

    In this example, the location block's add_header REPLACES all parent
    headers, so X-Content-Type-Options is silently dropped.

    Safe with nginx 1.29.3+ using add_header_inherit:
        server {
            add_header X-Content-Type-Options nosniff;
            location / {
                add_header_inherit on;
                add_header X-Frame-Options DENY;
            }
        }

    Severity Classification:
        MEDIUM - When dropping headers that are always security-critical
                 (CSP, HSTS, X-Frame-Options, etc.) OR when dropping
                 headers with security-protective values (e.g.,
                 Cache-Control: no-store)
        LOW    - When dropping headers that aren't security-critical
                 (e.g., Cache-Control: public, max-age=3600)
    """

    summary = 'Nested "add_header" drops parent headers.'
    severity = gixy.severity.LOW
    description = (
        '"add_header" replaces ALL parent headers. '
        "See documentation: https://nginx.org/en/docs/http/ngx_http_headers_module.html#add_header "
        'Note: nginx 1.29.3+ supports "add_header_inherit on;" to inherit parent headers.'
    )
    directives = ["server", "location", "if"]
    options = {"headers": set()}
    options_help = {
        "headers": "Only report dropped headers from this allowlist. Case-insensitive. Comma-separated list."
    }

    def __init__(self, config):
        super(add_header_redefinition, self).__init__(config)
        raw_headers = self.config.get("headers")
        # Normalize configured headers to lowercase set for case-insensitive matching
        if isinstance(raw_headers, (list, tuple, set)):
            self.interesting_headers = {
                h.lower().strip() for h in raw_headers if h and isinstance(h, str)
            }
        else:
            self.interesting_headers = set()

        # Headers that are ALWAYS security-sensitive (regardless of value)
        # These are headers whose very presence provides security protection
        self.always_secure_headers = frozenset(
            [
                "content-security-policy",
                "content-security-policy-report-only",
                "cross-origin-embedder-policy",
                "cross-origin-opener-policy",
                "cross-origin-resource-policy",
                "permissions-policy",
                "referrer-policy",
                "strict-transport-security",
                "x-content-type-options",
                "x-frame-options",
                "x-xss-protection",
                "x-permitted-cross-domain-policies",
            ]
        )

    def audit(self, directive):
        if not directive.is_block:
            return

        actual_headers_map = get_headers(directive)
        actual_headers = set(actual_headers_map.keys())
        if not actual_headers:
            return

        # Check if add_header_inherit is enabled (nginx 1.29.3+)
        if has_header_inherit(directive):
            return

        for parent in directive.parents:
            parent_headers_map = get_headers(parent)
            parent_headers = set(parent_headers_map.keys())
            if not parent_headers:
                continue

            diff = parent_headers - actual_headers

            if self.interesting_headers:
                diff = diff & self.interesting_headers

            if diff:
                self._report_issue(directive, parent, diff, parent_headers_map)

            break

    def _report_issue(self, current, parent, diff, parent_headers_map):
        directives = []
        directives.extend(parent.find("add_header"))
        directives.extend(current.find("add_header"))

        # Determine severity using intelligent classification
        is_secure_header_dropped = False

        for header in diff:
            # Check 1: Is it an always-secure header? (CSP, HSTS, etc.)
            if header in self.always_secure_headers:
                is_secure_header_dropped = True
                break

            # Check 2: Is it a conditionally-secure header with security-protective value?
            # e.g., Cache-Control: no-store is security-protective
            #       Cache-Control: public is not
            if header in CONDITIONAL_SECURITY_HEADERS:
                values = parent_headers_map.get(header, [])
                if is_security_protective_value(header, values):
                    is_secure_header_dropped = True
                    break

        issue_severity = (
            gixy.severity.MEDIUM if is_secure_header_dropped else self.severity
        )
        reason = 'Parent header(s) "{headers}" dropped in nested block'.format(
            headers='", "'.join(sorted(diff))
        )
        self.add_issue(directive=directives, reason=reason, severity=issue_severity)


def get_headers(directive):
    """Get headers as a dict mapping header name (lowercase) -> list of values."""
    headers_list = directive.find("add_header")
    if not headers_list:
        return {}

    result = {}
    for d in headers_list:
        header = d.header.lower()
        if header not in result:
            result[header] = []
        result[header].append(d.value)
    return result


def has_header_inherit(directive):
    """
    Check if add_header_inherit is enabled in the directive.

    nginx 1.29.3+ supports 'add_header_inherit on;' which causes headers
    to be inherited from parent levels, making the redefinition warning
    unnecessary.
    """
    inherit_directives = directive.find("add_header_inherit")
    if not inherit_directives:
        return False

    for d in inherit_directives:
        if d.args and d.args[0].lower() == "on":
            return True

    return False
