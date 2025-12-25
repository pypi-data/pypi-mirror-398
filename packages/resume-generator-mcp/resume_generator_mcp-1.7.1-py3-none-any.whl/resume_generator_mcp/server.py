#!/usr/bin/env python3
"""
MCP Server for Resume PDF Generation (Remote Service)

This MCP server connects to a remote Flask API (deployed on Fly.io) for PDF generation.
Users don't need to install LibreOffice locally - all processing happens on the remote service.

The server automatically handles resume generation requests and can work with:
- Structured YAML/JSON data
- Natural language descriptions
- Partial information (with smart prompting for missing fields)
"""

import os
import sys
import yaml
import json
import requests
import logging
from pathlib import Path
from typing import Any, Dict, Optional, List
from mcp.server.fastmcp import FastMCP
from mcp.types import TextContent

# Configure logging to stderr (required for STDIO-based MCP servers)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger(__name__)

# Initialize MCP server
mcp = FastMCP("resume-generator")

# Remote API URL - defaults to official Wrok PDF service
# Users don't need to configure this unless they're self-hosting
API_URL = os.getenv("RESUME_API_URL", "https://wrok-docx.fly.dev")


@mcp.prompt()
def resume_workflow_guide() -> str:
    """
    Guide for LLMs on how to handle resume creation requests.
    Use this workflow whenever a user asks to create, generate, or build a resume.
    """
    return """
# Resume Generation Workflow

When a user asks to create a resume, follow this workflow:

## Step 1: Gather Information
If the user hasn't provided complete information, ask for:
- Full name
- Contact info (email, phone, location, LinkedIn)
- Education (degree, school, graduation date, GPA)
- Work experience (companies, titles, dates, achievements)
- Skills (optional but recommended)

## Step 2: Structure as YAML
Convert the information into YAML format following this structure:

```yaml
name: Full Name
email: email@example.com
phone: +1 555-123-4567
location: City, State
linkedin: linkedin.com/in/username

education:
  title: Degree in Major
  college: University Name
  location: City, State
  period: Graduation Date
  gpa: X.X / 4.0

roles:
  - company: Company Name
    title: Job Title
    locations:
      - location: City, State
        start_date: Mon YYYY
        end_date: Mon YYYY or Present
    achievements:
      - Quantified achievement with impact
      - Another achievement with metrics

skills:
  - Skill 1
  - Skill 2
```

## Step 3: Generate PDF
Call the `create_resume` tool with the YAML content and desired filename.

## Step 4: Confirm
Inform the user of the PDF location and ask if they need any modifications.

## Tips:
- Use action verbs for achievements (Led, Developed, Increased, etc.)
- Include metrics and impact where possible
- Keep achievements concise but specific
- Format dates consistently (e.g., "Jan 2020")
"""


def validate_resume_data(data: Dict[str, Any]) -> tuple[bool, Optional[str]]:
    """
    Validate that resume data contains all required fields.

    Args:
        data: Dictionary containing resume data

    Returns:
        Tuple of (is_valid, error_message)
    """
    required_fields = ['name', 'email', 'phone', 'location', 'linkedin', 'education', 'roles']

    # Check top-level required fields
    for field in required_fields:
        if field not in data:
            return False, f"Missing required field: {field}"

    # Validate education structure
    education_fields = ['title', 'college', 'location', 'period', 'gpa']
    for field in education_fields:
        if field not in data['education']:
            return False, f"Missing required education field: {field}"

    # Validate roles structure
    if not isinstance(data['roles'], list) or len(data['roles']) == 0:
        return False, "roles must be a non-empty array"

    for idx, role in enumerate(data['roles']):
        if 'company' not in role:
            return False, f"Role {idx} missing 'company' field"
        if 'title' not in role:
            return False, f"Role {idx} missing 'title' field"
        if 'locations' not in role or not isinstance(role['locations'], list):
            return False, f"Role {idx} missing 'locations' array"
        if 'achievements' not in role or not isinstance(role['achievements'], list):
            return False, f"Role {idx} missing 'achievements' array"

        # Validate locations
        for loc_idx, location in enumerate(role['locations']):
            if 'location' not in location:
                return False, f"Role {idx}, location {loc_idx} missing 'location' field"
            if 'start_date' not in location:
                return False, f"Role {idx}, location {loc_idx} missing 'start_date' field"
            if 'end_date' not in location:
                return False, f"Role {idx}, location {loc_idx} missing 'end_date' field"

    return True, None


def check_api_status() -> tuple[bool, str]:
    """
    Check if the remote API is available.

    Returns:
        Tuple of (is_available, message)
    """
    try:
        response = requests.get(f"{API_URL}/test", timeout=10)
        if response.status_code == 200:
            return True, "Remote API is available"
        else:
            return False, f"Remote API returned status {response.status_code}"
    except requests.exceptions.ConnectionError:
        return False, f"Cannot connect to API at {API_URL}"
    except requests.exceptions.Timeout:
        return False, f"Connection to {API_URL} timed out"
    except Exception as e:
        return False, f"Error checking API: {str(e)}"


def get_writable_output_path(filename: str) -> Path:
    """
    Determine a writable output path for the PDF file.

    Args:
        filename: The desired filename for the PDF

    Returns:
        Path object pointing to a writable location
    """
    # Try current directory first
    try:
        output_path = Path.cwd() / filename
        # Test if writable by checking parent directory
        if os.access(output_path.parent, os.W_OK):
            return output_path
    except (PermissionError, OSError):
        pass

    # Fall back to user's Downloads or home directory
    home = Path.home()
    downloads = home / "Downloads"
    if downloads.exists() and os.access(downloads, os.W_OK):
        return downloads / filename
    else:
        return home / filename


def generate_pdf_via_api(yaml_content: str, output_path: Optional[str] = None) -> tuple[bool, str, Optional[bytes]]:
    """
    Generate PDF by sending request to remote API.

    Args:
        yaml_content: YAML resume data
        output_path: Optional path where PDF should be saved (if None, only returns bytes)

    Returns:
        Tuple of (success, message, pdf_bytes)
    """
    try:
        # Check if API is available
        is_available, message = check_api_status()
        if not is_available:
            return False, message, None

        logger.info(f"Sending request to API at {API_URL}")

        # Create multipart form data
        files = {
            'yaml_file': ('resume.yaml', yaml_content.encode('utf-8'), 'application/x-yaml')
        }

        response = requests.post(
            f"{API_URL}/process_resume",
            files=files,
            timeout=120  # Increased timeout for PDF generation (LibreOffice conversion can be slow)
        )

        if response.status_code == 200:
            pdf_bytes = response.content

            # Save to file if output path provided
            if output_path:
                with open(output_path, 'wb') as f:
                    f.write(pdf_bytes)
                logger.info(f"PDF saved to: {output_path}")
                return True, f"Resume PDF successfully created at: {output_path}", pdf_bytes
            else:
                logger.info("PDF generated successfully (not saved to disk)")
                return True, "Resume PDF generated successfully", pdf_bytes
        else:
            error_msg = response.text
            logger.error(f"API error: {error_msg}")
            return False, f"PDF generation failed: {error_msg}", None

    except requests.exceptions.Timeout:
        return False, "Request timed out. PDF generation took too long.", None
    except requests.exceptions.ConnectionError:
        return False, f"Cannot connect to API at {API_URL}. Please check your internet connection.", None
    except Exception as e:
        logger.exception("Error generating PDF via API")
        return False, f"Error: {str(e)}", None


@mcp.tool()
def generate_resume(
    name: str,
    email: str,
    phone: str,
    location: str,
    linkedin: str,
    education_title: str,
    education_college: str,
    education_location: str,
    education_period: str,
    education_gpa: str,
    roles_json: str,
    skills: Optional[str] = None,
    output_filename: str = "resume.pdf"
) -> List[TextContent]:
    """
    Generate a professional PDF resume from the provided information.

    **CRITICAL**: After this tool returns successfully, you MUST use the Read tool to read and display
    the PDF file at the path returned in the response. This will show the PDF inline to the user.

    Args:
        name: Full name (e.g., "Alex Johnson")
        email: Email address (e.g., "alex@example.com")
        phone: Phone number with country code (e.g., "+1 555 123 4567")
        location: Current location (e.g., "Seattle, WA 98101")
        linkedin: LinkedIn profile URL (e.g., "https://www.linkedin.com/in/alexjohnson/")
        education_title: Degree and field (e.g., "Master of Science in Computer Science")
        education_college: Institution name (e.g., "University of Washington")
        education_location: Institution location (e.g., "Seattle, USA")
        education_period: Graduation date (e.g., "June 2015")
        education_gpa: Grade point average (e.g., "3.9 / 4.0")
        roles_json: JSON string containing array of roles. Each role must have: company, title, locations (array with location, start_date, end_date), and achievements (array of strings)
        skills: Optional comma-separated list of skills (e.g., "Python, Cloud Architecture, Team Leadership")
        output_filename: Name of the output PDF file (default: "resume.pdf")

    Returns:
        Success message with the path to the generated PDF, or error message

    Example roles_json:
    [
      {
        "company": "TechCorp",
        "title": "Senior Architect",
        "locations": [
          {"location": "Seattle, USA", "start_date": "Jan 2022", "end_date": "Present"}
        ],
        "achievements": [
          "Led team of 10 engineers in cloud migration",
          "Reduced infrastructure costs by 40%"
        ]
      }
    ]
    """
    try:
        # Parse roles JSON
        try:
            roles = json.loads(roles_json)
        except json.JSONDecodeError as e:
            return f"Error: Invalid JSON in roles_json: {str(e)}"

        # Build resume data structure
        resume_data = {
            'name': name,
            'email': email,
            'phone': phone,
            'location': location,
            'linkedin': linkedin,
            'education': {
                'title': education_title,
                'college': education_college,
                'location': education_location,
                'period': education_period,
                'gpa': education_gpa
            },
            'roles': roles
        }

        # Add skills if provided
        if skills:
            resume_data['skills'] = [s.strip() for s in skills.split(',')]

        # Validate data
        is_valid, error_msg = validate_resume_data(resume_data)
        if not is_valid:
            return f"Validation error: {error_msg}"

        # Convert to YAML
        yaml_content = yaml.dump(resume_data, default_flow_style=False, allow_unicode=True)

        # Generate PDF via API (don't save to disk)
        success, message, pdf_bytes = generate_pdf_via_api(yaml_content)

        if success and pdf_bytes:
            # Save to disk
            output_path = get_writable_output_path(output_filename)
            with open(output_path, 'wb') as f:
                f.write(pdf_bytes)

            # Calculate file size
            file_size_kb = len(pdf_bytes) / 1024

            # Return success message - Claude will need to read the PDF to display it
            return [TextContent(
                type="text",
                text=f"""Resume PDF created successfully and saved to {output_path} ({file_size_kb:.1f} KB).

ACTION REQUIRED: You must now use the Read tool with file_path="{output_path}" to display the PDF to the user."""
            )]
        else:
            return [TextContent(type="text", text=f"Error: {message}")]

    except Exception as e:
        logger.exception("Error in generate_resume tool")
        return [TextContent(type="text", text=f"Error: {str(e)}")]


@mcp.tool()
def create_resume(yaml_content: str, output_filename: str = "resume.pdf") -> List[TextContent]:
    """
    PRIMARY TOOL for resume generation. Use this tool whenever the user asks to create, generate,
    or build a resume/CV.

    WORKFLOW for LLM:
    1. When user requests a resume, ask for their information (or use provided info)
    2. Structure the information into YAML format following the schema below
    3. Call this tool with the generated YAML content
    4. **CRITICAL**: After this tool returns successfully, you MUST use the Read tool to read and display
       the PDF file at the path returned in the response. This will allow you to show the PDF inline
       in the conversation

    Args:
        yaml_content: Complete YAML resume data with all required fields (see schema below)
        output_filename: Desired PDF filename (default: "resume.pdf")

    Returns:
        Success message with PDF file path, or detailed error if validation fails

    REQUIRED YAML SCHEMA:
    name: string                    # Full name
    email: string                   # Email address
    phone: string                   # Phone with country code (e.g., "+1 555-123-4567")
    location: string                # Current city/state
    linkedin: string                # LinkedIn URL or handle

    education:
      title: string                 # Degree and major
      college: string               # University name
      location: string              # University location
      period: string                # Graduation date or date range
      gpa: string                   # GPA or achievement

    roles:                          # Array of work experiences
      - company: string             # Company name
        title: string               # Job title
        locations:                  # Array of location periods
          - location: string        # Office/city location
            start_date: string      # Start date (e.g., "Jan 2020")
            end_date: string        # End date or "Present"
        achievements:               # Array of bullet points
          - string                  # Achievement/responsibility
          - string

    skills:                         # Optional array of skills
      - string

    EXAMPLE YAML:
    name: Sarah Chen
    email: sarah.chen@email.com
    phone: +1 650-555-0123
    location: San Francisco, CA
    linkedin: linkedin.com/in/sarachen

    education:
      title: Master of Science in Computer Science
      college: Stanford University
      location: Stanford, CA
      period: June 2018
      gpa: 3.9 / 4.0

    roles:
      - company: Tech Innovations Inc
        title: Senior Software Engineer
        locations:
          - location: San Francisco, CA
            start_date: Mar 2020
            end_date: Present
        achievements:
          - Led development of microservices architecture serving 10M+ users
          - Reduced API latency by 60% through caching optimization
          - Mentored team of 5 junior engineers

    skills:
      - Python
      - AWS
      - Docker
    """
    try:
        # Parse and validate YAML
        try:
            resume_data = yaml.safe_load(yaml_content)
        except yaml.YAMLError as e:
            return f"Error: Invalid YAML content: {str(e)}"

        # Validate structure
        is_valid, error_msg = validate_resume_data(resume_data)
        if not is_valid:
            return f"Validation error: {error_msg}"

        # Generate PDF via API (don't save to disk initially)
        success, message, pdf_bytes = generate_pdf_via_api(yaml_content)

        if success and pdf_bytes:
            # Save to disk
            output_path = get_writable_output_path(output_filename)
            with open(output_path, 'wb') as f:
                f.write(pdf_bytes)

            # Calculate file size
            file_size_kb = len(pdf_bytes) / 1024

            # Return success message - Claude will need to read the PDF to display it
            return [TextContent(
                type="text",
                text=f"""Resume PDF created successfully and saved to {output_path} ({file_size_kb:.1f} KB).

ACTION REQUIRED: You must now use the Read tool with file_path="{output_path}" to display the PDF to the user."""
            )]
        else:
            return [TextContent(type="text", text=f"Error: {message}")]

    except Exception as e:
        logger.exception("Error in generate_resume_from_yaml tool")
        return [TextContent(type="text", text=f"Error: {str(e)}")]


@mcp.tool()
def validate_resume_yaml(yaml_content: str) -> str:
    """
    Validate YAML resume content without generating a PDF.

    Args:
        yaml_content: YAML content to validate

    Returns:
        Validation result message
    """
    try:
        # Parse YAML
        try:
            resume_data = yaml.safe_load(yaml_content)
        except yaml.YAMLError as e:
            return f"Invalid YAML syntax: {str(e)}"

        # Validate structure
        is_valid, error_msg = validate_resume_data(resume_data)

        if is_valid:
            return "✓ Resume data is valid and ready for PDF generation"
        else:
            return f"✗ Validation failed: {error_msg}"

    except Exception as e:
        logger.exception("Error in validate_resume_yaml tool")
        return f"Error during validation: {str(e)}"


@mcp.tool()
def check_service_status() -> str:
    """
    Check if the remote resume generation service is running and accessible.

    Returns:
        Status message about service availability
    """
    is_available, message = check_api_status()

    if is_available:
        return f"✓ {message}\n\nService URL: {API_URL}\n\nYou can generate resumes!"
    else:
        return f"✗ {message}\n\nService URL: {API_URL}\n\nPlease check your internet connection or contact support."


@mcp.resource("resume://schema")
def get_resume_schema() -> str:
    """Get the YAML schema specification for resumes"""
    return """
Resume YAML Schema:

Required fields:
- name: string (full name)
- email: string (email address)
- phone: string (phone number with country code)
- location: string (current location)
- linkedin: string (LinkedIn profile URL)

- education: object with:
  - title: string (degree and field)
  - college: string (institution name)
  - location: string (institution location)
  - period: string (graduation date)
  - gpa: string (grade point average)

- roles: array of role objects, each with:
  - company: string (company name)
  - title: string (job title)
  - locations: array of location objects, each with:
    - location: string (work location)
    - start_date: string (start date)
    - end_date: string (end date or "Present")
  - achievements: array of strings (bullet points)

Optional fields:
- skills: array of strings (skills/technologies)

Example:
name: Alex Johnson
email: alex@example.com
phone: +1 555 123 4567
location: Seattle, WA 98101
linkedin: https://www.linkedin.com/in/alexjohnson/

education:
  title: Master of Science in Computer Science
  college: University of Washington
  location: Seattle, USA
  period: June 2015
  gpa: 3.9 / 4.0

roles:
  - company: TechCorp
    title: Senior Software Architect
    locations:
      - location: Seattle, USA
        start_date: Jan 2022
        end_date: Present
    achievements:
      - Led team of 10 engineers in cloud migration
      - Reduced infrastructure costs by 40%

skills:
  - Python
  - Cloud Architecture
  - Team Leadership
"""


@mcp.resource("resume://example")
def get_example_resume() -> str:
    """Get an example resume YAML for reference"""
    return """
name: Alex Johnson
linkedin: https://www.linkedin.com/in/alexjohnson/
email: alex.johnson@email.com
phone: +1 555 123 4567
location: Seattle, WA 98101

education:
  title: Master of Science in Computer Science
  college: University of Washington
  location: Seattle, USA
  period: June 2015
  gpa: 3.9 / 4.0

roles:
  - company: TechCorp
    title: Senior Software Architect
    locations:
      - location: Seattle, USA
        start_date: Jan 2022
        end_date: Present
    achievements:
      - Led the redesign of the company's flagship product, resulting in a 30% increase in user engagement
      - Mentored a team of 10 junior developers, implementing best practices that improved code quality by 40%
      - Architected a microservices-based solution that increased system scalability by 300%

  - company: InnoSoft
    title: Lead Developer
    locations:
      - location: San Francisco, USA
        start_date: Mar 2018
        end_date: Dec 2021
    achievements:
      - Developed a scalable microservices architecture that improved system reliability to 99.9%
      - Implemented an AI-driven recommendation engine that increased customer retention by 20%

skills:
  - Cloud Architecture
  - Microservices
  - Python
  - Java
  - Team Leadership
"""


def main():
    """Entry point for the MCP server"""
    mcp.run()


if __name__ == "__main__":
    main()
