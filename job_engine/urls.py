from django.urls import path
from . import views

urlpatterns = [
    path("jobs/", views.dashboard_view, name="dashboard"),
]