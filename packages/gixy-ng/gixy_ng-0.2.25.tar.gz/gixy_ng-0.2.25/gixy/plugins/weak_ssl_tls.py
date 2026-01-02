"""
Plugin to detect weak SSL/TLS configurations in NGINX.

Checks for:
- Outdated protocols (SSLv2, SSLv3, TLSv1, TLSv1.1)
- Weak cipher suites
- Insecure ssl_prefer_server_ciphers settings
"""

import gixy
from gixy.plugins.plugin import Plugin

# Protocols considered insecure
INSECURE_PROTOCOLS = {"SSLv2", "SSLv3", "TLSv1", "TLSv1.1"}

# Weak ciphers that should be avoided
# Based on: https://wiki.mozilla.org/Security/Server_Side_TLS
WEAK_CIPHERS = {
    # Export ciphers (40-bit, 56-bit)
    "EXP",
    "EXPORT",
    "EXPORT40",
    "EXPORT56",
    # NULL ciphers (no encryption)
    "NULL",
    "eNULL",
    "aNULL",
    # DES and 3DES (weak)
    "DES",
    "3DES",
    "DES-CBC3",
    # RC4 (broken)
    "RC4",
    # MD5 (weak hash)
    "MD5",
    # Anonymous ciphers (no authentication)
    "ADH",
    "AECDH",
    # Low-grade ciphers
    "LOW",
    # Medium-grade ciphers (still weak by modern standards)
    "MEDIUM",
    # Camellia (less reviewed than AES)
    "CAMELLIA",
    # SEED (rarely used, less reviewed)
    "SEED",
    # IDEA (old)
    "IDEA",
    # Single DES
    "DES-CBC-SHA",
    # SSLv2 ciphers
    "SSLv2",
}

# Patterns that indicate weak cipher configuration
WEAK_CIPHER_PATTERNS = [
    # Allowing all ciphers
    "ALL",
    "DEFAULT",
    # Specific weak cipher suites
    "RC4-SHA",
    "RC4-MD5",
    "DES-CBC-SHA",
    "DES-CBC3-SHA",
    "EXPORT",
    "EXP-",
    "NULL-",
    "ADH-",
    "AECDH-",
]


class weak_ssl_tls(Plugin):
    """
    Detects weak SSL/TLS configurations that may compromise security.

    Checks ssl_protocols, ssl_ciphers, ssl_prefer_server_ciphers,
    and basic server-level TLS hardening.
    """

    summary = "Weak SSL/TLS configuration detected"
    severity = gixy.severity.HIGH
    description = (
        "Using outdated TLS protocols (TLSv1.0, TLSv1.1) or weak cipher suites "
        "exposes your server to attacks such as POODLE, BEAST, and SWEET32. "
        "Modern configurations should use TLSv1.2+ with strong AEAD ciphers."
    )
    directives = ["ssl_protocols", "ssl_ciphers", "ssl_prefer_server_ciphers"]
    supports_full_config = True

    def audit(self, directive):
        """Audit individual SSL/TLS directives."""
        if directive.name == "ssl_protocols":
            self._check_protocols(directive)
        elif directive.name == "ssl_ciphers":
            self._check_ciphers(directive)
        elif directive.name == "ssl_prefer_server_ciphers":
            self._check_prefer_server_ciphers(directive)

    def _check_protocols(self, directive):
        """Check for insecure protocols in ssl_protocols directive."""
        protocols = set(directive.args)
        insecure_found = protocols & INSECURE_PROTOCOLS

        if insecure_found:
            # Build fix - remove insecure protocols
            current_protocols = " ".join(directive.args)
            secure_protocols = protocols - INSECURE_PROTOCOLS

            # If no secure protocols remain, suggest TLSv1.2 TLSv1.3
            if not secure_protocols:
                secure_protocols = {"TLSv1.2", "TLSv1.3"}  # noqa: F841

            self.add_issue(
                severity=gixy.severity.HIGH,
                directive=[directive, directive.parent],
                summary="Insecure TLS protocols enabled",
                reason=f"Insecure protocols enabled: {', '.join(sorted(insecure_found))}. "
                "TLSv1.0 and TLSv1.1 are vulnerable to POODLE, BEAST, and other attacks.",
                fixes=[
                    self.make_fix(
                        title="Use only TLSv1.2 and TLSv1.3",
                        search=f"ssl_protocols {current_protocols}",
                        replace="ssl_protocols TLSv1.2 TLSv1.3",
                        description="Remove insecure protocols and use only modern TLS",
                    ),
                ],
            )

    def _check_ciphers(self, directive):
        """Check for weak ciphers in ssl_ciphers directive."""
        cipher_string = directive.args[0] if directive.args else ""

        # Parse cipher string - it's colon-separated
        cipher_parts = cipher_string.replace("+", ":").replace(" ", ":").split(":")
        cipher_parts = [c.strip() for c in cipher_parts if c.strip()]

        weak_found = []
        for cipher in cipher_parts:
            # Skip negation prefixes
            cipher_check = cipher.lstrip("!-")

            # Check against weak cipher list
            if cipher_check.upper() in WEAK_CIPHERS:
                # Only flag if it's not being excluded (! prefix)
                if not cipher.startswith("!"):
                    weak_found.append(cipher)
                continue

            # Check against weak patterns
            for pattern in WEAK_CIPHER_PATTERNS:
                if pattern.upper() in cipher_check.upper():
                    if not cipher.startswith("!"):
                        weak_found.append(cipher)
                    break

        if weak_found:
            # Mozilla Intermediate compatibility cipher suite
            modern_ciphers = (
                "ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:"
                "ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:"
                "ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:"
                "DHE-RSA-AES128-GCM-SHA256:DHE-RSA-AES256-GCM-SHA384"
            )

            self.add_issue(
                severity=gixy.severity.HIGH,
                directive=[directive, directive.parent],
                summary="Weak SSL/TLS ciphers enabled",
                reason=f"Weak ciphers found: {', '.join(weak_found[:5])}{'...' if len(weak_found) > 5 else ''}. "
                "These ciphers are vulnerable to various attacks.",
                fixes=[
                    self.make_fix(
                        title="Use Mozilla Intermediate cipher suite",
                        search=f"ssl_ciphers {cipher_string}",
                        replace=f"ssl_ciphers {modern_ciphers}",
                        description="Use Mozilla's recommended intermediate cipher suite",
                    ),
                ],
            )

    def _check_prefer_server_ciphers(self, directive):
        """Check if ssl_prefer_server_ciphers is properly configured."""
        if directive.args and directive.args[0] == "off":
            self.add_issue(
                severity=gixy.severity.MEDIUM,
                directive=[directive, directive.parent],
                summary="Server cipher preference disabled",
                reason="ssl_prefer_server_ciphers is off, allowing clients to choose ciphers. "
                "This may result in weaker cipher selection if the client prefers insecure options.",
                fixes=[
                    self.make_fix(
                        title="Enable server cipher preference",
                        search="ssl_prefer_server_ciphers off",
                        replace="ssl_prefer_server_ciphers on",
                        description="Let the server choose the strongest cipher",
                    ),
                ],
            )

    def post_audit(self, root):
        """Check for missing SSL configurations in HTTPS servers."""
        # Find http block
        http_block = None
        for child in root.children:
            if child.name == "http":
                http_block = child
                break

        if not http_block:
            return

        # Check each server block that has SSL enabled
        for server_block in http_block.find_all_contexts_of_type("server"):
            # Check if this is an SSL server
            has_ssl = False
            for listen_dir in server_block.find("listen"):
                listen_args = " ".join(listen_dir.args)
                if "ssl" in listen_args or "443" in listen_args:
                    has_ssl = True
                    break

            if not has_ssl:
                continue

            # Check for missing ssl_protocols at server level
            # (only if not set at http level)
            http_protocols = http_block.some("ssl_protocols")
            server_protocols = server_block.some("ssl_protocols")

            if not http_protocols and not server_protocols:
                self.add_issue(
                    severity=gixy.severity.MEDIUM,
                    directive=[server_block],
                    summary="Missing ssl_protocols directive",
                    reason="No ssl_protocols directive found. Default may include insecure protocols.",
                    fixes=[
                        self.make_fix(
                            title="Add ssl_protocols TLSv1.2 TLSv1.3",
                            search="server {",
                            replace="server {\n    ssl_protocols TLSv1.2 TLSv1.3;",
                            description="Explicitly set secure TLS protocols",
                        ),
                    ],
                )

            # Check for missing ssl_ciphers
            http_ciphers = http_block.some("ssl_ciphers")
            server_ciphers = server_block.some("ssl_ciphers")

            if not http_ciphers and not server_ciphers:
                self.add_issue(
                    severity=gixy.severity.MEDIUM,
                    directive=[server_block],
                    summary="Missing ssl_ciphers directive",
                    reason="No ssl_ciphers directive found. Default cipher suite may include weak ciphers.",
                    fixes=[
                        self.make_fix(
                            title="Add modern ssl_ciphers",
                            search="server {",
                            replace=(
                                "server {\n    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:"
                                "ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:"
                                "ECDHE-RSA-AES256-GCM-SHA384;"
                            ),
                            description="Add Mozilla Intermediate cipher suite",
                        ),
                    ],
                )

            # HSTS checks are handled by the dedicated `hsts_header` plugin.
