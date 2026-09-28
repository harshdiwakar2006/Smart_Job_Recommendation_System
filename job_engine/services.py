import os
import json
import requests
from dotenv import load_dotenv
from groq import Groq

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

    try:
        response = requests.get(
            url,
            headers=headers,
            params=params,
            timeout=30
        )

        response.raise_for_status()

        return response.json()

    except requests.RequestException as e:
        print(f"Error fetching jobs: {e}")
        return []


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

    return {
        "title": title,
        "company": company,
        "description": description,
    }


def chunk_list(items, size):
    for i in range(0, len(items), size):
        yield items[i:i + size]


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
        print("No jobs found.")
        return []

    slimmed_jobs = [slim_job(job) for job in jobs]

    BATCH_SIZE = 8  # tune this down further if you still hit length errors
    all_results = []

    for batch_num, batch in enumerate(chunk_list(slimmed_jobs, BATCH_SIZE), start=1):
        prompt = f"""
You are a job recommendation system.

Candidate skills:
{json.dumps(user_skills)}

Here is a list of jobs:
{json.dumps(batch, indent=2)}

Output ONLY the job listings sorted in descending order by skill matching percentage.
For each job output exactly this format, nothing else:
<percentage>% - <job title> - <company>

No explanations, no headers, no extra text.
Combine all the batches and sort them in descending order.
"""

        try:
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

            result = response.choices[0].message.content
            all_results.append(result)

            #print(result)
            #print(f"\n--- Job Recommendations (batch {batch_num}) ---\n")

        except Exception as e:
            print(f"Groq API error on batch {batch_num}: {e}")

    return all_results
