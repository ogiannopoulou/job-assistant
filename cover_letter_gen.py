"""Cover Letter Generator v2 — tailored, multi-style, with project evidence."""

import re
from datetime import date
from pathlib import Path
from profile import load_profile

STYLES = {
    "professional": {
        "salutation": "Dear Hiring Team,",
        "closing": "Thank you for your consideration. I look forward to hearing from you.",
        "tone": "confident and concise",
    },
    "research": {
        "salutation": "Dear Members of the Search Committee,",
        "closing": "Thank you for your time and consideration. I would welcome the opportunity to discuss my background further.",
        "tone": "academic and collaborative",
    },
    "industry": {
        "salutation": "Dear Hiring Manager,",
        "closing": "I am eager to contribute to your team and would welcome the chance to discuss how my background can help solve your challenges. Thank you for your consideration.",
        "tone": "results-oriented",
    },
    "concise": {
        "salutation": "Dear Team,",
        "closing": "I would love to bring my skills to {company}. Thanks for considering my application.",
        "tone": "direct and efficient",
    },
}

PROFILE_PARAGRAPHS = {
    "legal_admin": (
        "I currently serve as a Legal-Administrative Officer at the Ministry of Justice - Court of Viterbo, "
        "where I manage trial office operations, certification services, public records, and complex document analysis. "
        "My Master's degree in Law from Sapienza University of Rome provides a strong foundation in legal procedures, "
        "administrative law, and regulatory compliance. I combine this legal expertise with proven organizational "
        "abilities and meticulous attention to detail."
    ),
    "sales": (
        "For eight years, I managed sales and customer relationships at Archegonia Flowers in Rome, "
        "where I consistently exceeded monthly and annual sales targets. I oversaw the full sales cycle from "
        "personalized quoting through after-sales support, developed long-term client relationships, and "
        "managed supplier relations to ensure efficient service delivery. This experience built my ability "
        "to understand client needs, negotiate effectively, and deliver results."
    ),
    "multilingual": (
        "I am a trilingual professional with native Italian, professional English (B2), and professional German (B2). "
        "My academic exchange year at Humboldt Universität Berlin and German language studies at Heidelberg "
        "University gave me deep cultural familiarity with German-speaking markets. I am comfortable working "
        "across Italian, English, and German business environments."
    ),
    "customer_service": (
        "Throughout my career, I have developed strong customer relationship skills. Whether managing key "
        "accounts at Archegonia Flowers, promoting Sony products at Free Way, or assisting customers at Unieuro, "
        "I have consistently focused on understanding needs, providing tailored solutions, and building lasting "
        "relationships. I believe that excellent service is the foundation of business success."
    ),
    "administration": (
        "My current role at the Ministry of Justice and previous management position have honed my organizational, "
        "time management, and problem-solving abilities. I regularly handle multiple simultaneous priorities, "
        "analyze large volumes of information, and ensure compliance with legal and administrative procedures. "
        "I am proficient in Microsoft Office, Windows, Mac OS, and electronic invoicing systems."
    ),
}

COMPANY_REASONS = {
    "ministero": "its central role in the Italian justice system and the opportunity to contribute to public service excellence",
    "justice": "its critical mission in upholding the rule of law, where my legal expertise and administrative experience can make a meaningful impact",
    "comune": "its role in serving the local community, where my administrative skills and legal background can support efficient public service delivery",
    "intesa": "its position as a leading Italian banking group, where my legal background and sales expertise would be valuable in compliance or client relations",
    "generali": "its leadership in the insurance sector and the opportunity to apply my legal knowledge and relationship management skills",
    "allianz": "its global presence and commitment to customer excellence, where my multilingual and sales background would be an asset",
    "enel": "its role in Italy's energy transition and the chance to contribute my administrative and legal expertise to a major corporate environment",
    "ferrari": "its excellence as an Italian luxury brand and the opportunity to bring my customer-focused sales approach to a prestigious environment",
    "luxury": "its position in the luxury sector, where my customer relationship skills and multilingual abilities are highly valued",
    "amazon": "its customer-centric culture and the chance to apply my operations and customer service experience at a global scale",
    "airbnb": "its global hospitality platform and the opportunity to use my trilingual customer service skills to support guests and hosts",
}


def _classify_job(job_title: str, job_desc: str = "") -> list:
    text = (job_title + " " + job_desc).lower()
    cats = []
    if any(w in text for w in ["legal", "law", "administrative", "justice",
                                "court", "compliance", "paralegal", "funzionario",
                                "amministrativo", "cancelliere", "giuridico"]):
        cats.append("legal_admin")
    if any(w in text for w in ["sales", "account manager", "sales manager",
                                "business development", "commerciale", "vendite",
                                "export", "key account", "trade"]):
        cats.append("sales")
    if any(w in text for w in ["customer service", "customer support", "helpdesk",
                                "servizio clienti", "call center", "customer care"]):
        cats.append("customer_service")
    if any(w in text for w in ["admin", "administrative", "coordinatore",
                                "office manager", "back office", "segreteria",
                                "impiegato", "operations", "logistics"]):
        cats.append("administration")
    if any(w in text for w in ["german", "english", "bilingual", "trilingual",
                                "multilingual", "lingue", "tedesco", "international"]):
        cats.append("multilingual")
    return cats if cats else ["legal_admin"]


def _pick_paragraphs(job_title: str, job_desc: str = "", custom: str = "") -> list:
    cats = _classify_job(job_title, job_desc)
    if custom:
        return [custom]

    paras = []
    used_cats = set()
    for cat in cats:
        if cat in PROFILE_PARAGRAPHS and cat not in used_cats:
            paras.append(PROFILE_PARAGRAPHS[cat])
            used_cats.add(cat)

    if not paras:
        paras.append(PROFILE_PARAGRAPHS["legal_admin"])

    # Second paragraph: supplement with cross-functional experience
    extra = []
    if "legal_admin" in used_cats and "sales" not in used_cats:
        extra.append(PROFILE_PARAGRAPHS["sales"])
    elif "sales" in used_cats and "legal_admin" not in used_cats:
        extra.append(PROFILE_PARAGRAPHS["legal_admin"])
    if "multilingual" not in used_cats:
        extra.append(PROFILE_PARAGRAPHS["multilingual"])

    if extra:
        paras.append("\n\n".join(extra[:2]))

    return paras


def _company_reason(company: str) -> str:
    c = company.lower()
    for key, reason in COMPANY_REASONS.items():
        if key in c:
            return reason
    return f"its work in {c} and the opportunity to bring my legal, administrative, and sales expertise to your team"


def _select_style(job_title: str, job_desc: str = "") -> str:
    text = (job_title + " " + job_desc).lower()
    if any(w in text for w in ["funzionario", "concorso", "pubblica amministrazione"]):
        return "research"
    if any(w in text for w in ["sales", "account", "commerciale", "vendite"]):
        return "concise"
    if any(w in text for w in ["admin", "coordinatore", "office", "impiegato"]):
        return "professional"
    return "professional"


TEMPLATE = """{date}

{company}
{company_address}

Subject: Application for {position_title}

{salutation}

I am writing to express my strong interest in the {position_title} position at {company}, as advertised on {source}. With a Master's Degree in Law from Sapienza University of Rome and extensive professional experience spanning legal administration, sales management, and customer service, I am confident that my background aligns well with your needs.

{paragraph_1}

{paragraph_2}

I am particularly drawn to {company} because of {company_reason}. I am eager to contribute to your team and would welcome the opportunity to discuss how my experience aligns with your goals.

{closing}

Best regards,

{name}
{email}
{phone}
"""


def generate(job_title: str, company: str, source: str = "your website",
             custom_paragraph: str = "", company_reason: str = "",
             company_address: str = "", output_dir: str = None,
             style: str = "auto", job_description: str = "") -> str:
    p = load_profile()

    if style == "auto":
        style = _select_style(job_title, job_description)
    style_config = STYLES.get(style, STYLES["professional"])

    paras = _pick_paragraphs(job_title, job_description, custom_paragraph)
    para_1 = paras[0] if paras else PROFILE_PARAGRAPHS["legal_admin"]
    para_2 = paras[1] if len(paras) > 1 else ""

    reason = company_reason or _company_reason(company)
    closing = style_config["closing"].format(company=company)

    content = TEMPLATE.format(
        date=date.today().strftime("%B %d, %Y"),
        company=company,
        company_address=company_address or company,
        position_title=job_title,
        source=source,
        salutation=style_config["salutation"],
        paragraph_1=para_1,
        paragraph_2=para_2,
        company_reason=reason,
        closing=closing,
        name=p["name"],
        email=p["email"],
        phone=p["phone"],
    )

    if output_dir:
        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)
        safe = "".join(c if c.isalnum() or c in " -_" else "_" for c in f"{company}_{job_title}")
        filepath = out / f"cover_letter_{safe[:80]}.txt"
        filepath.write_text(content)
        return str(filepath)

    return content
