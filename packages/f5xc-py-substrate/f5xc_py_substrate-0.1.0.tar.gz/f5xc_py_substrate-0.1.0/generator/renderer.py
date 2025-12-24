"""Jinja2 template renderer for code generation.

Renders ResourceDefinitions into Python source code using Jinja2 templates.
"""

from __future__ import annotations

from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from generator.transformer import ResourceDefinition

# Template directory
TEMPLATES_DIR = Path(__file__).parent / "templates"


class Renderer:
    """Render resource definitions to Python source code."""

    def __init__(self, output_dir: Path) -> None:
        self.output_dir = output_dir
        self.env = Environment(
            loader=FileSystemLoader(TEMPLATES_DIR),
            trim_blocks=True,
            lstrip_blocks=True,
            keep_trailing_newline=True,
        )

    def render_resource(self, resource: ResourceDefinition) -> None:
        """Render a single resource to Python files."""
        resource_dir = self.output_dir / "resources" / resource.name
        resource_dir.mkdir(parents=True, exist_ok=True)

        # Render models.py
        models_content = self._render_template("models.py.j2", resource=resource)
        (resource_dir / "models.py").write_text(models_content)

        # Render resource.py
        resource_content = self._render_template("resource.py.j2", resource=resource)
        (resource_dir / "resource.py").write_text(resource_content)

        # Render __init__.py
        init_content = self._render_template("resource_init.py.j2", resource=resource)
        (resource_dir / "__init__.py").write_text(init_content)

    def render_all(self, resources: list[ResourceDefinition]) -> None:
        """Render all resources."""
        # Render each resource
        for resource in resources:
            self.render_resource(resource)

        # Render resources __init__.py with lazy imports
        resources_init = self._render_template(
            "resources_init.py.j2",
            resources=resources,
        )
        (self.output_dir / "resources" / "__init__.py").write_text(resources_init)

    def _render_template(self, template_name: str, **kwargs) -> str:
        """Render a template with context."""
        template = self.env.get_template(template_name)
        return template.render(**kwargs)
