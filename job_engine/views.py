import json
import logging
import re

from django.contrib.auth.decorators import login_required
from accounts.models import Profile
from django.http import HttpResponseBadRequest, StreamingHttpResponse
from django.shortcuts import render

from .services import recommended_jobs

logger = logging.getLogger(__name__)

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
    profile_skills = list(profile.skills.values_list("name", flat=True)) if profile else []
    skills_text = request.GET.get("skills")
    if skills_text is None:
        skills_text = ", ".join(profile_skills)
    skills = [skill.strip() for skill in skills_text.split(",") if skill.strip()]

    return render(
        request,
        "dashboard.html",
        {
            "skills": skills,
            "skills_text": skills_text,
        },
    )


@login_required(login_url="login")
def stream_jobs_view(request):
    skills_text = request.GET.get("skills", "")
    skills = [skill.strip() for skill in skills_text.split(",") if skill.strip()]
    if not skills:
        return HttpResponseBadRequest("At least one skill is required.")

    def events():
        yield "event: status\ndata: {}\n\n"
        result_count = 0
        try:
            for batch in recommended_jobs(skills):
                jobs = parse_results([batch])
                if jobs:
                    result_count += len(jobs)
                    yield (
                        "event: batch\n"
                        f"data: {json.dumps({'jobs': jobs})}\n\n"
                    )
            yield (
                "event: done\n"
                f"data: {json.dumps({'count': result_count})}\n\n"
            )
        except Exception:
            logger.exception("Failed to stream job recommendations.")
            yield (
                "event: error\n"
                f"data: {json.dumps({'message': 'Recommendations could not be loaded. Please try again.'})}\n\n"
            )

    response = StreamingHttpResponse(
        events(),
        content_type="text/event-stream",
    )
    response["Cache-Control"] = "no-cache"
    response["X-Accel-Buffering"] = "no"
    return response