from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from unittest.mock import patch


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

    @patch("job_engine.views.recommended_jobs")
    def test_dashboard_renders_without_waiting_for_recommendations(self, recommendations):
        user = User.objects.create_user(
            username="quick@example.com",
            password="test-password",
        )
        self.client.force_login(user)

        response = self.client.get(reverse("dashboard"), {"skills": "Python"})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Finding matching jobs...")
        recommendations.assert_not_called()


class StreamingRecommendationsTests(TestCase):
    def setUp(self):
        user = User.objects.create_user(
            username="stream@example.com",
            password="test-password",
        )
        self.client.force_login(user)

    @patch("job_engine.views.recommended_jobs")
    def test_stream_sends_each_completed_batch_as_its_own_event(self, recommendations):
        produced_batches = []

        def batch_results(skills):
            self.assertEqual(skills, ["Python", "Django"])
            produced_batches.append("first")
            yield "75% - Python Developer - Acme"
            produced_batches.append("second")
            yield "90% - Django Developer - Example"

        recommendations.side_effect = batch_results
        response = self.client.get(
            reverse("stream_jobs"),
            {"skills": "Python, Django"},
        )
        chunks = response.streaming_content

        self.assertIn("event: status", next(chunks).decode())
        self.assertEqual(produced_batches, [])

        first_batch = next(chunks).decode()
        self.assertIn("Python Developer", first_batch)
        self.assertEqual(produced_batches, ["first"])

        remaining = b"".join(chunks).decode()
        self.assertIn("Django Developer", remaining)
        self.assertIn("event: done", remaining)
        self.assertEqual(produced_batches, ["first", "second"])

    @patch("job_engine.views.recommended_jobs")
    def test_stream_reports_failure_after_preserving_completed_batches(self, recommendations):
        def failing_results(skills):
            self.assertEqual(skills, ["Python"])
            yield "85% - Python Developer - Acme"
            raise RuntimeError("upstream failure")

        recommendations.side_effect = failing_results
        response = self.client.get(
            reverse("stream_jobs"),
            {"skills": "Python"},
        )

        with self.assertLogs("job_engine.views", level="ERROR"):
            body = b"".join(response.streaming_content).decode()

        self.assertIn("Python Developer", body)
        self.assertIn("event: error", body)
        self.assertNotIn("upstream failure", body)
