import gixy
from gixy.plugins.plugin import Plugin


class host_spoofing(Plugin):
    """
    Insecure example:
        proxy_set_header Host $http_host
    """

    summary = "The proxied Host header may be spoofed."
    severity = gixy.severity.MEDIUM
    description = 'In most cases "$host" variable are more appropriate, just use it.'
    directives = ["proxy_set_header"]

    def audit(self, directive):
        name, value = directive.args
        if name.lower() != "host":
            # Not a "Host" header
            return

        if value == "$http_host":
            self.add_issue(
                directive=directive,
                fixes=[
                    self.make_fix(
                        title="Replace $http_host with $host",
                        search="$http_host",
                        replace="$host",
                        description="Use $host which is safer and normalizes the Host header",
                    ),
                ],
            )
        elif value.startswith("$arg_"):
            self.add_issue(
                directive=directive,
                reason=f'Host header set from user-controlled variable "{value}"',
                fixes=[
                    self.make_fix(
                        title="Replace with $host",
                        search=value,
                        replace="$host",
                        description="Use $host instead of user-controlled variable",
                    ),
                ],
            )
