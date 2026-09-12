def get_candidate_data(user):

    profile = user.profile

    candidate_data = {
        "personal": {
            "first_name": profile.first_name,
            "last_name": profile.last_name,
            "phone": profile.phone,
            "location": profile.location,
            "job_title": profile.job_title,
            "linkedin": profile.linkedin,
            "github": profile.github,
            "portfolio": profile.portfolio,
        },

        "summary": profile.summary,

        "education": [
            {
                "degree": education.degree,
                "institution": education.institution,
                "start_year": education.start_year,
                "end_year": education.end_year,
                "cgpa": education.cgpa,
            }
            for education in profile.educations.all()
        ],

        "skills": [
            skill.name
            for skill in profile.skills.all()
        ],

        "experience": [
            {
                "job_title": experience.job_title,
                "company": experience.company,
                "start_date": (
                    str(experience.start_date)
                    if experience.start_date
                    else None
                ),
                "end_date": (
                    str(experience.end_date)
                    if experience.end_date
                    else None
                ),
                "description": experience.description,
            }
            for experience in profile.experiences.all()
        ],

        "projects": [
            {
                "name": project.name,
                "technologies": project.technologies,
                "description": project.description,
                "github_url": project.github_url,
                "project_url": project.project_url,
            }
            for project in profile.projects.all()
        ],

        "certifications": [
            {
                "name": certification.name,
                "organization": certification.organization,
                "issue_date": (
                    str(certification.issue_date)
                    if certification.issue_date
                    else None
                ),
                "credential_url": certification.credential_url,
            }
            for certification in profile.certifications.all()
        ],

        "achievements": [
            achievement.description
            for achievement in profile.achievements.all()
        ],

        "languages": [
            language.name
            for language in profile.languages.all()
        ],
    }

    return candidate_data