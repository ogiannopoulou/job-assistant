"""Role Suggester — maps your skills to unconventional roles you might not have considered."""

from profile import load_profile, save_profile

UNCONVENTIONAL_ROLES = [
    {
        "title": "Concorsi Pubblici Specialist (Public Administration)",
        "sector": "Public Administration / Government",
        "description": "Prepare and apply for Italian public competitions (concorsi). Roles include funzionario amministrativo, istruttore direttivo, dirigente.",
        "avg_salary_eur": "30k-55k",
        "remote": "in-office (most PA roles)",
        "stress": "low-medium",
        "why_match": "Your law degree is the most common requirement for PA concorsi. Your current Ministry role shows you already operate in this environment. Italian PA values seniority + legal background.",
        "skill_gaps": ["Concorso preparation strategy", "Administrative law deep dive",
                       "Digital PA (CAD, SPID, PEC)", "Public procurement (Codice Appalti)",
                       "Constitutional law review for concorsi"],
        "one_month_prep": "Register on inPA.gov.it and set up alerts (1 day). Identify 5 open concorsi matching your profile (1 week). Start studying administrative law + procurement (2 weeks). Apply to first concorso (1 week).",
    },
    {
        "title": "Bilingual Customer Service (German-English-Italian)",
        "sector": "Customer Service / Call Center",
        "description": "Handle customer inquiries in German, English, and Italian for international companies (luxury, automotive, tech, travel) based in Rome or remote.",
        "avg_salary_eur": "28k-38k",
        "remote": "hybrid / remote (common)",
        "stress": "medium",
        "why_match": "You speak Italian (native), English (B2), and German (B2). Many companies in Rome hire trilingual staff for their European customer service centers. Your sales/CS experience is a perfect foundation.",
        "skill_gaps": ["Zendesk / Salesforce Service Cloud", "Call center KPIs (AHT, FCR, CSAT)",
                       "German business correspondence", "Complaint management techniques",
                       "Quality monitoring processes"],
        "one_month_prep": "Get Zendesk Customer Service certification (free, 1 week). Update LinkedIn with 'Trilingual Customer Service' headline (1 day). Apply to 10 roles at companies like Airbnb, Booking.com, Mercedes-Benz Rome (2 weeks).",
    },
    {
        "title": "Legal Tech / Document Specialist",
        "sector": "Legal / Technology",
        "description": "Manage legal document workflows, e-discovery, contract management at law firms or legal departments using technology platforms.",
        "avg_salary_eur": "30k-45k",
        "remote": "hybrid (common)",
        "stress": "low-medium",
        "why_match": "Your law degree + current role managing trial documents + IT proficiency. Legal tech is growing in Italy, and firms need people who understand both law AND software.",
        "skill_gaps": ["e-Discovery tools (Relativity, Everlaw)", "Contract lifecycle management (DocuSign CLM, Icertis)",
                       "Legal project management", "Basic SQL for legal databases",
                       "GDPR and data protection for legal tech"],
        "one_month_prep": "Take 'Legal Technology' course on Coursera (free, 1 week). Learn DocuSign eSignature basics (free, weekend). Build a simple contract tracking system in Excel (1 week). Apply to legal tech roles in Rome/Milan (1 week).",
    },
    {
        "title": "Trade Show / Event Coordinator (Sales Focus)",
        "sector": "Events / Hospitality / B2B",
        "description": "Coordinate B2B trade shows, corporate events, and networking events. Combine sales skills with event logistics.",
        "avg_salary_eur": "30k-40k",
        "remote": "in-person (mostly on-site)",
        "stress": "medium",
        "why_match": "Your sales background + relationship management + organizational skills. Rome/Fiumicino area has many exhibition centers and the growing tourism-event sector.",
        "skill_gaps": ["Event management software (Eventbrite, Cvent)", "Vendor negotiation",
                       "Logistics and timeline planning", "Budget management",
                       "Post-event analytics and ROI reporting"],
        "one_month_prep": "Get 'Event Management' certification from Eventbrite (free, 1 week). Volunteer at a Rome trade show to gain experience (weekend). Build an event planning portfolio concept (1 week). Apply to event coordinator roles (1 week).",
    },
    {
        "title": "HR / Recruitment Coordinator",
        "sector": "Human Resources",
        "description": "Support recruitment, onboarding, and HR operations at companies in Rome. Leverage communication and organizational skills.",
        "avg_salary_eur": "28k-38k",
        "remote": "hybrid (common)",
        "stress": "low-medium",
        "why_match": "Your sales background = you know how to talk to people and sell opportunities. Your organizational skills from managing multiple client accounts. Legal background is useful for employment law/compliance.",
        "skill_gaps": ["Applicant Tracking Systems (ATS)", "Labor law basics (Italian)",
                       "Interviewing techniques", "Employer branding",
                       "HR analytics and reporting"],
        "one_month_prep": "Complete 'HR Fundamentals' course on Coursera (free, 2 weeks). Learn about Italian labor law basics (1 week). Update LinkedIn for HR/recruitment visibility (1 week).",
    },
    {
        "title": "Tourism / Cultural Heritage Officer",
        "sector": "Tourism / Culture / Public Administration",
        "description": "Work in tourism promotion, cultural heritage management, or museum administration in Rome and Lazio.",
        "avg_salary_eur": "28k-38k",
        "remote": "in-person",
        "stress": "low",
        "why_match": "Your classical studies high school background + law degree + cycling tour guide qualification + languages. Rome is the cultural capital of Italy. Your administrative skills apply directly to museum/heritage management.",
        "skill_gaps": ["Cultural heritage law (Italian)", "Museum management basics",
                       "Tourism marketing and promotion", "EU cultural funding programs",
                       "Event programming for cultural sites"],
        "one_month_prep": "Research concorsi for cultural heritage roles in Lazio (1 week). Take 'Introduction to Museum Management' on Coursera (free, 1 week). Visit 3 cultural institutions and study their organizational structure (1 week).",
    },
    {
        "title": "Insurance Agent / Broker",
        "sector": "Insurance / Finance",
        "description": "Sell insurance products (life, health, property, auto) and advise clients on coverage. Commission + salary models.",
        "avg_salary_eur": "30k-50k (with commission)",
        "remote": "hybrid",
        "stress": "medium",
        "why_match": "Your sales track record + law degree (insurance law is a legal field). Your relationship management skills are perfect for client retention. Italian insurance market values legal knowledge for compliance.",
        "skill_gaps": ["Insurance product knowledge (life, non-life)", "IVASS regulations",
                       "Risk assessment basics", "Insurance sales techniques",
                       "Claims management processes"],
        "one_month_prep": "Study for the IVASS insurance agent exam (RE, RUI) — required in Italy (2 weeks). Take 'Insurance Fundamentals' on Coursera (free, 1 week). Connect with Allianz, Generali, Unipol agencies in Rome (1 week).",
    },
    {
        "title": "Export Manager / International Sales",
        "sector": "International Trade / Manufacturing",
        "description": "Manage international sales for Italian companies exporting products (food, fashion, machinery, design). Leverage language skills for German and English markets.",
        "avg_salary_eur": "35k-55k",
        "remote": "hybrid (some remote + travel)",
        "stress": "medium",
        "why_match": "Your sales management + languages (IT/EN/DE) + law degree (contracts, international trade law). Italian SMEs desperately need export managers who speak German. Rome/Lazio has many exporting companies.",
        "skill_gaps": ["International trade documentation", "Incoterms and customs procedures",
                       "Export marketing and market research", "Cross-cultural negotiation",
                       "Trade finance basics"],
        "one_month_prep": "Get 'International Trade' certification from ITA (free, 2 weeks). Learn Incoterms 2024 (weekend). Research Lazio-based exporting companies and prepare target list (1 week).",
    },
    {
        "title": "Compliance Officer (Legal/Administrative)",
        "sector": "Banking / Finance / Corporate",
        "description": "Ensure company compliance with regulations, manage anti-money laundering (AML) procedures, data protection (GDPR), and corporate governance.",
        "avg_salary_eur": "35k-55k",
        "remote": "hybrid (common in EU)",
        "stress": "medium",
        "why_match": "Your law degree is the standard entry path for compliance. Your administrative/legal role shows you understand regulatory frameworks. Growing field with stable, well-paid positions in Rome (banks, insurance, multinationals).",
        "skill_gaps": ["AML/KYC regulations", "GDPR and data protection", "Corporate governance (Testo Unico della Finanza)",
                       "Risk management frameworks", "Compliance monitoring tools"],
        "one_month_prep": "Complete 'AML and Compliance' course on Coursera (free, 2 weeks). Study GDPR fundamentals (1 week). Join compliance networking groups in Rome (1 week).",
    },
    {
        "title": "Judicial Clerk / Cancelliere (Justice System)",
        "sector": "Justice / Public Administration",
        "description": "Work as cancelliere (judicial clerk) in Italian courts — managing case files, scheduling hearings, authenticating documents.",
        "avg_salary_eur": "30k-40k",
        "remote": "in-office",
        "stress": "low-medium",
        "why_match": "You already work in the Court of Viterbo as a Legal-Administrative Officer. This is a natural next step or lateral move within the Ministry of Justice. Your experience is directly applicable to any cancelliere concorso.",
        "skill_gaps": ["Specific cancelliere procedures", "Civil procedure code (Codice di Procedura Civile)",
                       "Criminal procedure basics", "Electronic trial management (Processo Civile Telematico)",
                       "Judicial accounting"],
        "one_month_prep": "Monitor Ministry of Justice concorsi on inPA.gov.it (ongoing). Study Civil Procedure Code for concorso preparation (2 weeks). Talk to colleagues about career progression paths (1 week).",
    },
]

SKILL_ADJACENCY = {
    "Legal procedures": ["compliance", "cancelleria", "legal consulting", "paralegal"],
    "Sales management": ["account management", "export", "business development", "retail management"],
    "CRM": ["salesforce", "hubspot", "customer analytics", "account management"],
    "Negotiation": ["procurement", "contract management", "sales", "mediation"],
    "Administrative law": ["public administration", "concorsi", "procurement", "compliance"],
    "Customer relationship management": ["account management", "customer success", "helpdesk"],
    "Microsoft Office": ["administrative assistant", "office management", "data entry"],
    "English (B2)": ["bilingual roles", "international trade", "EU institutions", "export"],
    "German (B2)": ["german companies", "export to Germany", "trilingual CS", "tourism"],
    "Cycling tour guide": ["tourism", "cultural heritage", "outdoor education", "event coordination"],
}


def suggest_roles(profile: dict = None) -> list:
    if profile is None:
        profile = load_profile()

    skills = profile.get("technical_skills", {})
    all_skills = set()
    for cat, skill_list in skills.items():
        for s in skill_list:
            all_skills.add(s.lower())

    domains = set(d.lower() for d in skills.get("legal_administrative", []) +
                  skills.get("sales_customer_service", []) +
                  skills.get("soft_skills", []))
    known_roles = set(r.lower() for r in profile.get("target_roles", []))

    scored = []
    for role in UNCONVENTIONAL_ROLES:
        role_lower = role["title"].lower()
        if any(kr in role_lower or role_lower in kr for kr in known_roles):
            continue

        score = 0
        reasons = []

        for skill_name in all_skills:
            for adj_skill, adj_roles in SKILL_ADJACENCY.items():
                if adj_skill.lower() == skill_name:
                    for adj_role in adj_roles:
                        if any(w in adj_role for w in role_lower.split()) or \
                           any(w in role_lower for w in adj_role.split()):
                            score += 2
                            reasons.append(f"Skill: {adj_skill} → {adj_role}")

            if skill_name in role_lower:
                score += 3
                reasons.append(f"Direct skill: {skill_name}")

        for d in domains:
            if d in role_lower:
                score += 2
                reasons.append(f"Domain: {d}")

        why = role["why_match"].lower()
        for s in all_skills:
            if s in why:
                score += 1

        if score > 0:
            scored.append({**role, "score": score, "reasons": reasons[:3]})

    scored.sort(key=lambda x: -x["score"])
    return scored


def add_role(role_title: str, profile: dict = None) -> bool:
    if profile is None:
        profile = load_profile()

    all_roles = [r["title"] for r in UNCONVENTIONAL_ROLES]
    match = None
    for r in all_roles:
        if role_title.lower() in r.lower():
            match = r
            break

    if not match:
        return False

    existing = profile.get("target_roles", [])
    if match not in existing:
        existing.append(match)
        profile["target_roles"] = existing
        save_profile(profile)
    return True


def list_suggested(profile: dict = None) -> str:
    suggested = suggest_roles(profile)
    if not suggested:
        return "No new roles to suggest — you've already covered all adjacent roles!"

    lines = [
        "╔══════════════════════════════════════════════════════════════╗",
        "║      UNCONVENTIONAL ROLES YOU HAVEN'T CONSIDERED           ║",
        "╚══════════════════════════════════════════════════════════════╝",
        "",
        "These roles are adjacent to your skills but outside your current radar.",
        f"Found {len(suggested)} potential fits. Match score = how well your skills align.",
        "",
    ]

    for i, role in enumerate(suggested, 1):
        lines.append(f"{i}. {role['title']}  [{role['sector']}]")
        lines.append(f"   {'💰' + role['avg_salary_eur'] : <20} {'🌍' + role['remote'] : <30} {'😌' + role['stress'] : <20}")
        lines.append(f"   Match score: {'█' * min(role['score'], 10)}{'░' * max(0, 10 - role['score'])} ({role['score']})")
        lines.append(f"   Why: {role['why_match'][:120]}")
        lines.append(f"   Gaps: {', '.join(role['skill_gaps'][:4])}")
        lines.append(f"   1-month prep: {role['one_month_prep'][:120]}")
        lines.append("")

    lines.append("─── How to add a role ───")
    lines.append("  Type the role number to add it to your target_roles.")
    lines.append("  Or type 'suggest add <role title>' to add directly.")
    lines.append("")

    return "\n".join(lines)


SEARCH_LINKS = {
    "Concorsi Pubblici Specialist (Public Administration)": "linkedin.com/jobs/search/?keywords=funzionario+amministrativo+OR+concorso+pubblico",
    "Bilingual Customer Service (German-English-Italian)": "linkedin.com/jobs/search/?keywords=customer+service+german+italian+OR+trilingual+customer",
    "Legal Tech / Document Specialist": "linkedin.com/jobs/search/?keywords=legal+tech+OR+document+specialist+OR+paralegal",
    "Trade Show / Event Coordinator (Sales Focus)": "linkedin.com/jobs/search/?keywords=event+coordinator+OR+trade+show+coordinator",
    "HR / Recruitment Coordinator": "linkedin.com/jobs/search/?keywords=hr+coordinator+OR+recruitment+coordinator",
    "Tourism / Cultural Heritage Officer": "linkedin.com/jobs/search/?keywords=tourism+OR+cultural+heritage+OR+museum+administration",
    "Insurance Agent / Broker": "linkedin.com/jobs/search/?keywords=insurance+agent+OR+broker+OR+consulente+assicurativo",
    "Export Manager / International Sales": "linkedin.com/jobs/search/?keywords=export+manager+OR+international+sales+OR+esport",
    "Compliance Officer (Legal/Administrative)": "linkedin.com/jobs/search/?keywords=compliance+officer+OR+AML+OR+antiriciclaggio",
    "Judicial Clerk / Cancelliere (Justice System)": "linkedin.com/jobs/search/?keywords=cancelliere+OR+funzionario+giudiziario",
}


def scan_real_jobs_for_role(role_title: str, max_results: int = 5) -> list:
    from job_scanner import scan_remoteok, scan_indeed

    queries = {
        "Concorsi Pubblici Specialist (Public Administration)": "funzionario amministrativo OR concorso pubblico",
        "Bilingual Customer Service (German-English-Italian)": "customer service german italian OR trilingual support",
        "Legal Tech / Document Specialist": "legal tech OR paralegal OR document specialist",
        "Trade Show / Event Coordinator (Sales Focus)": "event coordinator OR trade show coordinator",
        "HR / Recruitment Coordinator": "hr coordinator OR recruitment coordinator OR risorse umane",
        "Tourism / Cultural Heritage Officer": "tourism officer OR cultural heritage OR museum",
        "Insurance Agent / Broker": "insurance agent OR broker OR consulente assicurativo",
        "Export Manager / International Sales": "export manager OR international sales OR esport manager",
        "Compliance Officer (Legal/Administrative)": "compliance officer OR AML OR antiriciclaggio",
        "Judicial Clerk / Cancelliere (Justice System)": "cancelliere OR funzionario giudiziario",
    }

    term = queries.get(role_title, role_title)

    seen = set()
    all_results = []

    def add_unique(results):
        for j in results:
            link = j.get("link", "")
            if link and link not in seen:
                seen.add(link)
                all_results.append(j)
                return True
        return False

    try:
        for kw_part in term.split(" OR "):
            kw = kw_part.strip().replace(" ", "+")
            jobs = scan_remoteok(keywords=[kw], limit=3)
            for j in jobs:
                add_unique(j)
                if len(all_results) >= max_results:
                    return all_results
    except Exception:
        pass

    try:
        for kw_part in term.split(" OR "):
            kw = kw_part.strip()
            jobs = scan_indeed(keywords=[kw])
            for j in jobs:
                add_unique(j)
                if len(all_results) >= max_results:
                    return all_results
    except Exception:
        pass

    return all_results[:max_results]


if __name__ == "__main__":
    print(list_suggested())
