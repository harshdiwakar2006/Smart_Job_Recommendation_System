from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from unittest.mock import patch
from unittest.mock import MagicMock

from .services import recommended_jobs
from .views import parse_results


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

    @patch("job_engine.views.recommended_jobs")
    def test_stream_includes_safe_source_apply_url(self, recommendations):
        recommendations.return_value = iter(
            ["85% - Python Developer - Acme | apply: https://jobs.example/apply/1"]
        )
        response = self.client.get(
            reverse("stream_jobs"),
            {"skills": "Python"},
        )

        body = b"".join(response.streaming_content).decode()

        self.assertIn('"apply_url": "https://jobs.example/apply/1"', body)


class JobApplyUrlTests(TestCase):
    def test_parse_results_only_accepts_http_apply_urls(self):
        jobs = parse_results(
            [
                "85% - Python Developer - Acme | apply: https://jobs.example/apply/1\n"
                "70% - Data Analyst - Example | apply: javascript:alert(1)\n"
                "60% - Designer - Studio | apply: https://[invalid"
            ]
        )

        self.assertEqual(jobs[0]["apply_url"], "https://jobs.example/apply/1")
        self.assertEqual(jobs[1]["apply_url"], "")
        self.assertEqual(jobs[2]["apply_url"], "")

    def test_recommendations_attach_url_from_matching_source_job(self):
        job_source = [
            {
                "title": "Python Developer",
                "company": "Acme",
                "description": "Build Python services.",
                "url": "https://jobs.example/python",
            },
            {
                "title": "Data Analyst",
                "company": "Example",
                "description": "Analyze data.",
                "url": "https://jobs.example/analyst",
            },
        ]
        groq_client = MagicMock()
        groq_client.chat.completions.create.return_value.choices[0].message.content = (
            "1 | 92%\n0 | 85%"
        )

        with (
            patch.dict("os.environ", {"GROQ_API_KEY": "test-key"}),
            patch("job_engine.services.get_jobs", return_value=job_source),
            patch("job_engine.services.Groq", return_value=groq_client),
        ):
            recommendations = list(recommended_jobs(["Python"]))

        self.assertEqual(
            recommendations,
            [
                "92% - Data Analyst - Example | apply: https://jobs.example/analyst\n"
                "85% - Python Developer - Acme | apply: https://jobs.example/python"
            ],
        )
