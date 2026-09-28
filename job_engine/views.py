import re
from django.contrib.auth.decorators import login_required
from accounts.models import Profile

from django.shortcuts import render

from .services import recommended_jobs

# Matches lines like: "85% - Python Developer - Acme Corp"
# The title is greedy so titles containing " - " still work;
# the LAST " - " separates title from company.
LINE_RE = re.compile(r"^\s*(\d+(?:\.\d+)?)\s*%\s*-\s*(.+)\s+-\s+(.+?)\s*$")


def parse_results(batches):
    """Turn the list of raw batch strings into one sorted list of dicts."""
    jobs = []
    for batch in batches:
        for line in (batch or "").splitlines():
            match = LINE_RE.match(line)
            if not match:
                continue  # skip blank/unexpected lines
            score, title, company = match.groups()
            jobs.append(
                {
                    "score": float(score),
                    "title": title.strip(),
                    "company": company.strip(),
                }
            )

    # The model only sorts within each batch, so sort everything here.
    jobs.sort(key=lambda j: j["score"], reverse=True)
    return jobs


@login_required(login_url="login")
def dashboard_view(request):
    profile = Profile.objects.filter(user=request.user).first()
    skills = list(profile.skills.values_list("name", flat=True)) if profile else []
    

    jobs = []
    error = None

    if skills:
        try:
            jobs = parse_results(recommended_jobs(skills))
        except Exception as exc:  # missing .env keys, API failure, etc.
            error = str(exc)

    return render(
        request,
        "dashboard.html",
        {
            "jobs": jobs,
            "skills": skills,
            "error": error,
        },
    )