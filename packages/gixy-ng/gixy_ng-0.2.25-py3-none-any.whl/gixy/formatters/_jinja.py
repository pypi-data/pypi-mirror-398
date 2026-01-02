from jinja2 import Environment, PackageLoader

from gixy.utils.text import to_text


def load_template(name):
    # autoescape=False is safe here - these templates output plain text to terminal,
    # not HTML. Auto-escaping would incorrectly escape characters like < > &
    # nosemgrep: python.jinja2.security.audit.autoescape-disabled-false
    env = Environment(  # NOSONAR # nosec B701 - plain text CLI, not HTML
        loader=PackageLoader("gixy", "formatters/templates"),
        trim_blocks=True,
        lstrip_blocks=True,
        autoescape=False,
    )
    env.filters["to_text"] = to_text_filter
    return env.get_template(name)


def to_text_filter(text):
    try:
        return text.encode("latin1").decode("utf-8")
    except UnicodeEncodeError:
        return to_text(text)
