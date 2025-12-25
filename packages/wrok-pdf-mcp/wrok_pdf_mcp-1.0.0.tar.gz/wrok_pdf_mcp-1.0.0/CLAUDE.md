# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A Flask-based web service that generates PDF resumes from YAML/JSON data using DOCX templates. The service leverages Jinja2 templating to populate Word documents and converts them to PDF using LibreOffice's unoconv.

## Core Architecture

### Document Processing Pipeline

The system follows a four-step pipeline implemented in `app.py:process_resume()`:

1. **Input Processing**: Accept YAML or JSON resume data via Flask endpoint
2. **Template Rendering**: Use Jinja2 to populate `doc_template_roles.xml` with resume data
3. **DOCX Assembly**: Package the rendered XML with the `resume/` template structure into a valid DOCX file
4. **PDF Conversion**: Convert DOCX to PDF using LibreOffice's `unoconv` command-line tool

### Key Components

- **app.py**: Flask application with `/process_resume` endpoint (accepts `yaml_file` or `json_file` multipart form data)
- **templates/doc_template_roles.xml**: Jinja2 template for Word document XML (Office Open XML format)
- **templates/resume/**: Exploded DOCX directory structure serving as the base template (contains word/, _rels/, docProps/, etc.)
- **scripts/**: Utility scripts for manual DOCX manipulation (explode/implode/convert)

### Data Flow

```
YAML/JSON input → Jinja2 template rendering → Replace templates/resume/word/document.xml
→ Zip into DOCX → unoconv PDF conversion → Return PDF
```

Each request operates in an isolated temporary directory (`/tmp/resume_{uuid}_*`) to support concurrent processing.

## Development Commands

### Local Development (Docker)

```bash
# Build the Docker image
docker build . -t docx

# Run the service (port 3002 → container port 5000)
docker run -p 3002:5000 docx
```

The Flask app runs on port 5000 internally, exposed via Docker on port 3002.

### Testing the Service

```bash
# Health check endpoint
curl http://localhost:3002/test

# Process a resume (YAML)
curl -X POST -F "yaml_file=@examples/document.yaml" http://localhost:3002/process_resume --output resume.pdf

# Process a resume (JSON)
curl -X POST -F "json_file=@examples/resume.json" http://localhost:3002/process_resume --output resume.pdf
```

### Standalone Utilities

These scripts are for manual development/debugging (located in `scripts/`):

```bash
# Render template with YAML data (updates templates/resume/word/document.xml in-place)
python scripts/process_template.py examples/document.yaml

# Explode a DOCX into directory structure
python scripts/explode_docx.py

# Implode directory back to DOCX
python scripts/implode_docx.py

# Convert DOCX to PDF (requires docx2pdf library, macOS/Windows only)
python scripts/docx_pdf.py resume.docx
```

**Note**: The standalone `docx_pdf.py` uses the `docx2pdf` library (platform-dependent), while the Flask service uses `unoconv` for cross-platform Docker compatibility.

## Template Structure

### Resume Data Format

Input YAML/JSON must include:
- `name`, `email`, `phone`, `location`, `linkedin`
- `education` object with `title`, `college`, `location`, `period`, `gpa`
- `experiences` array with:
  - `company`, `location`
  - `roles` array with `title`, `start_date`, `end_date`
  - `achievements` array (bullet points)

See `examples/document.yaml` or `examples/document-roles.yaml` for reference schema.

### Modifying the Template

1. Edit an existing DOCX in Word/LibreOffice
2. Run `scripts/explode_docx.py` to extract to `templates/resume/` directory
3. Edit `templates/resume/word/document.xml` and convert to Jinja2 template syntax
4. Save as `templates/doc_template_roles.xml`
5. Update `app.py` template reference if needed (line ~56-62)

The `templates/doc_template_roles.xml` contains Office Open XML with Jinja2 variables embedded in `<w:t>` (text) elements.

## Deployment

Configured for Fly.io deployment via `fly.toml`:
- App: `wrok-docx`
- Region: `sjc` (San Jose)
- Memory: 1GB
- Internal port: 5000

Deploy with: `fly deploy`

## Dependencies

Critical runtime dependencies:
- **Python**: PyYAML, Jinja2, Flask
- **System**: LibreOffice, unoconv, python3-uno (installed in Docker)

All Python dependencies in `requirements.txt`. Docker base image: `python:3.9-slim` with LibreOffice installed.

## Important Notes

- Temporary directories are **not** automatically cleaned up (see `app.py:~150`) - consider implementing cleanup for production
- The service uses `unoconv` which requires LibreOffice headless mode - ensure it's available in the container
- DOCX files are just ZIP archives of XML - the `templates/resume/` directory structure must maintain exact Office Open XML format
- File paths in zip archives must use forward slashes (`/`) regardless of OS (see `app.py:~82`)

## Project Structure

```
.
├── app.py                      # Main Flask application
├── Dockerfile                  # Docker container definition
├── pyproject.toml             # Python package configuration
├── requirements.txt           # Python dependencies
├── fly.toml                   # Fly.io deployment config
├── CLAUDE.md                  # Project documentation for Claude Code
├── docs/                      # Documentation files
│   ├── QUICKSTART.md
│   ├── DEPLOYMENT_GUIDE.md
│   ├── MCP_SERVER_GUIDE.md
│   └── ...
├── examples/                  # Example YAML files and generated PDFs
│   ├── document.yaml
│   ├── document-roles.yaml
│   ├── sravan_resume.yaml
│   └── *.pdf (test outputs)
├── scripts/                   # Utility scripts
│   ├── setup_mcp.sh
│   ├── process_template.py    # Render template with YAML
│   ├── explode_docx.py        # Extract DOCX to directory
│   ├── implode_docx.py        # Package directory to DOCX
│   └── docx_pdf.py           # Convert DOCX to PDF
├── templates/                 # DOCX templates and schemas
│   ├── doc_template_roles.xml # Jinja2 template (Office Open XML)
│   ├── resume/               # Exploded DOCX structure
│   │   ├── word/
│   │   │   └── document.xml
│   │   ├── _rels/
│   │   └── [Content_Types].xml
│   ├── resume_schema.json
│   └── openapi.yaml
└── resume_generator_mcp/      # MCP server package
    ├── __init__.py
    └── __main__.py
```
