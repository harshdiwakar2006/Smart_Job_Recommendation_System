from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Profile


class LoginViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="candidate@example.com",
            email="candidate@example.com",
            password="test-password",
        )

    def test_login_redirects_to_profile_when_profile_is_missing(self):
        response = self.client.post(
            reverse("login"),
            {"email": self.user.email, "password": "test-password"},
        )

        self.assertRedirects(
            response,
            reverse("profile"),
            fetch_redirect_response=False,
        )

    def test_login_redirects_to_dashboard_when_profile_exists(self):
        Profile.objects.create(
            user=self.user,
            first_name="Taylor",
            last_name="Candidate",
            job_title="Developer",
            summary="Builds useful software.",
        )

        response = self.client.post(
            reverse("login"),
            {"email": self.user.email, "password": "test-password"},
        )

        self.assertRedirects(
            response,
            reverse("dashboard"),
            fetch_redirect_response=False,
        )


class ProfileViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="candidate@example.com",
            email="candidate@example.com",
            password="test-password",
        )
        self.client.force_login(self.user)

    def test_save_profile_persists_profile_data_and_redirects_to_dashboard(self):
        response = self.client.post(
            reverse("profile"),
            {
                "first_name": "Taylor",
                "last_name": "Candidate",
                "email": "candidate@example.com",
                "phone": "555-0100",
                "location": "Remote",
                "job_title": "Developer",
                "summary": "Builds useful software.",
                "linkedin": "",
                "github": "",
                "portfolio": "",
                "degree": "",
                "institution": "",
                "skills": "Django, Python",
                "experience_title": "",
                "company": "",
                "project_name": "",
                "certificate_name": "",
                "achievements": "",
                "languages": "",
            },
        )

        profile = Profile.objects.get(user=self.user)
        self.assertRedirects(
            response,
            reverse("dashboard"),
            fetch_redirect_response=False,
        )
        self.assertEqual(profile.first_name, "Taylor")
        self.assertEqual(profile.last_name, "Candidate")
        self.assertEqual(profile.job_title, "Developer")
        self.assertEqual(
            set(profile.skills.values_list("name", flat=True)),
            {"Django", "Python"},
        )
