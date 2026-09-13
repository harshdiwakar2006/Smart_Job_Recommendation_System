import json

from django.conf import settings
from groq import Groq

from .prompts import RESUME_SYSTEM_PROMPT


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
}


def clean_value(value):
    if value is None:
        return ""

    value = str(value).strip()

    if value.lower() in INVALID_VALUES:
        return ""

    return value


def clean_list(values):
    if not values:
        return []

    if isinstance(values, str):
        values = values.split(",")

    result = []

    for value in values:
        value = clean_value(value)

        if value:
            result.append(value)

    return result


def clean_candidate_data(candidate_data):

    personal = candidate_data.get("personal", {})

    cleaned = {
        "personal": {
            "first_name": clean_value(
                personal.get("first_name")
            ),
            "last_name": clean_value(
                personal.get("last_name")
            ),
            "email": clean_value(
                personal.get("email")
            ),
            "phone": clean_value(
                personal.get("phone")
            ),
            "location": clean_value(
                personal.get("location")
            ),
            "job_title": clean_value(
                personal.get("job_title")
            ),
            "linkedin": clean_value(
                personal.get("linkedin")
            ),
            "github": clean_value(
                personal.get("github")
            ),
            "portfolio": clean_value(
                personal.get("portfolio")
            ),
        },

        "summary": clean_value(
            candidate_data.get("summary")
        ),

        "skills": clean_list(
            candidate_data.get("skills", [])
        ),

        "education": [],

        "experience": [],

        "projects": [],

        "certifications": [],

        "achievements": clean_list(
            candidate_data.get("achievements", [])
        ),

        "languages": clean_list(
            candidate_data.get("languages", [])
        ),
    }

    # Education
    for item in candidate_data.get("education", []):

        degree = clean_value(item.get("degree"))
        institution = clean_value(item.get("institution"))

        if not degree and not institution:
            continue

        cleaned["education"].append({
            "degree": degree,
            "institution": institution,
            "start_year": item.get("start_year"),
            "end_year": item.get("end_year"),
            "cgpa": clean_value(item.get("cgpa")),
        })

    # Experience
    for item in candidate_data.get("experience", []):

        job_title = clean_value(
            item.get("job_title")
        )

        company = clean_value(
            item.get("company")
        )

        description = clean_value(
            item.get("description")
        )

        if not job_title and not company and not description:
            continue

        cleaned["experience"].append({
            "job_title": job_title,
            "company": company,
            "start_date": clean_value(
                item.get("start_date")
            ),
            "end_date": clean_value(
                item.get("end_date")
            ),
            "description": description,
        })

    # Projects
    for item in candidate_data.get("projects", []):

        name = clean_value(
            item.get("name")
        )

        description = clean_value(
            item.get("description")
        )

        technologies = item.get(
            "technologies",
            ""
        )

        if isinstance(technologies, list):

            technologies = clean_list(
                technologies
            )

        else:

            technologies = clean_value(
                technologies
            )

            if technologies:

                technologies = [
                    x.strip()
                    for x in technologies.split(",")
                    if x.strip()
                    and x.strip().lower()
                    not in INVALID_VALUES
                ]

            else:
                technologies = []

        github_url = clean_value(
            item.get("github_url")
        )

        project_url = clean_value(
            item.get("project_url")
        )

        if not name and not description and not technologies:
            continue

        cleaned["projects"].append({
            "name": name,
            "technologies": technologies,
            "description": description,
            "github_url": github_url,
            "project_url": project_url,
        })

    # Certifications
    for item in candidate_data.get(
        "certifications",
        []
    ):

        name = clean_value(
            item.get("name")
        )

        organization = clean_value(
            item.get("organization")
        )

        if not name and not organization:
            continue

        cleaned["certifications"].append({
            "name": name,
            "organization": organization,
            "issue_date": clean_value(
                item.get("issue_date")
            ),
            "credential_url": clean_value(
                item.get("credential_url")
            ),
        })

    return cleaned


def normalize_resume(resume):

    """
    Make sure the AI response always has the
    structure expected by the Django template.
    """

    if not isinstance(resume, dict):
        raise ValueError(
            "Groq returned an invalid resume format."
        )

    contact = resume.get(
        "contact",
        {}
    )

    if not isinstance(contact, dict):
        contact = {}

    result = {
        "name": clean_value(
            resume.get("name")
        ),

        "title": clean_value(
            resume.get("title")
        ),

        "contact": {
            "email": clean_value(
                contact.get("email")
            ),
            "phone": clean_value(
                contact.get("phone")
            ),
            "location": clean_value(
                contact.get("location")
            ),
            "linkedin": clean_value(
                contact.get("linkedin")
            ),
            "github": clean_value(
                contact.get("github")
            ),
            "portfolio": clean_value(
                contact.get("portfolio")
            ),
        },

        "summary": clean_value(
            resume.get("summary")
        ),

        "skills": clean_list(
            resume.get("skills", [])
        ),

        "education": (
            resume.get("education", [])
            if isinstance(
                resume.get("education", []),
                list
            )
            else []
        ),

        "experience": (
            resume.get("experience", [])
            if isinstance(
                resume.get("experience", []),
                list
            )
            else []
        ),

        "projects": (
            resume.get("projects", [])
            if isinstance(
                resume.get("projects", []),
                list
            )
            else []
        ),

        "certifications": (
            resume.get("certifications", [])
            if isinstance(
                resume.get("certifications", []),
                list
            )
            else []
        ),

        "achievements": clean_list(
            resume.get("achievements", [])
        ),

        "languages": clean_list(
            resume.get("languages", [])
        ),
    }

    return result


def generate_resume(
    candidate_data,
    job_description=""
):

    if not settings.GROQ_API_KEY:

        raise ValueError(
            "GROQ_API_KEY is missing."
        )

    candidate_data = clean_candidate_data(
        candidate_data
    )

    client = Groq(
        api_key=settings.GROQ_API_KEY
    )

    candidate_json = json.dumps(
        candidate_data,
        indent=2,
        ensure_ascii=False
    )

    target_job = (
        job_description.strip()
        if job_description
        else "No target job description provided."
    )

    user_prompt = f"""
Create a professional ATS-friendly resume.

Use ONLY the candidate information below.

CANDIDATE INFORMATION:
{candidate_json}

TARGET JOB:
{target_job}

Return ONLY valid JSON.

The JSON must have exactly these top-level fields:

name
title
contact
summary
skills
education
experience
projects
certifications
achievements
languages

Rules:

- Do not invent information.
- Do not create fake experience.
- Do not create fake projects.
- Do not create fake certifications.
- Do not create fake skills.
- Do not use placeholder values such as "none", "N/A", or "null".
- If information is missing, use an empty string or empty array.
- Keep skills as complete words.
- Keep technologies as complete technology names.
- Never split a word into individual characters.
- Improve grammar and professional wording.
- Keep the resume concise.
- Do not return Markdown.
- Do not return HTML.
- Do not explain anything.
- Return JSON only.
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
            "type": "json_object"
        },

        temperature=0.2,
    )

    content = response.choices[0].message.content

    if not content:
        raise ValueError(
            "Groq returned an empty response."
        )

    try:

        resume = json.loads(content)

    except json.JSONDecodeError as error:

        print(
            "Invalid Groq JSON:",
            content
        )

        raise ValueError(
            f"Groq returned invalid JSON: {error}"
        )

    return normalize_resume(resume)