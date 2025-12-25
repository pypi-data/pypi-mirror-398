from jinja2 import (
    Environment,
    PackageLoader,
    Template,
    TemplateError,
    TemplateNotFound,
    TemplateRuntimeError,
    select_autoescape,
)


def get_local_template(template: str) -> Template:
    template_name = template
    try:
        env = Environment(
            loader=PackageLoader("sw_ut_report", "templates"),
            autoescape=select_autoescape(),
            trim_blocks=True,  # Removes unnecessary spaces before and after blocks and loop
            lstrip_blocks=True,  # Removes unnecessary spaces before blocks and loop
        )
        return env.get_template(template_name)
    except TemplateNotFound as e:
        raise TemplateError(f"Template not found: {template_name}") from e
    except TemplateRuntimeError as e:
        raise TemplateError(f"Template runtime error: {template_name}") from e
    except Exception as e:
        raise TemplateError(f"Template error: {template_name}") from e
