import gixy
from gixy.plugins.plugin import Plugin


class allow_without_deny(Plugin):
    """
    Bad example: add_header Content-Type text/plain;
    Good example: default_type text/plain;
    """

    summary = "Found allow directive(s) without deny in the same context."
    severity = gixy.severity.HIGH
    description = 'The "allow" directives should be typically accompanied by "deny all;" directive.'
    directives = ["allow"]

    def audit(self, directive):
        parent = directive.parent
        if not parent:
            return
        if directive.args == ["all"]:
            # for example, "allow all" in a nested location which allows access to otherwise forbidden parent location
            return
        # Includes are not a true context boundary. If the allow comes from an
        # included file, climb to the real parent context (e.g., location/server).
        while parent and getattr(parent, "name", None) == "include":
            parent = parent.parent
            if not parent:
                return

        deny_found = False
        for child in parent.children:
            if child.name == "deny":
                deny_found = True
        if not deny_found:
            reason = 'You probably want "deny all;" after all the "allow" directives'
            # Find the last allow directive to suggest where to add deny
            last_allow_line = str(directive)
            self.add_issue(
                directive=directive,
                reason=reason,
                fixes=[
                    self.make_fix(
                        title='Add "deny all;" after allow directives',
                        search=last_allow_line,
                        replace=last_allow_line + "\n    deny all;",
                        description="Add deny all to complete the access control list",
                    ),
                ],
            )
