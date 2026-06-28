"""Project Scanner — extracts tech stacks, languages, and summaries from local project folders."""

import json
import os
import re
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"
P_FOLDERS_BASE = Path(os.path.expanduser("~/Documents"))
PORTFOLIO_BASE = Path(os.path.expanduser("~/Documents/p9_portfolgio"))

LANG_EXTENSIONS = {
    ".py": "Python",
    ".ipynb": "Jupyter Notebook",
    ".js": "JavaScript",
    ".ts": "TypeScript",
    ".tsx": "TypeScript (React)",
    ".jsx": "JavaScript (React)",
    ".java": "Java",
    ".kt": "Kotlin",
    ".kts": "Kotlin",
    ".swift": "Swift",
    ".c": "C",
    ".cpp": "C++",
    ".h": "C/C++ Header",
    ".hpp": "C++ Header",
    ".f90": "Fortran",
    ".f": "Fortran",
    ".m": "MATLAB",
    ".sh": "Bash",
    ".R": "R",
    ".r": "R",
    ".go": "Go",
    ".rs": "Rust",
    ".cs": "C#",
    ".fs": "F#",
    ".rb": "Ruby",
    ".php": "PHP",
    ".html": "HTML",
    ".css": "CSS",
    ".scss": "SASS",
    ".tex": "LaTeX",
    ".md": "Markdown",
    ".yaml": "YAML",
    ".yml": "YAML",
    ".toml": "TOML",
    ".json": "JSON",
    ".xml": "XML",
    ".gradle": "Gradle",
    ".docx": "Word Document",
    ".xlsx": "Excel Spreadsheet",
    ".pptx": "PowerPoint",
    ".pdf": "PDF Document",
}

TECH_KEYWORDS = {
    "microsoft office": "Microsoft Office",
    "excel": "Microsoft Excel",
    "word": "Microsoft Word",
    "powerpoint": "Microsoft PowerPoint",
    "outlook": "Microsoft Outlook",
    "windows": "Windows",
    "mac os": "Mac OS",
    "electronic invoicing": "Electronic Invoicing",
    "fatturazione": "Electronic Invoicing",
    "sap": "SAP",
    "salesforce": "Salesforce",
    "hubspot": "HubSpot",
    "zendesk": "Zendesk",
    "crm": "CRM",
    "gdpr": "GDPR",
    "legal": "Legal Procedures",
    "compliance": "Compliance",
    "concorsi": "Public Administration",
    "public administration": "Public Administration",
    "amministrativo": "Administrative Skills",
    "vendite": "Sales Management",
    "commerciale": "Sales Management",
    "negoziazione": "Negotiation",
    "servizio clienti": "Customer Service",
    "german": "German Language",
    "tedesco": "German Language",
    "english": "English Language",
    "inglese": "English Language",
}


def scan_readme(folder: Path) -> str:
    for name in ("README.md", "README.txt", "README", "readme.md"):
        p = folder / name
        if p.exists():
            try:
                return p.read_text(encoding="utf-8", errors="ignore")[:5000]
            except Exception:
                pass
    return ""


def detect_languages(folder: Path) -> dict:
    counts = {}
    for root, dirs, files in os.walk(str(folder)):
        dirs[:] = [d for d in dirs if not d.startswith(".") and d != "__pycache__"
                   and d != "node_modules" and d != ".venv" and d != "venv"
                   and d != ".git" and d != "build" and d != "dist"]
        for f in files:
            ext = os.path.splitext(f)[1].lower()
            if ext in LANG_EXTENSIONS:
                lang = LANG_EXTENSIONS[ext]
                counts[lang] = counts.get(lang, 0) + 1
    return dict(sorted(counts.items(), key=lambda x: -x[1]))


def extract_techs_from_text(text: str) -> list:
    found = set()
    lower = text.lower()
    for keyword, tech_name in TECH_KEYWORDS.items():
        if keyword in lower:
            found.add(tech_name)
    return sorted(found)


def extract_requirements(folder: Path) -> list:
    for name in ("requirements.txt", "environment.yml", "environment.yaml",
                 "Pipfile", "pyproject.toml", "package.json"):
        p = folder / name
        if p.exists():
            try:
                return [line.strip() for line in p.read_text(encoding="utf-8", errors="ignore").splitlines()
                        if line.strip() and not line.strip().startswith(("#", "//", "-"))][:20]
            except Exception:
                pass
    return []


def scan_single_folder(folder: Path, label: str = None, group: str = "p_folder") -> dict:
    if not folder.exists():
        return None
    readme = scan_readme(folder)
    languages = detect_languages(folder)
    techs = extract_techs_from_text(readme)
    for root, dirs, files in os.walk(str(folder)):
        dirs[:] = [d for d in dirs if not d.startswith(".") and d != "__pycache__"
                   and d != "node_modules" and d != ".venv" and d != "venv"
                   and d != ".git" and d != "build" and d != "dist"]
        for f in files:
            if f.endswith((".py", ".ipynb", ".m", ".cpp", ".c", ".h", ".java", ".kt", ".js", ".ts", ".docx", ".xlsx", ".pptx", ".pdf")):
                try:
                    fp = Path(root) / f
                    snippet = fp.read_text(encoding="utf-8", errors="ignore")[:2000]
                    more_techs = extract_techs_from_text(snippet)
                    techs = list(set(techs + more_techs))
                except Exception:
                    pass

    deps = extract_requirements(folder)
    techs_in_deps = extract_techs_from_text(" ".join(deps))
    techs = list(set(techs + techs_in_deps))

    return {
        "name": label or folder.name,
        "path": str(folder),
        "group": group,
        "readme_preview": readme[:500] if readme else "",
        "languages": languages,
        "tech_stack": sorted(techs),
        "dependencies": deps,
        "has_readme": bool(readme),
        "total_files": sum(len(files) for _, _, files in os.walk(str(folder))),
    }


def scan_p_folders() -> list:
    results = []
    p_dirs = sorted(P_FOLDERS_BASE.glob("p*"))
    for d in p_dirs:
        if d.is_dir() and d.name.startswith("p") and d.name[1:2].isdigit():
            r = scan_single_folder(d, group="p_folder")
            if r:
                results.append(r)
    return results


def scan_portfolio() -> list:
    results = []
    if PORTFOLIO_BASE.exists():
        for d in sorted(PORTFOLIO_BASE.iterdir()):
            if d.is_dir() and not d.name.startswith("."):
                r = scan_single_folder(d, group="portfolio")
                if r:
                    results.append(r)
    return results


def scan_all() -> list:
    return scan_p_folders() + scan_portfolio()


def save_inventory(projects: list = None):
    if projects is None:
        projects = scan_all()
    path = DATA_DIR / "projects_inventory.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(projects, f, indent=2, default=str)
    print(f"Saved {len(projects)} projects to {path}")
    return path


def load_inventory() -> list:
    path = DATA_DIR / "projects_inventory.json"
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return []


def get_all_techs(projects: list = None) -> dict:
    if projects is None:
        projects = load_inventory()
    techs = {}
    for p in projects:
        for t in p.get("tech_stack", []):
            techs.setdefault(t, []).append(p["name"])
    return techs


def get_summary() -> str:
    projects = load_inventory()
    if not projects:
        return "No projects scanned yet."
    techs = get_all_techs(projects)
    p_folders = [p for p in projects if p["group"] == "p_folder"]
    portfolio = [p for p in projects if p["group"] == "portfolio"]
    all_langs = {}
    for p in projects:
        for lang, count in p.get("languages", {}).items():
            all_langs[lang] = all_langs.get(lang, 0) + count

    lines = [
        f"Projects scanned: {len(projects)}",
        f"  P-folders: {len(p_folders)}",
        f"  Portfolio: {len(portfolio)}",
        "",
        "Top languages:",
    ]
    for lang, count in sorted(all_langs.items(), key=lambda x: -x[1])[:10]:
        lines.append(f"  {lang}: {count} files")
    lines.extend([
        "",
        f"Tech stack breadth: {len(techs)} technologies",
        "",
        "Key technologies:",
    ])
    for t, projs in sorted(techs.items(), key=lambda x: -len(x[1]))[:20]:
        lines.append(f"  {t}: {len(projs)} projects ({', '.join(projs[:4])})")
    return "\n".join(lines)


if __name__ == "__main__":
    print("Scanning all projects...")
    projects = scan_all()
    save_inventory(projects)
    print(get_summary())
