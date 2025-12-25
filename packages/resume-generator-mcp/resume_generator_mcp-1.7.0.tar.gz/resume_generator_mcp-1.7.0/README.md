# Resume Generator MCP Server

A [Model Context Protocol (MCP)](https://modelcontextprotocol.io) server for generating professional PDF resumes from YAML/JSON data. Works seamlessly with **Claude Desktop**, **ChatGPT Desktop**, and other MCP-compatible AI assistants.

## Features

- Generate professional PDF resumes through natural language conversations
- No local LibreOffice installation required - all processing happens on a remote service
- Support for YAML and JSON input formats
- Built-in validation and helpful error messages
- Pre-configured professional resume template
- Works with Claude Desktop, ChatGPT Desktop, Cline, and other MCP clients

## Installation

### Prerequisites

- Python 3.10 or higher
- Internet connection (to reach the remote PDF generation service)

### Install via pip

```bash
pip install resume-generator-mcp
```

**If you get an "externally-managed-environment" error:**
```bash
pip install --break-system-packages resume-generator-mcp
```

**Or use pipx (recommended for system Python):**
```bash
pipx install resume-generator-mcp
```

## Configuration

### For Claude Desktop

Add the following to your Claude Desktop configuration file:

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`

**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "resume-generator": {
      "command": "python",
      "args": ["-m", "resume_generator_mcp"]
    }
  }
}
```

### For ChatGPT Desktop

Add to your ChatGPT Desktop configuration file:

**macOS**: `~/Library/Application Support/ChatGPT/mcp_config.json`

**Windows**: `%APPDATA%\ChatGPT\mcp_config.json`

```json
{
  "mcpServers": {
    "resume-generator": {
      "command": "python",
      "args": ["-m", "resume_generator_mcp"]
    }
  }
}
```

### For Cline (VS Code Extension)

Add to your Cline MCP settings:

```json
{
  "mcpServers": {
    "resume-generator": {
      "command": "python",
      "args": ["-m", "resume_generator_mcp"]
    }
  }
}
```

### Environment Variables (Optional)

You can customize the API endpoint by setting an environment variable:

```json
{
  "mcpServers": {
    "resume-generator": {
      "command": "python",
      "args": ["-m", "resume_generator_mcp"],
      "env": {
        "RESUME_API_URL": "https://wrok-docx.fly.dev"
      }
    }
  }
}
```

## Usage

Once configured, you can interact with the resume generator through natural language in Claude Desktop:

### Example Conversations

**Generate a resume from scratch:**
```
Create a resume for Alex Johnson, a Senior Software Engineer at TechCorp in Seattle.
Email: alex@example.com, Phone: +1-555-0100.
Education: MS Computer Science from Stanford, 2015, GPA 3.9.
Current role since Jan 2022, led cloud migration project and reduced costs by 40%.
```

**Generate from YAML:**
```
Generate a resume using this YAML:
name: Alex Johnson
email: alex@example.com
phone: +1 555 123 4567
location: Seattle, WA
linkedin: https://www.linkedin.com/in/alexjohnson/
education:
  title: Master of Science in Computer Science
  college: Stanford University
  location: Stanford, CA
  period: June 2015
  gpa: 3.9 / 4.0
roles:
  - company: TechCorp
    title: Senior Software Engineer
    locations:
      - location: Seattle, USA
        start_date: Jan 2022
        end_date: Present
    achievements:
      - Led cloud migration reducing costs by 40%
      - Mentored 5 junior developers
```

**Validate resume data:**
```
Validate this resume YAML before generating the PDF
```

**Check service status:**
```
Is the resume generation service running?
```

## Available Tools

The MCP server provides the following tools:

### `generate_resume`
Generate a PDF resume from individual parameters (name, email, education, roles, etc.)

### `generate_resume_from_yaml`
Generate a PDF resume from complete YAML content

### `validate_resume_yaml`
Validate YAML resume content without generating a PDF

### `check_service_status`
Check if the remote resume generation service is accessible

## Available Resources

### `resume://schema`
Get the complete YAML schema specification for resumes

### `resume://example`
Get an example resume YAML for reference

## Resume Data Format

### Required Fields

```yaml
name: string           # Full name
email: string          # Email address
phone: string          # Phone with country code (e.g., +1 555 123 4567)
location: string       # Current location
linkedin: string       # LinkedIn profile URL

education:
  title: string        # Degree and field
  college: string      # Institution name
  location: string     # Institution location
  period: string       # Graduation date
  gpa: string         # Grade point average

roles:                 # Array of work experience
  - company: string    # Company name
    title: string      # Job title
    locations:         # Array of locations for this role
      - location: string      # Work location
        start_date: string    # Start date
        end_date: string      # End date or "Present"
    achievements:      # Array of bullet points
      - string
```

### Optional Fields

```yaml
skills:                # Array of skills/technologies
  - string
```

## Troubleshooting

### Service Connection Issues

If you see connection errors, check:

1. **Internet connection**: The MCP server needs internet access to reach the PDF generation service
2. **Service status**: Use the `check_service_status` tool to verify the service is running
3. **Firewall**: Ensure your firewall allows outbound HTTPS connections

### Installation Issues

If installation fails:

```bash
# Upgrade pip
pip install --upgrade pip

# Install with verbose output
pip install -v resume-generator-mcp

# Or install from source
git clone https://github.com/yourusername/resume-generator-mcp
cd resume-generator-mcp
pip install -e .
```

### Claude Desktop Not Recognizing the Server

1. Verify the configuration file path and JSON syntax
2. Restart Claude Desktop after adding the configuration
3. Check Claude Desktop logs for errors

## Development

### Running from Source

```bash
# Clone the repository
git clone https://github.com/yourusername/resume-generator-mcp
cd resume-generator-mcp

# Install in development mode
pip install -e .

# Run the server
python -m resume_generator_mcp
```

### Testing

```bash
# Install test dependencies
pip install pytest

# Run tests
pytest
```

## Architecture

The system consists of two components:

1. **MCP Server** (this package): Runs locally on your machine, communicates with Claude Desktop via STDIO
2. **PDF Generation API**: Hosted service that performs template rendering and PDF conversion using LibreOffice

```
Claude Desktop → MCP Server (local) → HTTPS → PDF API (remote) → PDF file
```

This architecture means:
- Users don't need to install LibreOffice
- No template files needed locally
- Fast and consistent PDF generation
- Works on all platforms (macOS, Windows, Linux)

## Privacy & Security

- Resume data is sent to the remote API via HTTPS
- PDFs are generated on-demand and not stored on the server
- No data is logged or retained after generation
- The service is stateless and ephemeral

## License

MIT License - see LICENSE file for details

## Support

- GitHub Issues: https://github.com/yourusername/resume-generator-mcp/issues
- Documentation: https://github.com/yourusername/resume-generator-mcp

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Changelog

### 1.0.0 (2025-11-05)
- Initial release
- Support for YAML/JSON resume input
- Remote PDF generation via Fly.io service
- Integration with Claude Desktop
- Built-in validation and error handling

---

## Project Structure

```
.
├── app.py                      # Main Flask application
├── Dockerfile                  # Docker container definition
├── pyproject.toml             # Python package configuration
├── requirements.txt           # Python dependencies
├── fly.toml                   # Fly.io deployment config
├── docs/                      # Documentation files
│   ├── QUICKSTART.md
│   ├── DEPLOYMENT_GUIDE.md
│   └── ...
├── examples/                  # Example YAML files and generated PDFs
│   ├── document.yaml
│   ├── sravan_resume.yaml
│   └── *.pdf
├── scripts/                   # Utility scripts
│   ├── setup_mcp.sh
│   ├── process_template.py
│   ├── explode_docx.py
│   └── implode_docx.py
├── templates/                 # DOCX templates and schemas
│   ├── doc_template_roles.xml
│   ├── resume/               # Exploded DOCX structure
│   ├── resume_schema.json
│   └── openapi.yaml
└── resume_generator_mcp/      # MCP server package
    ├── __init__.py
    └── __main__.py
```

## Docker Development (for contributors)

If you're contributing to the backend service:

```bash
# Build the Docker image
docker build . -t docx

# Run the service locally
docker run -p 3002:5000 docx

# Test the service
curl http://localhost:3002/test
curl -X POST -F "yaml_file=@examples/document.yaml" http://localhost:3002/process_resume --output resume.pdf
```
