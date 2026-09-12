from django.urls import path
from . import views

urlpatterns = [
    path("generate/", views.generate_resume_view, name="generate_resume"),
]