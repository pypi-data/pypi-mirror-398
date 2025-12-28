"""Utilidades para plantillas de email basadas en string.Template."""
from string import Template
from typing import Set


def extract_template_variables(template: Template) -> Set[str]:
    """Extrae los nombres de variables usados en una plantilla string.Template."""
    variables = set()

    for match in template.pattern.finditer(template.template):
        name = match.group("named") or match.group("braced")
        if name:
            variables.add(name)

    return variables
