"""Skills Analyzer -- maps your profile skills to job requirements, shows gaps & strengths."""

import re
from profile import load_profile


ALL_SKILLS = {
    "legal_administrative": ["Legal procedures", "Administrative law", "Certification services",
                              "Public records", "Document analysis", "Trial office operations",
                              "Compliance", "GDPR", "Contract management", "Public procurement"],
    "sales_customer_service": ["Sales management", "CRM", "Negotiation", "Customer loyalty",
                                "After-sales support", "Supplier relations", "Order management",
                                "Sales targets", "Account management", "Customer service"],
    "it_tools": ["Microsoft Office", "Excel", "Word", "PowerPoint", "Windows", "Mac OS",
                  "Electronic invoicing", "SAP", "Salesforce", "Email management"],
    "soft_skills": ["Communication", "Problem-solving", "Organization", "Time management",
                    "Multitasking", "Teamwork", "Leadership", "Presentation", "Planning"],
    "languages": ["Italian (native)", "English (B2)", "German (B2)"],
    "sectors": ["Public Administration", "Justice", "Legal", "Sales", "Customer Service",
                "Insurance", "Banking", "Tourism", "Export", "HR", "Compliance"],
}

CATEGORY_KEYWORDS = {
    "legal_administrative": {
        "keywords": ["legal", "administrative", "law", "justice", "ministry", "court",
                     "funzionario", "amministrativo", "cancelliere", "compliance",
                     "concorso", "pubblica amministrazione", "normativa",
                     "giuridico", "paralegal", "procurement", "appalti",
                     "gdpr", "privacy", "antiriciclaggio", "tribunale"],
        "min_score": 1,
    },
    "sales_account_management": {
        "keywords": ["sales", "account manager", "sales manager", "customer service",
                     "commerciale", "vendite", "business development", "key account",
                     "customer success", "after-sales", "clienti", "negoziazione",
                     "sales representative", "sales assistant", "retail",
                     "export", "trade", "agente", "rappresentante"],
        "min_score": 1,
    },
    "administrative_coordination": {
        "keywords": ["administrative", "coordinatore", "coordination", "office manager",
                     "back office", "segreteria", "impiegato", "amministrativo",
                     "organizzazione", "logistics", "operations", "supporto",
                     "customer service", "front office", "helpdesk"],
        "min_score": 1,
    },
    "public_administration": {
        "keywords": ["public administration", "pubblica amministrazione", "concorso",
                     "civil servant", "ministero", "ente pubblico", "comune",
                     "regione", "stato", "funzionario", "dirigente",
                     "pubblico impiego", "tempo indeterminato"],
        "min_score": 1,
    },
    "human_resources": {
        "keywords": ["hr", "human resources", "recruitment", "risorse umane",
                     "personnel", "staffing", "talent acquisition", "onboarding",
                     "payroll", "formazione", "selezione del personale"],
        "min_score": 1,
    },
}


def analyze_job_fit(job_title: str, job_description: str = "") -> dict:
    text = (job_title + " " + job_description).lower()

    category_scores = {}
    for cat, info in CATEGORY_KEYWORDS.items():
        score = sum(1 for kw in info["keywords"] if kw in text)
        category_scores[cat] = {
            "score": score,
            "threshold": info["min_score"],
            "match": score >= info["min_score"],
        }

    matched_skills = {"legal_administrative": [], "sales_customer_service": [],
                      "it_tools": [], "soft_skills": [], "sectors": []}
    for category, skills in ALL_SKILLS.items():
        for skill in skills:
            if skill.lower() in text:
                matched_skills[category].append(skill)

    matched_cats = [cat for cat, info in category_scores.items() if info["match"]]
    best_cat = max(category_scores, key=lambda c: category_scores[c]["score"]) if category_scores else None
    best_score = category_scores[best_cat]["score"] if best_cat else 0

    total_matched = sum(1 for c in category_scores.values() if c["match"])
    if best_score >= 3:
        fit_label = "strong"
    elif best_score >= 2:
        fit_label = "moderate"
    elif best_score >= 1:
        fit_label = "weak"
    else:
        fit_label = "unlikely"

    return {
        "best_category": best_cat,
        "fit_label": fit_label,
        "best_score": best_score,
        "category_scores": category_scores,
        "matched_skills": matched_skills,
        "matched_categories": matched_cats,
        "total_skill_matches": sum(len(v) for v in matched_skills.values()),
    }


def suggest_cv_and_tips(job_title: str, job_description: str = "") -> dict:
    from cv_matcher import recommend_cv

    analysis = analyze_job_fit(job_title, job_description)
    cv_rec = recommend_cv(job_title, job_description)

    tips = []
    best = analysis["best_category"]
    if best == "legal_administrative":
        tips = ["Highlight your Master's in Law from Sapienza",
                "Emphasize your experience at the Ministry of Justice - Court of Viterbo",
                "Mention certification services and public records expertise",
                "Reference your document analysis and trial office management skills"]
    elif best == "sales_account_management":
        tips = ["Lead with 8 years as Sales and Customer Service Manager at Archegonia Flowers",
                "Highlight sales targets achievement and customer loyalty",
                "Emphasize supplier relations and order management experience"]
    elif best == "administrative_coordination":
        tips = ["Showcase your organizational and time management skills",
                "Highlight your Microsoft Office proficiency",
                "Emphasize your problem-solving and multitasking abilities"]
    elif best == "public_administration":
        tips = ["Lead with your current role at Ministry of Justice",
                "Highlight your law degree and administrative experience",
                "Emphasize knowledge of legal procedures and public records"]
    elif best == "human_resources":
        tips = ["Highlight your sales management experience (people management)",
                "Emphasize communication and negotiation skills",
                "Reference your problem-solving and organizational abilities"]
    else:
        tips = ["Highlight your law degree from Sapienza",
                "Emphasize your combined legal + sales experience",
                "Showcase your multilingual abilities (Italian, English, German)"]

    return {
        "cv_key": cv_rec["cv_key"],
        "cv_path": cv_rec["cv_path"],
        "analysis": analysis,
        "tips": tips,
    }
