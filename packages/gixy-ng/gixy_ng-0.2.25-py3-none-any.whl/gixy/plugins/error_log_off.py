"""Module for try_files_is_evil_too plugin."""

import gixy
from gixy.plugins.plugin import Plugin


class error_log_off(Plugin):
    """
    Insecure example:
        location / {
            try_files $uri $uri/ /index.php$is_args$args;
        }
    """

    summary = "The error_log directive does not take the off parameter."
    severity = gixy.severity.MEDIUM
    description = "The error_log directive should not be set to off. It should be set to a valid file path."
    directives = ["error_log"]

    def audit(self, directive):
        if directive.args[0] == "off":
            self.add_issue(
                severity=self.severity,
                directive=[directive],
                reason="The error_log directive should not be set to off.",
                fixes=[
                    self.make_fix(
                        title="Set error_log to file path",
                        search="error_log off",
                        replace="error_log /var/log/nginx/error.log warn",
                        description="Log errors to a file for debugging and security monitoring",
                    ),
                    self.make_fix(
                        title="Discard errors to /dev/null",
                        search="error_log off",
                        replace="error_log /dev/null crit",
                        description="If you really want to discard logs, use /dev/null with crit level",
                    ),
                ],
            )
