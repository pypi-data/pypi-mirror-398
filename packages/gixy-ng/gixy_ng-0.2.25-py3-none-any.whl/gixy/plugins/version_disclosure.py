import gixy
from gixy.plugins.plugin import Plugin


class version_disclosure(Plugin):
    """
    Syntax for the directive: server_tokens off;
    """

    summary = "Do not enable server_tokens on or server_tokens build"
    severity = gixy.severity.HIGH
    description = (
        "Using server_tokens on; or server_tokens build;  allows an "
        "attacker to learn the version of NGINX you are running, which can "
        "be used to exploit known vulnerabilities."
    )
    directives = ["server_tokens"]
    supports_full_config = True

    def audit(self, directive):
        if directive.args[0] in ["on", "build"]:
            self.add_issue(
                severity=gixy.severity.HIGH,
                directive=[directive, directive.parent],
                reason="Using server_tokens value which promotes information disclosure",
                fixes=[
                    self.make_fix(
                        title="Set server_tokens off",
                        search=f"server_tokens {directive.args[0]}",
                        replace="server_tokens off",
                        description="Disable version disclosure in Server header",
                    ),
                ],
            )

    def post_audit(self, root):
        """Check for missing server_tokens directive in full config mode.

        Only reports 'missing' if there's NO server_tokens directive anywhere
        in the config. If server_tokens exists (even with 'on' value), the
        audit() method already handles it.
        """
        # Find http block
        http_block = None
        for child in root.children:
            if child.name == "http":
                http_block = child
                break

        if not http_block:
            return

        # Check if server_tokens is set at http level
        http_server_tokens = http_block.some("server_tokens")

        # If server_tokens is set at http level (any value), the audit() method
        # handles bad values. Don't report "missing" at server level.
        if http_server_tokens:
            if http_server_tokens.args[0] == "off":
                # Properly configured at http level, nothing more to check
                return
            # Bad value at http level - audit() handles this, don't double-report
            # at server level
            return

        # No server_tokens at http level - check each server block
        for server_block in http_block.find_all_contexts_of_type("server"):
            server_tokens = server_block.some("server_tokens")

            if not server_tokens:
                # Truly missing - no directive at http or server level
                self.add_issue(
                    severity=gixy.severity.HIGH,
                    directive=[server_block],
                    reason="Missing server_tokens directive - defaults to 'on' which promotes information disclosure",
                    fixes=[
                        self.make_fix(
                            title="Add server_tokens off",
                            search="server {",
                            replace="server {\n    server_tokens off;",
                            description="Add server_tokens off to disable version disclosure",
                        ),
                    ],
                )
            # If server_tokens exists at server level, audit() handles bad values
