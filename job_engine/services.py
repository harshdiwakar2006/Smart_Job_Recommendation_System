import json
import os
import re
from urllib.parse import urlsplit

from dotenv import load_dotenv
from groq import Groq
import requests

load_dotenv()


# -----------------------------
# Get jobs from Apify
# -----------------------------
def get_jobs():
    dataset_id = os.getenv("DATASET_ID")
    api_token = os.getenv("API_TOKEN")

    if not dataset_id or not api_token:
        raise ValueError("DATASET_ID or API_TOKEN is missing in .env")

    url = f"https://api.apify.com/v2/datasets/{dataset_id}/items"

    headers = {
        "Authorization": f"Bearer {api_token}"
    }

    params = {
        "format": "json"
    }

    response = requests.get(
        url,
        headers=headers,
        params=params,
        timeout=30
    )

    response.raise_for_status()

    return response.json()


# -----------------------------
# Trim each job down to only what the model needs
# -----------------------------
def slim_job(job, description_limit=1200):
    """
    Apify job records often contain a LOT of extra fields (raw HTML,
    tracking metadata, salary objects, company logos, etc). Sending all
    of that for every job is what blows past the model's token limit.
    Keep only what's useful for skill matching, and cap description length.
    """
    title = job.get("title") or job.get("jobTitle") or job.get("position") or "Unknown title"
    company = job.get("company") or job.get("companyName") or "Unknown company"
    description = (
        job.get("description")
        or job.get("jobDescription")
        or job.get("descriptionText")
        or ""
    )

    # Strip simple HTML tags if present, then cap length
    if "<" in description and ">" in description:
        import re
        description = re.sub(r"<[^>]+>", " ", description)
    description = " ".join(description.split())[:description_limit]
    apply_url = next(
        (
            job.get(field)
            for field in (
                "applyUrl",
                "apply_url",
                "applyLink",
                "apply_link",
                "applicationUrl",
                "application_url",
                "jobUrl",
                "job_url",
                "url",
                "link",
            )
            if isinstance(job.get(field), str) and job.get(field).strip()
        ),
        "",
    )
    try:
        parsed_url = urlsplit(apply_url)
    except ValueError:
        apply_url = ""
    else:
        if parsed_url.scheme.lower() not in {"http", "https"} or not parsed_url.netloc:
            apply_url = ""

    return {
        "title": title,
        "company": company,
        "description": description,
        "apply_url": apply_url,
    }


# -----------------------------
# Groq setup
# -----------------------------
def recommended_jobs(skills):
    groq_api_key = os.getenv("GROQ_API_KEY")
    if not groq_api_key:
        raise ValueError("GROQ_API_KEY is missing in .env")

    client = Groq(api_key=groq_api_key)

    if isinstance(skills, dict):
        skills = skills.get("skills", [])

    if isinstance(skills, str):
        user_skills = skills.split()
    else:
        user_skills = [str(skill) for skill in skills]

    jobs = get_jobs()
    if not jobs:
        return

    slimmed_jobs = [slim_job(job) for job in jobs]

    BATCH_SIZE = 8  # tune this down further if you still hit length errors
    job_id_pattern = re.compile(r"^\s*(\d+)\s*\|\s*(\d+(?:\.\d+)?)\s*%?\s*$")
    for batch_start in range(0, len(slimmed_jobs), BATCH_SIZE):
        batch = slimmed_jobs[batch_start:batch_start + BATCH_SIZE]
        prompt_batch = [
            {
                "job_id": batch_start + index,
                "title": job["title"],
                "company": job["company"],
                "description": job["description"],
            }
            for index, job in enumerate(batch)
        ]
        prompt = f"""
You are a job recommendation system.

Candidate skills:
{json.dumps(user_skills)}

Here is a list of jobs:
{json.dumps(prompt_batch, indent=2)}

Rank the jobs in this batch by skill match, highest first.
Output ONLY each recommended job's id and match percentage in this exact format:
<job_id> | <percentage>%

No explanations, no headers, no extra text.
"""

        response = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[
                {
                    "role": "system",
                    "content": "You are an accurate job matching assistant."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0
        )

        scored_jobs = []
        seen_job_ids = set()
        for line in (response.choices[0].message.content or "").splitlines():
            match = job_id_pattern.match(line)
            if not match:
                continue
            job_id, score = match.groups()
            if job_id in seen_job_ids:
                continue
            local_index = int(job_id) - batch_start
            if local_index < 0 or local_index >= len(batch):
                continue
            seen_job_ids.add(job_id)
            job = batch[local_index]
            scored_jobs.append(
                (
                    float(score),
                    job,
                )
            )

        scored_jobs.sort(key=lambda result: result[0], reverse=True)
        yield "\n".join(
            f"{score:g}% - {job['title']} - {job['company']}"
            + (f" | apply: {job['apply_url']}" if job["apply_url"] else "")
            for score, job in scored_jobs
        )
