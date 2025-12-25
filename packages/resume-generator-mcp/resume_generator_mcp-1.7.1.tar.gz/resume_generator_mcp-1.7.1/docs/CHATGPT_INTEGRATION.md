# ChatGPT Integration Guide

**UPDATE**: ChatGPT now supports MCP! Your resume generator works with ChatGPT the same way as Claude Desktop.

## ⭐ Best Option: Use MCP (NEW!)

ChatGPT Desktop now supports MCP servers, just like Claude Desktop!

### Setup for ChatGPT Desktop

Once you publish to PyPI, users can install and configure it:

1. **Install**:
```bash
pip install resume-generator-mcp
```

2. **Configure ChatGPT Desktop**:

Add to ChatGPT's MCP configuration file:
- **macOS**: `~/Library/Application Support/ChatGPT/mcp_config.json`
- **Windows**: `%APPDATA%\ChatGPT\mcp_config.json`

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

3. **Restart ChatGPT Desktop**

4. **Use it**:
> "Generate a resume for Alex Johnson, Senior Engineer at Google..."

**That's it!** Your MCP server now works with BOTH Claude Desktop and ChatGPT Desktop! 🎉

---

## Alternative Options (If Not Using MCP)

Your resume generator can also work with ChatGPT through other approaches:

## Option 1: Custom GPT (No Code Required)

### What You Get
- Natural language interface
- API integration
- Shareable link

### Limitations
- **Cannot download PDFs** (ChatGPT limitation - Custom GPTs can't return files)
- Requires ChatGPT Plus ($20/month)
- Can only validate and call API

### Setup Steps

1. **Go to ChatGPT**: https://chat.openai.com/
2. **Create Custom GPT**: Profile → "My GPTs" → "Create"
3. **Configure**:

#### Name
```
Professional Resume Generator
```

#### Description
```
Generates professional PDF resumes from your career information. Supports natural language input.
```

#### Instructions
```
You are an expert resume generation assistant. Help users create professional PDF resumes.

When users provide their information, collect:
1. Personal info: name, email, phone, location, LinkedIn URL
2. Education: degree, institution, location, graduation date, GPA
3. Work experience: company, title, location, dates, achievements
4. Skills (optional)

Format the data as valid YAML following this structure:

```yaml
name: Full Name
email: email@example.com
phone: +1 555 123 4567
location: City, State
linkedin: https://www.linkedin.com/in/username/

education:
  title: Degree and Field
  college: University Name
  location: City, State
  period: Month Year
  gpa: X.X / 4.0

roles:
  - company: Company Name
    title: Job Title
    locations:
      - location: City, State
        start_date: Month Year
        end_date: Month Year or Present
    achievements:
      - Achievement bullet point 1
      - Achievement bullet point 2

skills:
  - Skill 1
  - Skill 2
```

Once you have complete information, use the generateResume action to create the PDF.

Note: Due to ChatGPT limitations, I can validate your data and confirm the API call, but cannot directly provide the PDF download. The PDF is generated on the backend.
```

#### Conversation Starters
```
- Help me create a professional resume
- Generate a resume from my LinkedIn
- I need a resume for a software engineering role
- Update my resume with new experience
```

4. **Add Action**: Click "Create new action"

**OpenAPI Schema**:
```yaml
openapi: 3.1.0
info:
  title: Resume Generator API
  description: Generates professional PDF resumes from YAML data
  version: 1.0.0
servers:
  - url: https://wrok-docx.fly.dev
    description: Production server
paths:
  /process_resume:
    post:
      operationId: generateResume
      summary: Generate a PDF resume from YAML data
      description: Accepts YAML resume data and returns a PDF
      requestBody:
        required: true
        content:
          multipart/form-data:
            schema:
              type: object
              required:
                - yaml_file
              properties:
                yaml_file:
                  type: string
                  format: binary
                  description: YAML file containing resume data
      responses:
        '200':
          description: PDF generated successfully
          content:
            application/pdf:
              schema:
                type: string
                format: binary
        '400':
          description: Invalid YAML or missing required fields
          content:
            application/json:
              schema:
                type: object
                properties:
                  error:
                    type: string
  /test:
    get:
      operationId: testAPI
      summary: Test API connectivity
      responses:
        '200':
          description: API is working
          content:
            application/json:
              schema:
                type: object
```

5. **Save and Test**

Try asking your Custom GPT:
> "Create a resume for Alex Johnson, Senior Software Engineer at Google since Jan 2022, MS in CS from Stanford 2020, GPA 3.9, email alex@google.com"

### Workaround for PDF Downloads

Since Custom GPTs can't return files, tell users:

```
To download the actual PDF:
1. Go to: https://wrok-docx.fly.dev
2. Upload the YAML I've created
3. Download your PDF

Or use the MCP server with Claude Desktop for direct PDF generation.
```

---

## Option 2: OpenAI API + Function Calling (For Developers)

If you're building an application, integrate with OpenAI's API:

### Python Example

```python
import openai
import requests
import yaml

# Configure OpenAI
openai.api_key = "your-openai-api-key"

# Define function for ChatGPT to call
functions = [
    {
        "name": "generate_resume",
        "description": "Generate a professional PDF resume from structured data",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "email": {"type": "string"},
                "phone": {"type": "string"},
                "location": {"type": "string"},
                "linkedin": {"type": "string"},
                "education": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "college": {"type": "string"},
                        "location": {"type": "string"},
                        "period": {"type": "string"},
                        "gpa": {"type": "string"}
                    }
                },
                "roles": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "company": {"type": "string"},
                            "title": {"type": "string"},
                            "locations": {"type": "array"},
                            "achievements": {"type": "array"}
                        }
                    }
                }
            },
            "required": ["name", "email", "phone", "location", "linkedin", "education", "roles"]
        }
    }
]

# Chat with function calling
response = openai.ChatCompletion.create(
    model="gpt-4",
    messages=[
        {"role": "user", "content": "Create a resume for Alex Johnson, Senior Engineer at Google"}
    ],
    functions=functions,
    function_call="auto"
)

# If ChatGPT calls the function
if response.choices[0].message.get("function_call"):
    function_args = json.loads(response.choices[0].message.function_call.arguments)

    # Convert to YAML
    yaml_content = yaml.dump(function_args, default_flow_style=False)

    # Call your API
    files = {'yaml_file': ('resume.yaml', yaml_content.encode('utf-8'), 'application/x-yaml')}
    api_response = requests.post('https://wrok-docx.fly.dev/process_resume', files=files)

    # Save PDF
    with open('resume.pdf', 'wb') as f:
        f.write(api_response.content)

    print("✓ Resume generated: resume.pdf")
```

### JavaScript Example

```javascript
const OpenAI = require('openai');
const axios = require('axios');
const FormData = require('form-data');
const yaml = require('js-yaml');
const fs = require('fs');

const openai = new OpenAI({ apiKey: 'your-api-key' });

async function generateResume(userMessage) {
  const response = await openai.chat.completions.create({
    model: 'gpt-4',
    messages: [{ role: 'user', content: userMessage }],
    functions: [{
      name: 'generate_resume',
      description: 'Generate a PDF resume',
      parameters: {
        type: 'object',
        properties: {
          name: { type: 'string' },
          email: { type: 'string' },
          // ... other fields
        }
      }
    }],
    function_call: 'auto'
  });

  const functionCall = response.choices[0].message.function_call;
  if (functionCall) {
    const resumeData = JSON.parse(functionCall.arguments);
    const yamlContent = yaml.dump(resumeData);

    // Call your API
    const formData = new FormData();
    formData.append('yaml_file', Buffer.from(yamlContent), 'resume.yaml');

    const apiResponse = await axios.post(
      'https://wrok-docx.fly.dev/process_resume',
      formData,
      { responseType: 'arraybuffer', headers: formData.getHeaders() }
    );

    fs.writeFileSync('resume.pdf', apiResponse.data);
    console.log('✓ Resume generated!');
  }
}

generateResume('Create a resume for Alex Johnson, Senior Engineer');
```

---

## Option 3: Web App with ChatGPT Integration

Build a simple web app where users interact with ChatGPT and download PDFs:

### Architecture
```
User → Web App UI → OpenAI API (extracts data) → Your Fly.io API → PDF Download
```

### Quick Implementation (Flask + OpenAI)

```python
from flask import Flask, render_template, request, send_file
import openai
import requests
import yaml
import tempfile

app = Flask(__name__)
openai.api_key = "your-key"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    user_message = request.json['message']

    # ChatGPT extracts structured data
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "Extract resume data as YAML"},
            {"role": "user", "content": user_message}
        ]
    )

    yaml_data = response.choices[0].message.content

    # Generate PDF via your API
    files = {'yaml_file': ('resume.yaml', yaml_data.encode(), 'application/x-yaml')}
    pdf_response = requests.post('https://wrok-docx.fly.dev/process_resume', files=files)

    # Save and return PDF
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as f:
        f.write(pdf_response.content)
        return send_file(f.name, as_attachment=True, download_name='resume.pdf')

if __name__ == '__main__':
    app.run()
```

---

## Option 4: Make Your API Publicly Accessible

Update your Fly.io app to accept direct web requests:

### Add CORS to app.py

```python
from flask import Flask
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Allow requests from any origin

# Your existing routes...
```

### Create Simple Web Interface

Host a simple HTML page that calls your API:

```html
<!DOCTYPE html>
<html>
<head>
    <title>Resume Generator</title>
</head>
<body>
    <h1>Generate Your Resume</h1>
    <textarea id="yaml-input" rows="20" cols="80">
name: Your Name
email: you@example.com
...
    </textarea>
    <button onclick="generatePDF()">Generate PDF</button>

    <script>
    async function generatePDF() {
        const yaml = document.getElementById('yaml-input').value;
        const formData = new FormData();
        formData.append('yaml_file', new Blob([yaml]), 'resume.yaml');

        const response = await fetch('https://wrok-docx.fly.dev/process_resume', {
            method: 'POST',
            body: formData
        });

        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'resume.pdf';
        a.click();
    }
    </script>
</body>
</html>
```

---

## Comparison: ChatGPT vs Claude

| Feature | Claude Desktop (MCP) | ChatGPT (Custom GPT) |
|---------|---------------------|---------------------|
| PDF Download | ✅ Direct download | ❌ Cannot return files |
| Setup | pip install + config | Web UI configuration |
| Natural Language | ✅ | ✅ |
| Local Files | ✅ Can save locally | ❌ Web only |
| Cost for Users | Free | $20/month (Plus) |
| Best For | Power users, developers | Casual users |

---

## Recommendation

**For the best experience:**
1. **Keep MCP for Claude Desktop** (best user experience)
2. **Create Custom GPT** for ChatGPT users (with workaround instructions)
3. **Build a simple web app** if you want direct PDF downloads for ChatGPT users

**The MCP + Claude Desktop approach is superior** because it can actually save PDFs locally, which ChatGPT Custom GPTs cannot do due to platform limitations.

---

## Next Steps

1. **Publish MCP server to PyPI** (for Claude users) ⭐ Recommended
2. **Create Custom GPT** (for ChatGPT users) - Quick to set up
3. **Build web app** (if you want a universal solution)

The MCP server is already complete and ready to publish. Would you like help with any of these options?
