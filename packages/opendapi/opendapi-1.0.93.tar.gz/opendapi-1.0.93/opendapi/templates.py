"""Entrypoint for the OpenDAPI CLI `opendapi init` command."""

import os

from jinja2 import Template

DATASTORES_TEMPLATE_PATH = os.path.join(
    os.path.dirname(__file__), "templates", "datastores.yaml.jinja"
)
GITHUB_ACTIONS_TEMPLATE_PATH = os.path.join(
    os.path.dirname(__file__), "templates", "github_actions.yaml.jinja"
)
OPENDAPI_CONFIG_TEMPLATE_PATH = os.path.join(
    os.path.dirname(__file__), "templates", "opendapi.config.yaml.jinja"
)
TEAMS_TEMPLATE_PATH = os.path.join(
    os.path.dirname(__file__), "templates", "teams.yaml.jinja"
)
SUBJECTS_TEMPLATE_PATH = os.path.join(
    os.path.dirname(__file__), "templates", "subjects.yaml.jinja"
)
CATEGORIES_TEMPLATE_PATH = os.path.join(
    os.path.dirname(__file__), "templates", "categories.yaml.jinja"
)
PURPOSES_TEMPLATE_PATH = os.path.join(
    os.path.dirname(__file__), "templates", "purposes.yaml.jinja"
)


def _read_template_file(template_path: str) -> str:
    """Read the contents of the template file."""
    with open(template_path, "r", encoding="utf-8") as file:
        return file.read()


def render_template_buffer(template_path: str, template_input: dict) -> str:
    """Render the template and return the contents"""

    template_content = _read_template_file(template_path)
    template = Template(template_content, autoescape=True)
    return template.render(**template_input)


def render_template_file(
    output_filepath: str, template_path: str, template_input: dict
):
    """Render the template and write it to the output file."""

    if not os.path.exists(os.path.dirname(output_filepath)):
        os.makedirs(os.path.dirname(output_filepath), exist_ok=True)
    with open(output_filepath, "w", encoding="utf-8") as file:
        file.write(render_template_buffer(template_path, template_input))
