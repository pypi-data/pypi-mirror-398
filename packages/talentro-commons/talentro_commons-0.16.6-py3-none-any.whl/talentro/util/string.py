import string

def render_template_path(template: str, values: dict) -> str:
    formatter = string.Formatter()

    required_fields = [field for _, field, _, _ in formatter.parse(template) if field]

    missing = [field for field in required_fields if field not in values]

    if missing:
        raise ValueError(f"Variables not set: {', '.join(missing)}")

    return template.format(**values)