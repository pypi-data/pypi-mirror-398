# Publishing resume-generator-mcp to PyPI

This guide explains how to publish your MCP server package to PyPI so anyone in the world can install it.

## Prerequisites

1. **PyPI Account**: Create accounts on both:
   - Test PyPI: https://test.pypi.org/account/register/
   - Production PyPI: https://pypi.org/account/register/

2. **API Tokens**: Generate API tokens (more secure than passwords):
   - Test PyPI: https://test.pypi.org/manage/account/token/
   - Production PyPI: https://pypi.org/manage/account/token/

   Save these tokens securely - you'll need them for uploading.

3. **Install twine**: Publishing tool for PyPI
   ```bash
   pip install twine
   ```

## Step 1: Test Your Package Locally

Before publishing, test the package locally:

```bash
# Create a new virtual environment
python3 -m venv test_env
source test_env/bin/activate

# Install from the local wheel
pip install dist/resume_generator_mcp-1.0.0-py3-none-any.whl

# Test that it works
python -m resume_generator_mcp --help

# Test import
python -c "from resume_generator_mcp import main; print('Success!')"

# Deactivate
deactivate
```

## Step 2: Publish to Test PyPI (Recommended First)

Test your package upload on Test PyPI before going to production:

```bash
# Upload to Test PyPI
python3 -m twine upload --repository testpypi dist/*

# You'll be prompted for:
# Username: __token__
# Password: <your-test-pypi-api-token>
```

## Step 3: Test Installation from Test PyPI

```bash
# Create new env for testing
python3 -m venv test_install
source test_install/bin/activate

# Install from Test PyPI
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ resume-generator-mcp

# Test it
python -m resume_generator_mcp --help

# Deactivate
deactivate
rm -rf test_install
```

## Step 4: Publish to Production PyPI

Once testing is successful, publish to production PyPI:

```bash
# Upload to PyPI
python3 -m twine upload dist/*

# You'll be prompted for:
# Username: __token__
# Password: <your-pypi-api-token>
```

## Step 5: Verify Installation

Test that users can install your package:

```bash
# Create fresh environment
python3 -m venv verify_install
source verify_install/bin/activate

# Install from PyPI
pip install resume-generator-mcp

# Test it
python -m resume_generator_mcp --help

# Deactivate and cleanup
deactivate
rm -rf verify_install
```

## Step 6: Update README URLs

After publishing, update the GitHub URLs in `pyproject.toml` and `README.md` to point to your actual repository.

Current placeholder URLs to replace:
- `https://github.com/yourusername/resume-generator-mcp`

## Using .pypirc for Authentication (Optional)

Instead of entering credentials each time, create `~/.pypirc`:

```ini
[distutils]
index-servers =
    pypi
    testpypi

[pypi]
username = __token__
password = pypi-YOUR-PRODUCTION-TOKEN-HERE

[testpypi]
repository = https://test.pypi.org/legacy/
username = __token__
password = pypi-YOUR-TEST-TOKEN-HERE
```

**Security**: Set proper permissions:
```bash
chmod 600 ~/.pypirc
```

## Updating Your Package

When you make changes and want to release a new version:

1. **Update version** in `pyproject.toml`:
   ```toml
   version = "1.0.1"  # Increment version
   ```

2. **Update CHANGELOG** in `README.md`

3. **Rebuild**:
   ```bash
   rm -rf dist/
   /tmp/build_env/bin/python -m build --outdir /tmp/dist
   cp -r /tmp/dist .
   ```

4. **Upload new version**:
   ```bash
   python3 -m twine upload dist/*
   ```

## Troubleshooting

### "File already exists" error
- You can't re-upload the same version
- Increment version number in `pyproject.toml`
- Rebuild and upload again

### Import errors after installation
- Check that `resume_generator_mcp` package structure is correct
- Verify `__init__.py` and `__main__.py` exist
- Test with `pip install -e .` locally first

### Missing dependencies
- Ensure all dependencies are listed in `pyproject.toml`
- Test in clean environment to catch missing deps

## After Publishing

### Announce Your Package

1. **GitHub**: Create a repository and push your code
2. **MCP Directory**: Submit to https://github.com/modelcontextprotocol/servers
3. **Social Media**: Share on Twitter, LinkedIn, etc.
4. **Documentation**: Consider creating full docs site

### Monitor Usage

- Check download stats: https://pypistats.org/packages/resume-generator-mcp
- Watch for issues on GitHub
- Respond to user feedback

## Success!

Once published, users worldwide can install your MCP server with:

```bash
pip install resume-generator-mcp
```

And configure it in Claude Desktop:

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

## Package Information

- **PyPI URL**: https://pypi.org/project/resume-generator-mcp/
- **Test PyPI URL**: https://test.pypi.org/project/resume-generator-mcp/
- **Download stats**: https://pypistats.org/packages/resume-generator-mcp

## Next Steps

Consider adding:
- Unit tests with pytest
- CI/CD with GitHub Actions
- Automated publishing on git tags
- Documentation website
- Example videos/GIFs
- Integration with other MCP clients
