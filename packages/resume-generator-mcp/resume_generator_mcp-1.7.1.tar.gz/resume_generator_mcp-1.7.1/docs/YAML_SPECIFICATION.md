# Resume YAML Specification

This document describes the YAML format required to generate PDF resumes using the WROK-DOCX service.

## Table of Contents

- [Overview](#overview)
- [Schema Structure](#schema-structure)
- [Field Specifications](#field-specifications)
- [Complete Example](#complete-example)
- [Validation Rules](#validation-rules)
- [Usage Instructions](#usage-instructions)

## Overview

The resume service accepts YAML files (or JSON equivalents) that describe your professional resume. The YAML is processed through a Jinja2 template and converted into a professionally formatted PDF using LibreOffice.

**Supported Formats:**
- YAML (`.yaml` or `.yml`)
- JSON (`.json`)

## Schema Structure

```yaml
# Personal Information (Required)
name: string
email: string
phone: string
location: string
linkedin: string (URL)

# Education (Required)
education:
  title: string
  college: string
  location: string
  period: string
  gpa: string

# Professional Experience (Required)
roles:
  - company: string
    title: string
    locations:
      - location: string
        start_date: string
        end_date: string
    achievements:
      - string (achievement 1)
      - string (achievement 2)

# Skills (Optional)
skills:
  - string (skill 1)
  - string (skill 2)
```

## Field Specifications

### Personal Information

All personal information fields are **required** and appear at the top of the resume.

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `name` | String | Your full name | `"Alex Johnson"` |
| `email` | String | Professional email address | `"alex.johnson@email.com"` |
| `phone` | String | Contact phone number with country code | `"+1 555 123 4567"` |
| `location` | String | Current city, state, and ZIP code | `"Seattle, WA 98101"` |
| `linkedin` | String (URL) | Full LinkedIn profile URL | `"https://www.linkedin.com/in/alexjohnson/"` |

### Education

The `education` section is **required** and contains details about your highest degree or most relevant educational qualification.

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `title` | String | Degree name and field of study | `"Master of Science in Computer Science"` |
| `college` | String | Name of the institution | `"University of Washington"` |
| `location` | String | City and country of the institution | `"Seattle, USA"` |
| `period` | String | Graduation date or time period | `"June 2015"` |
| `gpa` | String | Grade point average (optional format) | `"3.9 / 4.0"` |

### Professional Experience (Roles)

The `roles` section is **required** and contains an array of your professional positions. Each role includes company information, job title(s), location(s), and achievements.

#### Role Object

| Field | Type | Description |
|-------|------|-------------|
| `company` | String | Company name |
| `title` | String | Job title for this role |
| `locations` | Array | List of location objects (see below) |
| `achievements` | Array of Strings | Bullet points describing your accomplishments |

#### Location Object

Each role can have multiple locations if you worked in different offices during the same position.

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `location` | String | City and country | `"Seattle, USA"` |
| `start_date` | String | Start date of this position at this location | `"Jan 2022"` |
| `end_date` | String | End date (use "Present" for current positions) | `"Present"` or `"Dec 2021"` |

#### Achievements

- Each achievement is a string (bullet point)
- Recommended: 3-6 achievements per role
- Use action verbs and quantify results when possible
- Keep each achievement to 1-2 sentences

### Skills

The `skills` section is **optional** and contains an array of your technical and professional skills.

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `skills` | Array of Strings | List of skills | `["Python", "Cloud Architecture", "Team Leadership"]` |

**Recommendations:**
- List 8-12 key skills
- Mix technical and soft skills
- Prioritize skills most relevant to your target role

## Complete Example

### Example 1: Single Role at Multiple Locations

```yaml
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
      - Led the redesign of the company's flagship product, resulting in a 30% increase in user engagement and a 25% reduction in infrastructure costs.
      - Mentored a team of 10 junior developers, implementing best practices that improved code quality by 40%.
      - Architected a microservices-based solution that increased system scalability by 300%.
      - Implemented CI/CD pipelines that reduced deployment time from hours to minutes.

  - company: InnoSoft
    title: Lead Developer
    locations:
      - location: San Francisco, USA
        start_date: Mar 2018
        end_date: Dec 2021
    achievements:
      - Developed a scalable microservices architecture that improved system reliability to 99.9%.
      - Implemented an AI-driven recommendation engine that increased customer retention by 20%.
      - Led a team of 8 engineers in delivering features that generated $2M in annual revenue.

  - company: CodeWizards
    title: Software Engineer
    locations:
      - location: Portland, USA
        start_date: Jul 2015
        end_date: Feb 2018
      - location: Boston, USA
        start_date: Sep 2013
        end_date: Jun 2015
    achievements:
      - Optimized database queries, resulting in a 50% reduction in response time for critical API endpoints.
      - Developed a custom testing framework that reduced QA time by 30% and improved bug detection rates.
      - Collaborated with cross-functional teams to deliver a major product launch on schedule.

skills:
  - Cloud Architecture
  - Microservices
  - Python
  - Java
  - DevOps
  - Machine Learning
  - Agile Methodologies
  - System Design
  - Database Optimization
  - Team Leadership
```

### Example 2: Multiple Titles at Same Company

For multiple positions at the same company, create separate role entries for each title:

```yaml
name: Sravan Sarraju
linkedin: https://www.linkedin.com/in/sksarraju/
email: sravan.sarraju@icloud.com
phone: +1 415 855 5378
location: Dublin, CA 94568

education:
  title: Bachelor of Engineering in Computer Science
  college: Osmania University
  location: Hyderabad, India
  period: May 2014
  gpa: 3.8 / 4.0

roles:
  - company: Oracle
    title: Architect
    locations:
      - location: Redwood City, USA
        start_date: Sep 2024
        end_date: Present
    achievements:
      - Architected and implemented a cloud-native solution for a major CRM product.
      - Led three cross-functional teams (2 managers, 3 Staff+ engineers, 11 engineers).

  - company: Oracle
    title: Senior Principal Engineer
    locations:
      - location: Redwood City, USA
        start_date: Mar 2018
        end_date: Sep 2024
    achievements:
      - Spearheaded the integration of modern observability into CRM.
      - Conceptualized and championed "Routines," a workflow orchestration platform.
      - Mentored over 20 engineers at various levels.

  - company: Oracle
    title: Principal Engineer
    locations:
      - location: Redwood City, USA
        start_date: May 2016
        end_date: Mar 2018
      - location: Hyderabad, India
        start_date: Sep 2013
        end_date: Mar 2016
    achievements:
      - Led teams in upgrading the CRM platform's extensibility.
      - Developed a robust upgrade framework for customer customizations.

skills:
  - Technical Leadership
  - Software Architecture
  - Cloud-native Development
  - Microservices
  - CI/CD
  - Performance Optimization
  - Observability
  - Java, Python, C++
```

## Validation Rules

### Required Fields

The following fields are **mandatory** and will cause errors if missing:

- `name`
- `email`
- `phone`
- `location`
- `linkedin`
- `education` (all sub-fields)
- `roles` (at least one role entry)

### Data Type Constraints

| Field | Constraint | Notes |
|-------|-----------|-------|
| `linkedin` | Must be a valid URL | Should start with `http://` or `https://` |
| `roles` | Must be an array | Cannot be empty |
| `locations` | Must be an array within each role | At least one location required per role |
| `achievements` | Must be an array of strings | At least one achievement recommended |
| `skills` | Optional array of strings | If included, should have at least 3 items |

### Best Practices

1. **Consistency**: Use consistent date formats throughout (e.g., "Jan 2022" or "January 2022")
2. **Chronological Order**: List roles in reverse chronological order (most recent first)
3. **Achievement Quality**: Use STAR method (Situation, Task, Action, Result) for achievements
4. **Length**: Keep achievements concise (1-2 lines each)
5. **Quantification**: Include numbers and percentages where possible
6. **Special Characters**: Avoid using special characters that might break YAML syntax (`:`, `{`, `}`, `[`, `]`)
7. **Multi-line Text**: For long achievements, use YAML string continuation:
   ```yaml
   achievements:
     - >
       Led a comprehensive initiative spanning multiple teams to deliver
       a critical product feature under tight deadlines.
   ```

## Usage Instructions

### Step 1: Create Your YAML File

Create a file named `my-resume.yaml` using the schema and examples above.

### Step 2: Validate Your YAML

Ensure your YAML is properly formatted:
- Use a YAML validator or linter
- Check for proper indentation (use spaces, not tabs)
- Verify all required fields are present

### Step 3: Generate PDF via API

**Using cURL:**

```bash
curl -X POST \
  -F "yaml_file=@my-resume.yaml" \
  http://localhost:3003/process_resume \
  --output my-resume.pdf
```

**Using cURL with JSON:**

```bash
curl -X POST \
  -F "json_file=@my-resume.json" \
  http://localhost:3003/process_resume \
  --output my-resume.pdf
```

**Python Example:**

```python
import requests

# Upload YAML file
with open('my-resume.yaml', 'rb') as f:
    files = {'yaml_file': f}
    response = requests.post('http://localhost:3003/process_resume', files=files)

# Save PDF
with open('my-resume.pdf', 'wb') as f:
    f.write(response.content)

print("PDF generated successfully!")
```

**JavaScript Example:**

```javascript
const FormData = require('form-data');
const fs = require('fs');
const axios = require('axios');

const form = new FormData();
form.append('yaml_file', fs.createReadStream('my-resume.yaml'));

axios.post('http://localhost:3003/process_resume', form, {
  headers: form.getHeaders(),
  responseType: 'arraybuffer'
})
.then(response => {
  fs.writeFileSync('my-resume.pdf', response.data);
  console.log('PDF generated successfully!');
})
.catch(error => {
  console.error('Error generating PDF:', error.message);
});
```

### Step 4: Review Your PDF

Open the generated PDF and verify:
- All information is correctly displayed
- Formatting looks professional
- No text is cut off or misaligned
- Links (LinkedIn) are clickable

## Converting JSON to YAML

If you prefer JSON, the structure is identical:

```json
{
  "name": "Alex Johnson",
  "email": "alex.johnson@email.com",
  "phone": "+1 555 123 4567",
  "location": "Seattle, WA 98101",
  "linkedin": "https://www.linkedin.com/in/alexjohnson/",
  "education": {
    "title": "Master of Science in Computer Science",
    "college": "University of Washington",
    "location": "Seattle, USA",
    "period": "June 2015",
    "gpa": "3.9 / 4.0"
  },
  "roles": [
    {
      "company": "TechCorp",
      "title": "Senior Software Architect",
      "locations": [
        {
          "location": "Seattle, USA",
          "start_date": "Jan 2022",
          "end_date": "Present"
        }
      ],
      "achievements": [
        "Led the redesign of the company's flagship product.",
        "Mentored a team of 10 junior developers."
      ]
    }
  ],
  "skills": [
    "Cloud Architecture",
    "Python",
    "Team Leadership"
  ]
}
```

## Troubleshooting

### Common Errors

| Error Message | Cause | Solution |
|---------------|-------|----------|
| `Missing yaml_file or json_file` | File parameter name incorrect | Use `yaml_file` or `json_file` as the form field name |
| `Template rendering error` | Missing required field | Check that all required fields are present |
| `YAML parse error` | Invalid YAML syntax | Validate YAML syntax, check indentation |
| `PDF conversion failed` | LibreOffice error | Check logs; may be a template issue |

### Tips

1. **Test with sample files first**: Use `document-roles-sample.yaml` as a starting point
2. **Keep backups**: Save versions of your YAML as you make changes
3. **Incremental changes**: If you encounter errors, revert to a working version and make small changes
4. **Character encoding**: Use UTF-8 encoding for your YAML files

## Support

For issues or questions:
- Check existing example files: `document-roles.yaml`, `document-roles-sample.yaml`
- Review CLAUDE.md for technical documentation
- Test the `/test` endpoint to verify service is running

## Version History

- **v1.0** (2025-11-02): Initial specification for roles-based resume format
