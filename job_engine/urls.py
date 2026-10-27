from django.urls import path
from . import views

urlpatterns = [
    path("jobs/stream/", views.stream_jobs_view, name="stream_jobs"),
    path("jobs/", views.dashboard_view, name="dashboard"),
]