"""
Plugin to detect unsafe HTTP/2 fallback handling in a TLS default_server.

Some NGINX deployments use a `default_server` with `ssl_reject_handshake on;`
to prevent serving arbitrary domains when SNI is missing or unknown.

In certain HTTP/2 edge-cases, requests may still be processed by a default
server context, so it's common to add a defensive:

    location / { return 421; }

This plugin warns when:
- `ssl_reject_handshake on;` is present
- the server is a `default_server`
- HTTP/2 is enabled
- and there is no `location /` (or `location = /`) returning 421
"""

import gixy
from gixy.plugins.plugin import Plugin


class http2_misdirected_request(Plugin):
    summary = "Missing HTTP/2 misdirected-request safeguard (return 421)"
    severity = gixy.severity.LOW
    description = (
        "With HTTP/2 enabled, some requests may still reach a TLS default_server "
        "even when `ssl_reject_handshake` is used. Returning 421 (Misdirected Request) "
        "in `location /` provides a deterministic, safe response."
    )
    directives = []
    supports_full_config = True

    def audit(self, directive):
        return

    def post_audit(self, root):
        http_block = None
        for child in root.children:
            if child.name == "http":
                http_block = child
                break

        if not http_block:
            return

        for server_block in http_block.find_all_contexts_of_type("server"):
            if not self._server_rejects_handshake(server_block):
                continue
            if not self._server_is_default(server_block):
                continue
            if not self._server_has_http2(server_block):
                continue
            if self._has_location_returning_421(server_block):
                continue

            self.add_issue(
                severity=self.severity,
                directive=[server_block],
                summary=self.summary,
                reason=(
                    "Server is `default_server` with `ssl_reject_handshake on` and HTTP/2 enabled, "
                    "but it does not define `location / { return 421; }`. "
                    "Adding a 421 safeguard helps handle misdirected HTTP/2 requests safely."
                ),
                fixes=[
                    self.make_fix(
                        title="Add location / returning 421",
                        search="server {",
                        replace="server {\n    location / {\n        return 421;\n    }",
                        description="Return 421 (Misdirected Request) for unexpected HTTP/2 requests",
                    ),
                ],
            )

    def _server_rejects_handshake(self, server_block):
        ssl_reject = server_block.some("ssl_reject_handshake")
        return bool(ssl_reject and ssl_reject.args and ssl_reject.args[0] == "on")

    def _server_is_default(self, server_block):
        for listen_dir in server_block.find("listen"):
            for token in listen_dir.args:
                lower = token.lower()
                if lower in ("default_server", "default"):
                    return True
        return False

    def _server_has_http2(self, server_block):
        # http2 on;
        http2 = server_block.some("http2")
        if http2 and http2.args and http2.args[0] == "on":
            return True

        # listen ... http2;
        for listen_dir in server_block.find("listen"):
            for token in listen_dir.args:
                if token.lower() == "http2":
                    return True
        return False

    def _has_location_returning_421(self, server_block):
        for location in server_block.find_all_contexts_of_type("location"):
            if location.path != "/":
                continue

            for ret in location.find("return"):
                if ret.args and ret.args[0] == "421":
                    return True

        return False
