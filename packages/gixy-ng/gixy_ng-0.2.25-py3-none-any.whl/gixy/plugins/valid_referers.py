import gixy
from gixy.plugins.plugin import Plugin


class valid_referers(Plugin):
    """
    Insecure example:
        valid_referers none server_names *.webvisor.com;
    """

    summary = 'Used "none" as valid referer.'
    severity = gixy.severity.HIGH
    description = "Never trust undefined referer."
    directives = ["valid_referers"]

    def audit(self, directive):
        if "none" in directive.args:
            # Build the fixed args list without 'none'
            fixed_args = [arg for arg in directive.args if arg != "none"]
            fixed_directive = "valid_referers " + " ".join(fixed_args) + ";"
            original_directive = "valid_referers " + " ".join(directive.args) + ";"

            self.add_issue(
                directive=directive,
                fixes=[
                    self.make_fix(
                        title='Remove "none" from valid_referers',
                        search=original_directive,
                        replace=fixed_directive,
                        description="Remove 'none' to prevent empty referer bypass",
                    ),
                ],
            )
