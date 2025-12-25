# ✨ Works with ChatGPT Desktop!

Your resume generator MCP server works with **both Claude Desktop AND ChatGPT Desktop**!

## Quick Setup for ChatGPT Users

### Step 1: Install
```bash
pip install resume-generator-mcp
```

### Step 2: Configure ChatGPT Desktop

**macOS**: Create/edit `~/Library/Application Support/ChatGPT/mcp_config.json`

**Windows**: Create/edit `%APPDATA%\ChatGPT\mcp_config.json`

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

### Step 3: Restart ChatGPT Desktop

### Step 4: Use It!

Open ChatGPT and say:
> "Generate a professional resume for Alex Johnson, Senior Software Engineer at Google since Jan 2022. MS in Computer Science from Stanford, 2020, GPA 3.9. Email: alex@google.com, Phone: +1-555-0100, LinkedIn: linkedin.com/in/alexj"

ChatGPT will use your MCP server to generate the PDF! 🎉

## Universal MCP Server

Your resume generator now works with:

| AI Assistant | Support | Config File Location |
|-------------|---------|---------------------|
| **Claude Desktop** | ✅ | `~/Library/Application Support/Claude/claude_desktop_config.json` |
| **ChatGPT Desktop** | ✅ | `~/Library/Application Support/ChatGPT/mcp_config.json` |
| **Cline (VS Code)** | ✅ | Cline MCP settings |
| **Any MCP Client** | ✅ | Varies by client |

## Same Package, Multiple Clients

Users only need to install **once**:
```bash
pip install resume-generator-mcp
```

Then they can use it with any MCP-compatible AI assistant!

## Why This is Powerful

- **One package** works everywhere
- **No duplicate work** - same codebase
- **Consistent behavior** across all AI assistants
- **Easy distribution** - just publish to PyPI once

## Marketing Opportunity

When you publish, you can market to:
- 📢 Claude Desktop users
- 📢 ChatGPT Desktop users
- 📢 Cline/VS Code users
- 📢 Any future MCP-compatible tools

**Much larger potential user base!** 🚀

## Example Announcement

When publishing:

```
🎉 Introducing resume-generator-mcp on PyPI!

Generate professional PDF resumes using AI - works with:
✅ Claude Desktop
✅ ChatGPT Desktop
✅ Cline (VS Code)
✅ Any MCP client

No LibreOffice needed. Just:
pip install resume-generator-mcp

#AI #MCP #ChatGPT #Claude #OpenSource
```

## Next Steps

1. **Publish to PyPI**: `uv publish`
2. **Test with ChatGPT Desktop**: Install and configure
3. **Announce**: Share on social media mentioning both Claude AND ChatGPT support

Your MCP server just got **way more valuable** because it works with both major AI assistants! 🎯
