# Rewind.Learn

Transform session artifacts into structured knowledge.

[![PyPI version](https://badge.fury.io/py/rewindlearn.svg)](https://badge.fury.io/py/rewindlearn)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

## Installation

```bash
pip install rewindlearn
```

## Quick Start

```bash
# Set your API key
export ANTHROPIC_API_KEY="your-key"

# Process a session
rewindlearn process run \
    --template online-course \
    --transcript lecture.vtt \
    --chat chat.txt \
    --course "AI Engineering" \
    --session 5 \
    --output study-guides/
```

## Python API

```python
import asyncio
from rewindlearn import process_session

async def main():
    results = await process_session(
        template="online-course",
        transcript_path="lecture.vtt",
        chat_path="chat.txt",
        course_name="AI Engineering",
        session_number=5
    )
    print(results["session_summary"])

asyncio.run(main())
```

## Features

- **Session Summary**: Comprehensive overview of the session content
- **Concept Timeline**: Chronological breakdown of concepts with timestamps
- **Friction Analysis**: Identifies potential confusion points and questions
- **Coverage Gaps**: Topics that could use more coverage
- **Learning Resources**: Curated resources for each topic
- **Action Items**: Prioritized tasks for students
- **Concept Chunks**: CSV with video clip markers for splitting

## CLI Commands

```bash
# Show help
rewindlearn --help

# Show version
rewindlearn --version

# Process a session
rewindlearn process run --template online-course --transcript lecture.vtt --output ./output

# List available templates
rewindlearn template list

# Show template details
rewindlearn template show online-course

# Validate a template
rewindlearn template validate custom-template.yaml

# Show current configuration
rewindlearn config show

# Check configuration validity
rewindlearn config check
```

## Configuration

Create a `.env` file or set environment variables:

```bash
# Required: At least one LLM API key
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...

# Optional: LangSmith for observability
LANGSMITH_API_KEY=lsv2_...
LANGSMITH_TRACING=true

# Optional: Override defaults
REWINDLEARN_DEFAULT_PROVIDER=anthropic
REWINDLEARN_DEFAULT_MODEL=claude-sonnet-4-20250514
REWINDLEARN_TEMPLATES_DIR=./templates
REWINDLEARN_OUTPUT_DIR=./output
```

## Development

```bash
# Clone the repository
git clone https://github.com/knightsri/rewind.learn.git
cd rewind.learn

# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest -v

# Type checking
mypy src/

# Linting
ruff check src/
```

## License

Apache 2.0
