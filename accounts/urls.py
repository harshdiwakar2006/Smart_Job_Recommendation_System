from django.urls import path

from . import views

urlpatterns = [
    path('', views.overview_view, name='overview'),
    path('register', views.registration_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('profile/', views.profile_view, name='profile'),
]