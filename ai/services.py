import json

from django.conf import settings
from groq import Groq

from .prompts import RESUME_SYSTEM_PROMPT


# ---------------------------------------------------------
# Values that should NOT appear as real resume information
# ---------------------------------------------------------

INVALID_VALUES = {
    "",
    "none",
    "n/a",
    "na",
    "null",
    "nil",
    "-",
    "--",
    "not available",
    "not applicable",
    "no experience",
    "no projects",
    "no certifications",
    "no achievements",
}


def clean_value(value):
    """
    Convert a value into a clean string.

    Placeholder values such as 'none' or 'n/a' become empty strings.
    """

    if value is None:
        return ""

    value = str(value).strip()

    if value.lower() in INVALID_VALUES:
        return ""

    return value


def clean_list(values):
    """
    Clean a list of values.

    Example:

    ["Java", "Python", "none", ""]
    
    becomes:

    ["Java", "Python"]
    """

    if not values:
        return []

    cleaned = []

    for value in values:
        value = clean_value(value)

        if value:
            cleaned.append(value)

    return cleaned


def clean_candidate_data(candidate_data):
    """
    Clean all candidate information before sending it to Groq.
    """

    personal = candidate_data.get("personal", {})

    cleaned = {
        "personal": {
            "first_name": clean_value(personal.get("first_name")),
            "last_name": clean_value(personal.get("last_name")),
            "email": clean_value(personal.get("email")),
            "phone": clean_value(personal.get("phone")),
            "location": clean_value(personal.get("location")),
            "job_title": clean_value(personal.get("job_title")),
            "linkedin": clean_value(personal.get("linkedin")),
            "github": clean_value(personal.get("github")),
            "portfolio": clean_value(personal.get("portfolio")),
        },

        "summary": clean_value(candidate_data.get("summary")),

        "education": [],

        "skills": clean_list(candidate_data.get("skills", [])),

        "experience": [],

        "projects": [],

        "certifications": [],

        "achievements": clean_list(candidate_data.get("achievements", [])),

        "languages": clean_list(candidate_data.get("languages", [])),
    }

    # -----------------------------------------------------
    # Education
    # -----------------------------------------------------

    for education in candidate_data.get("education", []):

        degree = clean_value(education.get("degree"))
        institution = clean_value(education.get("institution"))

        # An education record without meaningful information
        # should not be sent to the AI.
        if not degree and not institution:
            continue

        cleaned["education"].append({
            "degree": degree,
            "institution": institution,
            "start_year": education.get("start_year"),
            "end_year": education.get("end_year"),
            "cgpa": clean_value(education.get("cgpa")),
        })

    # -----------------------------------------------------
    # Experience
    # -----------------------------------------------------

    for experience in candidate_data.get("experience", []):

        job_title = clean_value(experience.get("job_title"))
        company = clean_value(experience.get("company"))
        description = clean_value(experience.get("description"))

        # Do not allow completely empty experience records.
        if not job_title and not company and not description:
            continue

        # Ignore placeholder records.
        if (
            job_title.lower() in INVALID_VALUES
            or company.lower() in INVALID_VALUES
        ):
            continue

        cleaned["experience"].append({
            "job_title": job_title,
            "company": company,
            "start_date": clean_value(experience.get("start_date")),
            "end_date": clean_value(experience.get("end_date")),
            "description": description,
        })

    # -----------------------------------------------------
    # Projects
    # -----------------------------------------------------

    for project in candidate_data.get("projects", []):

        name = clean_value(project.get("name"))
        technologies = project.get("technologies", "")
        description = clean_value(project.get("description"))
        github_url = clean_value(project.get("github_url"))
        project_url = clean_value(project.get("project_url"))

        # -------------------------------------------------
        # Technologies
        # -------------------------------------------------

        if isinstance(technologies, list):
            cleaned_technologies = clean_list(technologies)

        else:
            technologies = clean_value(technologies)

            if not technologies:
                cleaned_technologies = []

            elif technologies.lower() in INVALID_VALUES:
                cleaned_technologies = []

            else:
                # IMPORTANT:
                # Split by comma ONLY.
                #
                # Never do:
                # list("none")
                #
                # because that creates:
                # ["n", "o", "n", "e"]
                cleaned_technologies = [
                    item.strip()
                    for item in technologies.split(",")
                    if item.strip()
                    and item.strip().lower() not in INVALID_VALUES
                ]

        # Completely empty project -> ignore it.
        if not name and not description and not cleaned_technologies:
            continue

        # Ignore placeholder project names.
        if name.lower() in INVALID_VALUES:
            continue

        cleaned["projects"].append({
            "name": name,
            "technologies": cleaned_technologies,
            "description": description,
            "github_url": github_url,
            "project_url": project_url,
        })

    # -----------------------------------------------------
    # Certifications
    # -----------------------------------------------------

    for certification in candidate_data.get("certifications", []):

        name = clean_value(certification.get("name"))
        organization = clean_value(certification.get("organization"))
        issue_date = clean_value(certification.get("issue_date"))
        credential_url = clean_value(certification.get("credential_url"))

        if not name and not organization:
            continue

        if name.lower() in INVALID_VALUES:
            continue

        cleaned["certifications"].append({
            "name": name,
            "organization": organization,
            "issue_date": issue_date,
            "credential_url": credential_url,
        })

    return cleaned


# ---------------------------------------------------------
# Groq JSON Schema
# ---------------------------------------------------------

RESUME_SCHEMA = {
    "type": "object",
    "properties": {

        "name": {
            "type": "string"
        },

        "title": {
            "type": "string"
        },

        "contact": {
            "type": "object",
            "properties": {
                "email": {
                    "type": "string"
                },
                "phone": {
                    "type": "string"
                },
                "location": {
                    "type": "string"
                },
                "linkedin": {
                    "type": "string"
                },
                "github": {
                    "type": "string"
                },
                "portfolio": {
                    "type": "string"
                },
            },
            "required": [
                "email",
                "phone",
                "location",
                "linkedin",
                "github",
                "portfolio",
            ],
            "additionalProperties": False,
        },

        "summary": {
            "type": "string"
        },

        "skills": {
            "type": "array",
            "items": {
                "type": "string"
            }
        },

        "education": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "degree": {
                        "type": "string"
                    },
                    "institution": {
                        "type": "string"
                    },
                    "start_year": {
                        "type": ["integer", "null"]
                    },
                    "end_year": {
                        "type": ["integer", "null"]
                    },
                    "cgpa": {
                        "type": "string"
                    },
                },
                "required": [
                    "degree",
                    "institution",
                    "start_year",
                    "end_year",
                    "cgpa",
                ],
                "additionalProperties": False,
            },
        },

        "experience": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "job_title": {
                        "type": "string"
                    },
                    "company": {
                        "type": "string"
                    },
                    "start_date": {
                        "type": "string"
                    },
                    "end_date": {
                        "type": "string"
                    },
                    "description": {
                        "type": "string"
                    },
                },
                "required": [
                    "job_title",
                    "company",
                    "start_date",
                    "end_date",
                    "description",
                ],
                "additionalProperties": False,
            },
        },

        "projects": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string"
                    },
                    "technologies": {
                        "type": "array",
                        "items": {
                            "type": "string"
                        }
                    },
                    "description": {
                        "type": "string"
                    },
                    "github_url": {
                        "type": "string"
                    },
                    "project_url": {
                        "type": "string"
                    },
                },
                "required": [
                    "name",
                    "technologies",
                    "description",
                    "github_url",
                    "project_url",
                ],
                "additionalProperties": False,
            },
        },

        "certifications": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string"
                    },
                    "organization": {
                        "type": "string"
                    },
                    "issue_date": {
                        "type": "string"
                    },
                    "credential_url": {
                        "type": "string"
                    },
                },
                "required": [
                    "name",
                    "organization",
                    "issue_date",
                    "credential_url",
                ],
                "additionalProperties": False,
            },
        },

        "achievements": {
            "type": "array",
            "items": {
                "type": "string"
            }
        },

        "languages": {
            "type": "array",
            "items": {
                "type": "string"
            }
        },
    },

    "required": [
        "name",
        "title",
        "contact",
        "summary",
        "skills",
        "education",
        "experience",
        "projects",
        "certifications",
        "achievements",
        "languages",
    ],

    "additionalProperties": False,
}


# ---------------------------------------------------------
# Generate Resume
# ---------------------------------------------------------

def generate_resume(candidate_data, job_description=""):
    """
    Send candidate data to Groq and return structured resume JSON.
    """

    if not settings.GROQ_API_KEY:
        raise ValueError(
            "GROQ_API_KEY is missing. Add it to your .env file."
        )

    # Clean the data BEFORE sending it to the AI.
    candidate_data = clean_candidate_data(candidate_data)

    client = Groq(
        api_key=settings.GROQ_API_KEY
    )

    user_prompt = f"""
Create a professional ATS-friendly resume from the candidate information below.

CANDIDATE DATA:
{json.dumps(candidate_data, indent=2, ensure_ascii=False)}

TARGET JOB DESCRIPTION:
{job_description.strip() if job_description else "No specific target job provided."}

Follow these rules:

- Use ONLY candidate information.
- Do not invent information.
- Rewrite wording professionally.
- Do not create fake experience.
- Do not create fake projects.
- Do not create fake certifications.
- Do not create fake achievements.
- Empty candidate sections MUST remain empty arrays.
- Do not output Markdown.
- Do not output HTML.
- Return only the JSON schema requested by the application.
"""

    response = client.chat.completions.create(
        model="openai/gpt-oss-20b",

        messages=[
            {
                "role": "system",
                "content": RESUME_SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": user_prompt,
            },
        ],

        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "professional_resume",
                "strict": True,
                "schema": RESUME_SCHEMA,
            },
        },

        temperature=0.2,
    )

    content = response.choices[0].message.content

    if not content:
        raise ValueError("Groq returned an empty response.")

    try:
        resume_data = json.loads(content)
    except json.JSONDecodeError as error:
        raise ValueError(
            f"Groq returned invalid JSON: {error}"
        )

    return resume_data