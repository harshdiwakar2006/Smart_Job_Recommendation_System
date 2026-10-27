from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse


class DashboardNavigationTests(TestCase):
    def test_dashboard_displays_profile_and_resume_navigation(self):
        user = User.objects.create_user(
            username="candidate@example.com",
            password="test-password",
        )
        self.client.force_login(user)

        response = self.client.get(reverse("dashboard"))

        self.assertContains(response, "Edit Profile")
        self.assertContains(response, "View Resume")
        self.assertContains(response, reverse("profile"))
        self.assertContains(response, reverse("generate_resume"))
