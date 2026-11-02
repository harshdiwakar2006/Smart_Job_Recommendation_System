from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from ai.services import generate_resume
from .services import get_candidate_data
from .models import Resume


@login_required
def generate_resume_view(request):

    try:
        profile = request.user.profile
        resume_record = (
            Resume.objects.filter(profile=profile)
            .order_by("-updated_at", "-pk")
            .first()
        )

        if resume_record is None:
            candidate_data = get_candidate_data(request.user)
            generated_resume = generate_resume(
                candidate_data=candidate_data,
                job_description="",
            )
            resume_record = Resume.objects.create(
                profile=profile,
                content=generated_resume,
            )
            resume_record.refresh_from_db(fields=("content",))

        return render(
            request,
            "resume_preview.html",
            {
                "resume": resume_record.content,
            },
        )

    except Exception as error:

        # IMPORTANT:
        # Show the REAL error in terminal
        print("\n====================================")
        print("RESUME GENERATION ERROR")
        print("====================================")
        print(type(error).__name__)
        print(str(error))
        print("====================================\n")

        messages.error(
            request,
            f"Resume generation failed: {str(error)}",
        )

        return render(
            request,
            "resume_preview.html",
            {
                "resume": None,
            },
        )