from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from accounts.models import Profile
from .models import Resume


class GenerateResumeViewTests(TestCase):
    @patch("resume.views.generate_resume")
    def test_generated_resume_is_saved_to_users_profile(self, generate_resume):
        user = User.objects.create_user(
            username="candidate@example.com",
            password="test-password",
        )
        profile = Profile.objects.create(
            user=user,
            first_name="Taylor",
            last_name="Candidate",
            job_title="Developer",
            summary="Builds useful software.",
        )
        generated_content = {
            "name": "Taylor Candidate",
            "title": "Developer",
            "contact": {},
            "summary": "Builds useful software.",
            "skills": [],
            "education": [],
            "experience": [],
            "projects": [],
            "certifications": [],
            "achievements": [],
            "languages": [],
        }
        generate_resume.return_value = generated_content
        self.client.force_login(user)

        response = self.client.get(reverse("generate_resume"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["resume"], generated_content)
        saved_resume = Resume.objects.get(profile=profile)
        self.assertEqual(saved_resume.content, generated_content)
