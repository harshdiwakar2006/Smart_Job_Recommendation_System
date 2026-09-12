from django.shortcuts import redirect, render
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from .models import (
    Profile,
    Education,
    Skill,
    Experience,
    Project,
    Certification,
    Achievement,
    Language
)

def registration_view(request):
    if request.method == "POST":
        email = request.POST["email"]
        password = request.POST["password"]
        confirmPassword = request.POST["confirmPassword"]

        if password != confirmPassword:
            messages.error(request, "Passwords do not match")
            return redirect("register")

        if User.objects.filter(username=email).exists():
            messages.error(request, "User already exists")
            return redirect("register")

        myuser = User.objects.create_user(
            username=email,
            email=email,
            password=password
        )

        myuser.save()

        messages.success(request, "You have successfully REGISTERED")

        return redirect("login")

    return render(request, "registration.html")


def login_view(request):
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")

        if not email or not password:
            messages.error(request, "Please enter email and password")
            return render(request, "login.html")

        user = authenticate(
            username=email,
            password=password
        )

        if user is not None:
            login(request, user)
            return redirect("profile")

        messages.error(request, "Invalid email or password")

    return render(request, "login.html")


@login_required
def profile_view(request):

    if request.method == "POST":

        # -------------------------
        # PROFILE
        # -------------------------

        profile, created = Profile.objects.update_or_create(
            user=request.user,
            defaults={
                "first_name": request.POST.get("first_name"),
                "last_name": request.POST.get("last_name"),
                "phone": request.POST.get("phone"),
                "location": request.POST.get("location"),
                "job_title": request.POST.get("job_title"),
                "summary": request.POST.get("summary"),
                "linkedin": request.POST.get("linkedin"),
                "github": request.POST.get("github"),
                "portfolio": request.POST.get("portfolio"),
            }
        )

        # -------------------------
        # EDUCATION
        # -------------------------

        degree = request.POST.get("degree")
        institution = request.POST.get("institution")

        if degree and institution:

            Education.objects.create(
                profile=profile,
                degree=degree,
                institution=institution,
                start_year=request.POST.get("education_start") or None,
                end_year=request.POST.get("education_end") or None,
                cgpa=request.POST.get("cgpa")
            )

        # -------------------------
        # SKILLS
        # -------------------------

        skills = request.POST.get("skills")

        if skills:

            for skill in skills.split(","):

                skill = skill.strip()

                if skill:
                    Skill.objects.create(
                        profile=profile,
                        name=skill
                    )

        # -------------------------
        # EXPERIENCE
        # -------------------------

        experience_title = request.POST.get("experience_title")
        company = request.POST.get("company")

        if experience_title and company:

            Experience.objects.create(
                profile=profile,
                job_title=experience_title,
                company=company,
                description=request.POST.get(
                    "experience_description",
                    ""
                )
            )

        # -------------------------
        # PROJECT
        # -------------------------

        project_name = request.POST.get("project_name")

        if project_name:

            Project.objects.create(
                profile=profile,
                name=project_name,
                technologies=request.POST.get(
                    "project_technologies",
                    ""
                ),
                description=request.POST.get(
                    "project_description",
                    ""
                ),
                github_url=request.POST.get(
                    "github_url",
                    ""
                ),
                project_url=request.POST.get(
                    "project_url",
                    ""
                )
            )

        # -------------------------
        # CERTIFICATION
        # -------------------------

        certificate_name = request.POST.get("certificate_name")

        if certificate_name:

            Certification.objects.create(
                profile=profile,
                name=certificate_name,
                organization=request.POST.get(
                    "certificate_organization",
                    ""
                ),
                credential_url=request.POST.get(
                    "certificate_url",
                    ""
                )
            )

        # -------------------------
        # ACHIEVEMENT
        # -------------------------

        achievements = request.POST.get("achievements")

        if achievements:

            Achievement.objects.create(
                profile=profile,
                description=achievements
            )

        # -------------------------
        # LANGUAGES
        # -------------------------

        languages = request.POST.get("languages")

        if languages:

            for language in languages.split(","):

                language = language.strip()

                if language:

                    Language.objects.create(
                        profile=profile,
                        name=language
                    )

        return redirect("profile")

    return render(request, "profile.html")
