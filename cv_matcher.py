"""CV Matcher -- picks the best CV version for a given job description."""

import re
from profile import load_profile


CV_PROFILES = {
    "Demo_User_CV_English": {
        "file": "Demo_User_CV_English.pdf",
        "focus": ["software", "developer", "engineer", "python", "javascript",
                  "full-stack", "backend", "frontend", "cloud", "aws",
                  "docker", "agile", "data", "machine learning", "sql",
                  "react", "node", "django", "flask", "devops", "ci/cd"],
        "description": "English CV — software engineering background",
    },
}

DEFAULT_CV_KEY = "Demo_User_CV_English"


def match_cv(job_title: str, job_description: str = "") -> str:
    text = (job_title + " " + job_description).lower()
    scores = {}
    for key, profile in CV_PROFILES.items():
        score = sum(1 for kw in profile["focus"] if kw.lower() in text)
        scores[key] = score

    if not scores or max(scores.values()) == 0:
        return DEFAULT_CV_KEY

    best = max(scores, key=scores.get)
    return best


def recommend_cv(job_title: str, job_description: str = "") -> dict:
    key = match_cv(job_title, job_description)
    profile = CV_PROFILES[key]
    p = load_profile()
    cv_path = p.get("cv_files", {}).get(key, "")
    return {
        "cv_key": key,
        "cv_filename": profile["file"],
        "cv_path": cv_path,
        "description": profile["description"],
        "match_score": sum(1 for kw in profile["focus"]
                          if kw.lower() in (job_title + " " + job_description).lower()),
    }
