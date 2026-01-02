"""Output file generation."""

from datetime import datetime
from pathlib import Path
from typing import Any

from rewindlearn.templates.models import Template
from rewindlearn.workflow.state import SessionState


class OutputBuilder:
    """Generate output files from workflow results."""

    def __init__(self, template: Template, output_dir: Path):
        self.template = template
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate(
        self,
        state: SessionState,
        course_name: str,
        session_number: int
    ) -> list[Path]:
        """Generate all output files from workflow state."""
        outputs: list[Path] = []

        for deliverable in self.template.outputs.deliverables:
            content = state.get(deliverable)
            if not content:
                continue

            # Determine format
            if deliverable == "concept_chunks":
                ext = "csv"
            else:
                ext = "md"

            # Generate filename
            filename = self._make_filename(
                deliverable, ext, course_name, session_number
            )
            path = self.output_dir / filename

            # Write file
            if ext == "csv":
                path.write_text(content, encoding="utf-8")
            else:
                # Add frontmatter to markdown
                full_content = self._add_frontmatter(
                    content, deliverable, course_name, session_number
                )
                path.write_text(full_content, encoding="utf-8")

            outputs.append(path)

        return outputs

    def _make_filename(
        self,
        deliverable: str,
        ext: str,
        course_name: str,
        session_number: int
    ) -> str:
        """Generate output filename."""
        # Clean course name for filename
        safe_name = course_name.replace(" ", "-").lower()
        safe_name = "".join(c for c in safe_name if c.isalnum() or c == "-")

        return f"{safe_name}-S{session_number:02d}-{deliverable}.{ext}"

    def _add_frontmatter(
        self,
        content: str,
        deliverable: str,
        course_name: str,
        session_number: int
    ) -> str:
        """Add YAML frontmatter to markdown content."""
        frontmatter = f"""---
course: "{course_name}"
session: {session_number}
deliverable: {deliverable}
template: {self.template.template_id}
generated: {datetime.now().isoformat()}
---

"""
        return frontmatter + content
