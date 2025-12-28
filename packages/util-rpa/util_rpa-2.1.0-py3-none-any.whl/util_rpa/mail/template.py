"""Email template rendering utilities."""
from string import Template


class EmailTemplate:
    """Email template renderer using string.Template."""

    def __init__(self, subject: str, body: str):
        self.subject_tpl = Template(subject)
        self.body_tpl = Template(body)

    def render(self, **context):
        """Render the template with the given context."""
        return (
            self.subject_tpl.safe_substitute(**context),
            self.body_tpl.safe_substitute(**context)
        )
