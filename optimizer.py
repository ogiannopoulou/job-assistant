"""Optimizer — learns from outcomes, suggests next best actions, career plans, courses."""

import json
from pathlib import Path
from datetime import date, datetime

DATA_DIR = Path(__file__).parent / "data"


def load_skill_inventory():
    path = DATA_DIR / "skill_inventory.json"
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return {}


def load_projects():
    path = DATA_DIR / "projects_inventory.json"
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return []


def load_applications():
    path = DATA_DIR / "applications.csv"
    if path.exists():
        import csv
        with open(path, encoding="utf-8") as f:
            return list(csv.DictReader(f))
    return []


def suggest_skill_gaps(inv: dict = None) -> list:
    if inv is None:
        inv = load_skill_inventory()
    gaps = []
    for name, data in inv.items():
        projects = data.get("project_count", 0)
        cvs = data.get("cv_count", 0)
        if projects == 0 and cvs > 0:
            gaps.append({
                "skill": name,
                "severity": "low",
                "message": f"'{name}' in CV but no project — add a project to prove it"
            })
    return gaps


def suggest_next_action(applications: list = None, inv: dict = None) -> dict:
    if applications is None:
        applications = load_applications()
    if inv is None:
        inv = load_skill_inventory()

    pending_apps = [a for a in applications if a.get("status") in ("discovered", "preparing")]
    if pending_apps:
        next_up = pending_apps[0]
        return {
            "action": "apply",
            "priority": "high",
            "message": f"Complete application for {next_up['position'][:50]} @ {next_up['company']}",
            "detail": f"Status: {next_up['status']}. Deadline: {next_up.get('deadline', 'N/A')}",
        }

    if not applications:
        return {
            "action": "scan",
            "priority": "high",
            "message": "No applications yet — run a job scan first",
            "detail": "Use 'scan' to find jobs matching your profile",
        }

    gaps = suggest_skill_gaps(inv)
    if gaps:
        top_gap = gaps[0]
        return {
            "action": "build_skill",
            "priority": "medium",
            "message": f"Skill gap: {top_gap['skill']}",
            "detail": top_gap["message"],
        }

    return {
        "action": "scan",
        "priority": "low",
        "message": "Check for new jobs",
        "detail": "Run a fresh scan to find new opportunities",
    }


def analyze_effectiveness(applications: list = None) -> dict:
    if applications is None:
        applications = load_applications()
    if not applications:
        return {"error": "No application data yet"}

    cv_stats = {}
    for a in applications:
        cv = a.get("cv_used", "unknown")
        status = a.get("status", "unknown")
        if cv not in cv_stats:
            cv_stats[cv] = {"total": 0, "interview": 0, "accepted": 0, "rejected": 0}
        cv_stats[cv]["total"] += 1
        if status in ("interview_scheduled", "interviewed"):
            cv_stats[cv]["interview"] += 1
        if status == "accepted":
            cv_stats[cv]["accepted"] += 1
        if status == "rejected":
            cv_stats[cv]["rejected"] += 1

    return {"cv_stats": cv_stats}


def generate_digest() -> str:
    apps = load_applications()
    inv = load_skill_inventory()
    projects = load_projects()

    lines = [
        f"=== Weekly Digest — {date.today().isoformat()} ===",
        "",
        f"Applications: {len(apps)} total",
    ]
    if apps:
        status_counts = {}
        for a in apps:
            s = a.get("status", "?")
            status_counts[s] = status_counts.get(s, 0) + 1
        for s, c in sorted(status_counts.items()):
            lines.append(f"  {s}: {c}")

    lines.extend([
        "",
        f"Projects: {len(projects)} in inventory",
        f"Skills tracked: {len(inv)}",
        "",
    ])

    effect = analyze_effectiveness(apps)
    if "cv_stats" in effect and effect["cv_stats"]:
        lines.append("CV Effectiveness:")
        for cv, stats in sorted(effect["cv_stats"].items(), key=lambda x: -x[1]["total"])[:5]:
            lines.append(f"  {cv}: {stats['total']} apps, {stats['interview']} interviews")

    lines.append("")
    action = suggest_next_action(apps, inv)
    lines.append(f"Next action [{action['priority']}]: {action['message']}")
    lines.append(f"  {action['detail']}")

    return "\n".join(lines)


ITALY_CAREER_PATHS = [
    {
        "title": "Legal-Administrative Officer (Public Administration)",
        "description": "Permanent role in Italian public administration (concorsi pubblici) or EU institutions. Stable, structured, good benefits.",
        "avg_salary_eur": "30k-45k",
        "stress_level": "low-medium",
        "remote_common": "uncommon (mostly in-office)",
        "why_fits": "Your law degree + current Ministry of Justice role is a direct match. Italian concorsi pubblici value legal qualifications highly. EU institutions also hire Italian law graduates.",
        "skill_gaps": ["EU law and institutions", "Digital administration (CAD)", "Public procurement code",
                       "Administrative process optimization", "FOIA and transparency regulations"],
        "courses": [
            ("Preparazione Concorsi Pubblici", "Formazione GO/PA 110 e lode", "self-paced"),
            ("EU Law for Public Administrators", "Coursera / LUISS", "~6 weeks, free audit"),
            ("Digital Transformation in Public Administration", "AgID (free)", "~20h, free"),
            ("Managing Public Contracts", "European Commission (free)", "~10h, free"),
        ],
    },
    {
        "title": "Sales Manager / Account Manager",
        "description": "Manage client accounts, drive sales, and build relationships at companies in Italy or remote EU.",
        "avg_salary_eur": "35k-55k",
        "stress_level": "medium",
        "remote_common": "hybrid (common in EU)",
        "why_fits": "8 years managing sales, exceeding targets, developing client relationships. Your Archegonia experience shows proven results. Legal background is a plus for B2B sales in regulated industries.",
        "skill_gaps": ["CRM software (Salesforce, HubSpot)", "Sales analytics / KPI tracking",
                       "B2B sales methodologies (MEDDIC, Challenger Sale)",
                       "LinkedIn Sales Navigator", "Basic Excel/PowerBI for reporting"],
        "courses": [
            ("Salesforce Administrator Certification", "Salesforce Trailhead (free)", "~40h, free"),
            ("HubSpot Sales Software Certification", "HubSpot Academy (free)", "~4h, free"),
            ("Strategic Sales Management", "Coursera / University of Illinois", "~20h, free audit"),
            ("LinkedIn Sales Navigator Training", "LinkedIn Learning", "~3h, free trial"),
        ],
    },
    {
        "title": "Customer Service / Operations Manager",
        "description": "Lead customer service teams, manage operations, ensure client satisfaction at Italian or EU companies.",
        "avg_salary_eur": "30k-45k",
        "stress_level": "low-medium",
        "remote_common": "common (call centers, support teams)",
        "why_fits": "Your customer-facing sales management + problem-solving + multilingual skills (IT/EN/DE). Many companies in Rome hire for German-speaking customer service roles (luxury, travel, tech).",
        "skill_gaps": ["Zendesk / Freshdesk / Helpdesk software", "Customer support metrics (CSAT, NPS)",
                       "Quality assurance processes", "Workforce management",
                       "Italian privacy law (GDPR for customer data)"],
        "courses": [
            ("Customer Service Excellence", "Coursera / Zendesk (free)", "~6h, free"),
            ("Zendesk Customer Service Certification", "Zendesk (free)", "~8h, free"),
            ("GDPR for Customer Data Management", "European Commission (free)", "~4h, free"),
            ("Managing Customer Service Teams", "LinkedIn Learning", "~5h, free trial"),
        ],
    },
    {
        "title": "Legal Consultant / Paralegal (Law Firms)",
        "description": "Work in law firms as a legal consultant, paralegal, or litigation assistant. Leverage your law degree and courtroom experience.",
        "avg_salary_eur": "28k-40k",
        "stress_level": "medium",
        "remote_common": "rare (mostly in-office)",
        "why_fits": "Master's in Law + current role in a trial office. Direct courtroom and legal procedure experience. Sapienza degree is well-regarded in Italian law firms.",
        "skill_gaps": ["Legal research databases (DeJure, OneLegale)", "Case management software",
                       "Contract drafting best practices", "English legal terminology",
                       "German legal terminology (for international firms)"],
        "courses": [
            ("Legal Research and Writing", "Coursera / University of Michigan (free audit)", "~20h, free"),
            ("Introduction to Italian Civil Procedure", "Altalex Formazione (free)", "~10h, free"),
            ("English for Law", "British Council (free)", "~15h, free"),
            ("Legal Tech and Innovation", "Coursera / LUISS (free audit)", "~10h, free"),
        ],
    },
    {
        "title": "Administrative Coordinator / Office Manager",
        "description": "Coordinate office operations, manage schedules, handle administrative procedures at Italian companies or international organizations.",
        "avg_salary_eur": "28k-38k",
        "stress_level": "low",
        "remote_common": "sometimes hybrid",
        "why_fits": "Strong administrative skills from Ministry role + 8 years of managing orders, suppliers, and client communication. Your legal background is an asset for compliance-heavy admin roles.",
        "skill_gaps": ["Advanced Excel (pivot tables, vlookup)", "SAP / ERP basics",
                       "Project management (Asana, Trello)", "Business correspondence (Italian/English)",
                       "Payroll and HR administration basics"],
        "courses": [
            ("Advanced Excel for Business", "Coursera / Macquarie (free audit)", "~15h, free"),
            ("SAP ERP Fundamentals", "SAP Learning (free)", "~10h, free"),
            ("Project Management Principles", "Google Project Management (Coursera)", "~20h, free audit"),
            ("HR Administration Basics", "Alison (free)", "~4h, free"),
        ],
    },
]

PERSONAL_RECOMMENDATIONS = {
    "long_term": [
        "Prepare for Italian public administration concorsi (competitions) — your law degree makes you eligible for many roles",
        "Get SAP or Salesforce certified — opens doors to both public and private sector administrative roles",
        "Build a professional LinkedIn profile highlighting your legal + sales combined experience",
        "Consider EU institutions (EPSO exams) — your law degree + English + German is a strong combination",
        "Develop a specialization (public procurement, GDPR, labor law) to differentiate from other candidates",
    ],
    "immediate_actions": [
        "Update your CV with your current Ministry of Justice role (2025–present) — it's your strongest credential",
        "Register on the Italian PA recruitment portal (inPA.gov.it) for concorsi alerts",
        "Set up job alerts on LinkedIn for 'funzionario amministrativo', 'sales manager', 'legal officer' in Rome/Lazio",
        "Polish your LinkedIn profile — add your legal role, sales experience, and languages",
        "Consider registering with recruiting agencies in Rome (Adecco, Gi Group, Randstad) for admin/legal roles",
    ],
    "mindset": [
        "Your law degree + 8 years of sales management + current Ministry role is a rare combination — don't undervalue it",
        "Public administration concorsi are competitive but your profile is strong. Apply consistently.",
        "Your English and German are assets, especially in international companies and EU institutions.",
        "It's OK to want a stable, structured job with good work-life balance. That's not settling — it's choosing wisely.",
        "Your experience managing people, targets, and processes in sales is directly transferable to many roles.",
    ],
}


def generate_career_plan() -> str:
    from profile import load_profile
    p = load_profile()
    prefs = p.get("preferences", {})

    lines = [
        "╔══════════════════════════════════════════════════════════════╗",
        "║         YOUR PERSONALIZED CAREER ROADMAP                    ║",
        "╚══════════════════════════════════════════════════════════════╝",
        "",
        f"Based on your profile: {p.get('name', '')}",
        f"Location: {p.get('location', '')} — Remote={prefs.get('remote', False)}, "
        f"WLB={prefs.get('work_life_balance', 3)}/5, Industry={prefs.get('prefer_industry', True)}",
        "",
        "─── Top Career Paths ───",
        "",
    ]

    for i, path in enumerate(ITALY_CAREER_PATHS, 1):
        lines.append(f"{i}. {path['title']}")
        lines.append(f"   💰 {path['avg_salary_eur']} | 😌 {path['stress_level']} stress | "
                     f"🌍 Remote: {path['remote_common']}")
        lines.append(f"   {path['why_fits']}")
        lines.append(f"   Skills to build: {', '.join(path['skill_gaps'][:4])}")
        lines.append("   Recommended courses:")
        for course_name, provider, duration in path['courses'][:3]:
            lines.append(f"     • {course_name} ({provider}, {duration})")
        lines.append("")

    lines.append("─── Recommended Next Steps ───")
    lines.append("")
    for action in PERSONAL_RECOMMENDATIONS["immediate_actions"]:
        lines.append(f"  ☐ {action}")
    lines.append("")

    lines.append("─── Long-Term Strategy ───")
    lines.append("")
    for action in PERSONAL_RECOMMENDATIONS["long_term"]:
        lines.append(f"  → {action}")
    lines.append("")

    lines.append("─── Note from your assistant ───")
    lines.append("")
    for note in PERSONAL_RECOMMENDATIONS["mindset"]:
        lines.append(f"  💬 {note}")

    return "\n".join(lines)


def suggest_courses(target_path: str = None) -> str:
    if target_path:
        for path in ITALY_CAREER_PATHS:
            if target_path.lower() in path["title"].lower():
                lines = [f"Courses for: {path['title']}", ""]
                for course_name, provider, duration in path['courses']:
                    lines.append(f"  • {course_name}")
                    lines.append(f"    {provider} — {duration}")
                return "\n".join(lines)
        return f"No path matching '{target_path}'. Options:\n" + \
               "\n".join(f"  {i+1}. {p['title']}" for i, p in enumerate(ITALY_CAREER_PATHS))

    lines = ["All Recommended Courses (grouped by path):", ""]
    for path in ITALY_CAREER_PATHS:
        lines.append(f"── {path['title']} ──")
        for course_name, provider, duration in path['courses'][:3]:
            lines.append(f"  • {course_name} ({provider}, {duration})")
        lines.append("")
    return "\n".join(lines)


if __name__ == "__main__":
    print(generate_digest())
