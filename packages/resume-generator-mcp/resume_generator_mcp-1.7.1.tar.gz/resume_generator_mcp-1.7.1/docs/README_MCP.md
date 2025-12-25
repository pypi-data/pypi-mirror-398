# Resume Generator - MCP Server Edition

Generate professional PDF resumes through natural language conversations with Claude or other LLM clients using the Model Context Protocol (MCP).

## 🌟 Features

- **Natural Language Interface**: Describe your resume in conversation, get a professional PDF
- **YAML/JSON Support**: Use structured data for precise control
- **Validation**: Check your resume data before generation
- **Templates**: Professional DOCX templates with LibreOffice rendering
- **Schema Documentation**: Built-in help and examples
- **Multi-format**: Support for complex role histories, relocations, and career progressions

## 🚀 Quick Start

### Option 1: Automated Setup (Recommended)

```bash
./setup_mcp.sh
```

This script will:
- Check prerequisites (Python 3.10+, LibreOffice)
- Install dependencies via `uv`
- Configure the MCP server
- Provide Claude Desktop configuration instructions

### Option 2: Manual Setup

1. **Install Dependencies**

```bash
# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install project dependencies
uv sync
```

2. **Install LibreOffice**

```bash
# macOS
brew install --cask libreoffice

# Linux (Ubuntu/Debian)
sudo apt-get install libreoffice

# Verify installation
libreoffice --version
```

3. **Configure Claude Desktop**

Add to your Claude Desktop config (`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):

```json
{
  "mcpServers": {
    "resume-generator": {
      "command": "uv",
      "args": [
        "run",
        "python",
        "/ABSOLUTE/PATH/TO/wrok-docx/mcp_server.py"
      ],
      "env": {}
    }
  }
}
```

**Or use the automatic installer:**

```bash
uv run mcp install mcp_server.py
```

4. **Restart Claude Desktop**

Completely quit and restart Claude Desktop for changes to take effect.

## 📖 Usage

### Through Claude Desktop

Once configured, you can have natural conversations like:

```
You: I need to create a resume. My name is Alex Johnson,
email alex@tech.com, phone +1-555-123-4567...

Claude: I'll help you generate a professional PDF resume.
Let me collect all the necessary information...
[Generates PDF using MCP tools]
```

### Available Tools

The MCP server provides these tools to Claude:

1. **`generate_resume`** - Generate PDF from individual fields
2. **`generate_resume_from_yaml`** - Generate PDF from complete YAML
3. **`validate_resume_yaml`** - Validate YAML structure

### Available Resources

- **`resume://schema`** - Get YAML specification
- **`resume://example`** - Get example resume

## 📝 Resume Data Format

### Minimal Example

```yaml
name: Your Name
email: your.email@example.com
phone: +1 555 123 4567
location: City, State ZIP
linkedin: https://www.linkedin.com/in/yourprofile/

education:
  title: Degree in Field
  college: University Name
  location: City, Country
  period: Graduation Date
  gpa: X.X / 4.0

roles:
  - company: Company Name
    title: Your Title
    locations:
      - location: City, Country
        start_date: Start Date
        end_date: End Date (or "Present")
    achievements:
      - Achievement 1
      - Achievement 2

skills:
  - Skill 1
  - Skill 2
```

See [YAML_SPECIFICATION.md](./YAML_SPECIFICATION.md) for complete documentation.

## 🔧 Development

### Running in Development Mode

Test the MCP server with the inspector:

```bash
uv run mcp dev mcp_server.py
```

### Running the Flask API (Alternative)

The project also includes a REST API:

```bash
# Build Docker image
docker build . -t resume-generator

# Run container
docker run -p 3003:5000 resume-generator

# Generate PDF via API
curl -X POST \
  -F "yaml_file=@resume.yaml" \
  http://localhost:3003/process_resume \
  --output resume.pdf
```

## 📚 Documentation

- **[MCP_SERVER_GUIDE.md](./MCP_SERVER_GUIDE.md)** - Complete MCP server documentation
- **[YAML_SPECIFICATION.md](./YAML_SPECIFICATION.md)** - YAML schema and examples
- **[CLAUDE.md](./CLAUDE.md)** - Technical implementation details

## 🛠️ Troubleshooting

### "LibreOffice not found" Error

Install LibreOffice:
```bash
brew install --cask libreoffice  # macOS
```

### Server Not Appearing in Claude Desktop

1. Verify absolute path in config (no `~` or relative paths)
2. Completely quit and restart Claude Desktop
3. Check Claude Desktop logs:
   - macOS: `~/Library/Logs/Claude/`
   - Look for MCP server errors

### Validation Errors

Use the built-in validation:
```
Ask Claude: "Validate this resume YAML: [paste YAML]"
```

Or check against the schema:
```
Ask Claude: "Show me the resume schema"
```

## 📁 Project Structure

```
wrok-docx/
├── mcp_server.py              # MCP server implementation
├── app.py                     # Flask REST API
├── doc_template_roles.xml     # Resume template (Jinja2)
├── resume/                    # DOCX template structure
├── setup_mcp.sh               # Automated setup script
├── pyproject.toml             # Python dependencies
├── requirements.txt           # Pip requirements
├── MCP_SERVER_GUIDE.md        # MCP documentation
├── YAML_SPECIFICATION.md      # Schema documentation
└── README_MCP.md              # This file
```

## 🎯 Example Use Cases

### 1. Quick Resume Generation

```
You: Create a resume for me. Name: Sarah Chen,
email: sarah@email.com, currently Senior Engineer
at Google in Mountain View...

Claude: [Collects remaining information through conversation]
[Generates PDF]
```

### 2. Update Existing Resume

```
You: I have this resume YAML [paste], but I need to add
a new role at Microsoft starting January 2025.

Claude: [Updates YAML and regenerates PDF]
```

### 3. Validate Before Generating

```
You: Before generating, can you validate this resume data?

Claude: [Uses validate_resume_yaml tool]
[Reports any issues or confirms validity]
```

### 4. Schema Exploration

```
You: What fields do I need for the education section?

Claude: [Reads resume://schema resource]
[Explains education fields]
```

## 🤝 Contributing

This is a personal project, but suggestions are welcome via issues.

## 📄 License

See repository license.

## 🆘 Support

- Check [MCP_SERVER_GUIDE.md](./MCP_SERVER_GUIDE.md) for detailed troubleshooting
- Review Claude Desktop logs for errors
- Test server with `uv run mcp dev mcp_server.py`

## 🎓 Learn More

- [Model Context Protocol Documentation](https://modelcontextprotocol.io/)
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- [Claude Desktop MCP Guide](https://claude.ai/docs)

---

**Version**: 1.0.0
**Last Updated**: 2025-11-02
