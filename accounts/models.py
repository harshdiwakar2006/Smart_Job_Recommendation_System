from django.db import models
from django.contrib.auth.models import User


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)

    phone = models.CharField(max_length=20, blank=True)
    location = models.CharField(max_length=200, blank=True)

    job_title = models.CharField(max_length=200)
    summary = models.TextField()

    linkedin = models.URLField(blank=True)
    github = models.URLField(blank=True)
    portfolio = models.URLField(blank=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class Education(models.Model):
    profile = models.ForeignKey(
        Profile,
        on_delete=models.CASCADE,
        related_name="educations"
    )

    degree = models.CharField(max_length=200)
    institution = models.CharField(max_length=200)

    start_year = models.IntegerField(null=True, blank=True)
    end_year = models.IntegerField(null=True, blank=True)

    cgpa = models.CharField(max_length=20, blank=True)

    def __str__(self):
        return self.degree


class Skill(models.Model):
    profile = models.ForeignKey(
        Profile,
        on_delete=models.CASCADE,
        related_name="skills"
    )

    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Experience(models.Model):
    profile = models.ForeignKey(
        Profile,
        on_delete=models.CASCADE,
        related_name="experiences"
    )

    job_title = models.CharField(max_length=200)
    company = models.CharField(max_length=200)

    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)

    description = models.TextField(blank=True)

    def __str__(self):
        return f"{self.job_title} - {self.company}"


class Project(models.Model):
    profile = models.ForeignKey(
        Profile,
        on_delete=models.CASCADE,
        related_name="projects"
    )

    name = models.CharField(max_length=200)
    technologies = models.CharField(max_length=500)

    description = models.TextField()

    github_url = models.URLField(blank=True)
    project_url = models.URLField(blank=True)

    def __str__(self):
        return self.name


class Certification(models.Model):
    profile = models.ForeignKey(
        Profile,
        on_delete=models.CASCADE,
        related_name="certifications"
    )

    name = models.CharField(max_length=200)
    organization = models.CharField(max_length=200)

    issue_date = models.DateField(null=True, blank=True)

    credential_url = models.URLField(blank=True)

    def __str__(self):
        return self.name


class Achievement(models.Model):
    profile = models.ForeignKey(
        Profile,
        on_delete=models.CASCADE,
        related_name="achievements"
    )

    description = models.TextField()

    def __str__(self):
        return self.description[:50]


class Language(models.Model):
    profile = models.ForeignKey(
        Profile,
        on_delete=models.CASCADE,
        related_name="languages"
    )

    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name