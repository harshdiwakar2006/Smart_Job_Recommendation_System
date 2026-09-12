from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from ai.services import generate_resume
from .services import get_candidate_data


@login_required
def generate_resume_view(request):
    """
    Generate an AI resume using the logged-in user's profile.
    """

    try:
        # ---------------------------------------------
        # Get profile information from database
        # ---------------------------------------------

        candidate_data = get_candidate_data(request.user)

        # ---------------------------------------------
        # Optional target job description
        # ---------------------------------------------

        job_description = ""

        if request.method == "POST":
            job_description = request.POST.get(
                "job_description",
                ""
            ).strip()

        # ---------------------------------------------
        # Generate resume using Groq
        # ---------------------------------------------

        generated_resume = generate_resume(
            candidate_data=candidate_data,
            job_description=job_description,
        )

        # ---------------------------------------------
        # Display generated resume
        # ---------------------------------------------

        return render(
            request,
            "resume_preview.html",
            {
                "resume": generated_resume,
                "job_description": job_description,
            },
        )

    except ValueError as error:

        messages.error(
            request,
            str(error),
        )

        return render(
            request,
            "resume_preview.html",
            {
                "resume": None,
            },
        )

    except Exception as error:

        print("Resume generation error:", error)

        messages.error(
            request,
            "Unable to generate the resume right now. "
            "Please check your Groq API configuration and try again.",
        )

        return render(
            request,
            "resume_preview.html",
            {
                "resume": None,
            },
        )