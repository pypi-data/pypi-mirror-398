import os

from jinja2 import Environment, FileSystemLoader, TemplateError


def render_template_file(template_file_path: str, **kwargs):
    """
    Renders a given template file.

    Args:
        template_file_path (str): template file path
        kwargs: variables passed to the template

    Returns:
        str
    """
    env = Environment(loader=FileSystemLoader(os.path.dirname(template_file_path)))
    template = env.get_template(os.path.basename(template_file_path))
    return template.render(**kwargs)


def render_template_string(template_string: str, **kwargs):
    """
    Renders a given template string.

    Args:
        template_string (str): template string
        kwargs: variables passed to the template

    Returns:
        str
    """
    env = Environment()
    template = env.from_string(template_string)
    return template.render(**kwargs)


def render_jinja_with_error_handling(template_string: str, **kwargs):
    """
    Renders a given template string with error handling.

    Args:
        template_string (str): template string
        kwargs: variables passed to the template

    Returns:
        str
    """
    try:
        return render_template_string(template_string, **kwargs)
    except TemplateError as e:
        return (
            f"Error rendering template: {str(e)}\nTemplate content:\n{template_string}\nTemplate variables:\n{kwargs}"
        )
