# Test Package Locally Before Publishing

Quick guide to test your MCP server package before publishing to PyPI.

## Option 1: Install from Local Wheel (Recommended)

```bash
# Create a fresh virtual environment
python3 -m venv test_env
source test_env/bin/activate

# Install from the built wheel
pip install dist/resume_generator_mcp-1.0.0-py3-none-any.whl

# Verify installation
pip show resume-generator-mcp
```

## Option 2: Install in Editable Mode

```bash
# Create virtual environment
python3 -m venv test_env
source test_env/bin/activate

# Install in editable mode (for development)
pip install -e .

# Make changes to code and they'll be reflected immediately
```

## Test the Package

### 1. Check Module Import
```bash
python -c "from resume_generator_mcp import main; print('✓ Package imports successfully')"
```

### 2. Test as Module
```bash
# This should connect to your Fly.io service
# (You'll see MCP server startup messages)
python -m resume_generator_mcp
```

Press Ctrl+C to stop the server.

### 3. Configure in Claude Desktop

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "resume-generator-test": {
      "command": "/path/to/test_env/bin/python",
      "args": ["-m", "resume_generator_mcp"]
    }
  }
}
```

Replace `/path/to/test_env` with actual path. Get it with:
```bash
echo "$(pwd)/test_env"
```

### 4. Test in Claude Desktop

1. Restart Claude Desktop
2. Start a new conversation
3. Type: "Is the resume generation service running?"
4. Claude should use the `check_service_status` tool

If it works, try:
> "Generate a test resume for John Smith, software engineer"

## Verify API Connection

Test that the MCP server can reach your Fly.io service:

```bash
source test_env/bin/activate
python << 'EOF'
import requests
url = "https://wrok-docx.fly.dev/test"
response = requests.get(url, timeout=10)
print(f"Status: {response.status_code}")
print(f"Response: {response.text}")
EOF
```

Expected output:
```
Status: 200
Response: Hello from Flask!
```

## Test Package Structure

Verify the wheel contains correct files:

```bash
# Extract and inspect the wheel
unzip -l dist/resume_generator_mcp-1.0.0-py3-none-any.whl
```

Should contain:
- `resume_generator_mcp/__init__.py`
- `resume_generator_mcp/__main__.py`
- `resume_generator_mcp/server.py`
- Metadata files

## Common Issues

### Import Error
```
ModuleNotFoundError: No module named 'resume_generator_mcp'
```

**Fix**: Make sure you're in the virtual environment where you installed it:
```bash
source test_env/bin/activate
which python  # Should show test_env path
```

### Connection Error
```
Cannot connect to API at https://wrok-docx.fly.dev
```

**Fix**: Verify your Fly.io service is running:
```bash
curl https://wrok-docx.fly.dev/test
```

If not running:
```bash
fly deploy
```

### MCP Server Not Recognized

**Fix**:
1. Check JSON syntax in claude_desktop_config.json
2. Use absolute path to Python interpreter
3. Restart Claude Desktop

## Clean Up

After testing:

```bash
# Deactivate virtual environment
deactivate

# Remove test environment
rm -rf test_env
```

## Ready to Publish?

If all tests pass:
1. Your package installs correctly ✓
2. Imports work ✓
3. Can run as module ✓
4. Connects to Fly.io service ✓
5. Works in Claude Desktop ✓

→ You're ready to publish to PyPI! See `PUBLISH_TO_PYPI.md`

## Quick Test Script

Save this as `test_install.sh`:

```bash
#!/bin/bash
set -e

echo "Creating test environment..."
python3 -m venv test_env
source test_env/bin/activate

echo "Installing package..."
pip install dist/resume_generator_mcp-1.0.0-py3-none-any.whl

echo "Testing import..."
python -c "from resume_generator_mcp import main; print('✓ Import successful')"

echo "Testing API connection..."
python -c "import requests; r=requests.get('https://wrok-docx.fly.dev/test'); print(f'✓ API Status: {r.status_code}')"

echo ""
echo "✓ All tests passed!"
echo "Package is ready for publishing to PyPI"

deactivate
```

Run with:
```bash
chmod +x test_install.sh
./test_install.sh
```
