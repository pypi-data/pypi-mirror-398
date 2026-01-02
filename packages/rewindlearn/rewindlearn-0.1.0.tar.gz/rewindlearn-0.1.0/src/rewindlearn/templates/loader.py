"""YAML template loading and validation."""

from pathlib import Path
from typing import Optional

import yaml

from rewindlearn.core.exceptions import TemplateError
from rewindlearn.templates.models import Template


class TemplateLoader:
    """Load and validate YAML templates."""

    def __init__(self, templates_dir: Path):
        self.templates_dir = Path(templates_dir)
        self._cache: dict[str, Template] = {}

    def load(self, template_id: str) -> Template:
        """Load a template by ID or path."""
        # Return cached if available
        if template_id in self._cache:
            return self._cache[template_id]

        # Find template file
        path = self._find_template(template_id)
        if path is None:
            raise TemplateError(f"Template not found: {template_id}")

        # Load and parse
        try:
            with open(path, encoding="utf-8") as f:
                data = yaml.safe_load(f)
            template = Template(**data)
        except yaml.YAMLError as e:
            raise TemplateError(f"Invalid YAML in template {template_id}: {e}")
        except Exception as e:
            raise TemplateError(f"Error loading template {template_id}: {e}")

        # Validate dependencies
        errors = template.validate_dependencies()
        if errors:
            raise TemplateError(f"Template validation failed: {'; '.join(errors)}")

        # Cache and return
        self._cache[template_id] = template
        return template

    def _find_template(self, template_id: str) -> Optional[Path]:
        """Find template file by ID."""
        # Direct path
        if Path(template_id).exists():
            return Path(template_id)

        # In templates directory
        direct = self.templates_dir / f"{template_id}.yaml"
        if direct.exists():
            return direct

        # With version suffix
        matches = list(self.templates_dir.glob(f"{template_id}*.yaml"))
        if matches:
            # Return most recent version (alphabetically last)
            return sorted(matches)[-1]

        return None

    def validate(self, path: Path) -> tuple[bool, list[str]]:
        """Validate a template file without caching."""
        errors: list[str] = []

        try:
            with open(path, encoding="utf-8") as f:
                data = yaml.safe_load(f)
            template = Template(**data)
            errors.extend(template.validate_dependencies())
        except Exception as e:
            errors.append(str(e))

        return len(errors) == 0, errors

    def list_templates(self) -> list[str]:
        """List available template IDs."""
        templates = []
        if self.templates_dir.exists():
            for f in self.templates_dir.glob("*.yaml"):
                templates.append(f.stem)
        return sorted(templates)
