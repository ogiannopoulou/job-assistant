# Job Assistant

A **job search copilot** that scans multiple job boards, ranks opportunities by your preferences, matches and rewrites CVs, generates cover letters, tracks applications, and analyzes skills — all from a web dashboard or CLI.

![Dashboard](https://img.shields.io/badge/streamlit-v1.58-red)
![Python](https://img.shields.io/badge/python-3.10+-blue)
![License](https://img.shields.io/badge/license-MIT-green)

---

## Features

| Feature | Description |
|---------|-------------|
| **Job Scanning** | Scrapes LinkedIn, Indeed, RemoteOK, Himalayas, Remotive, and INPA (Italian PA) |
| **Smart Ranking** | Scores jobs by your preferences — remote, salary, location, sector, stress level |
| **CV Rewriting** | Rewrites your CV to match job descriptions, outputs LaTeX → PDF or DOCX → PDF |
| **Cover Letters** | Generates tailored cover letters in multiple styles (professional, research, concise) |
| **Application Tracker** | Tracks status across the full pipeline: discovered → submitted → interview → outcome |
| **Skills Analysis** | Maps your skills against job requirements, identifies gaps |
| **Career Planning** | Generates personalized career roadmaps with course recommendations |
| **Role Discovery** | Suggests unconventional adjacent roles you might not have considered |

---

## Quick Start

### 1. Install

```bash
git clone https://github.com/ogiannopoulou/job-assistant.git
cd job-assistant
pip install -r requirements.txt
```

### 2. Run Dashboard

```bash
streamlit run dashboard.py
```

Open **http://localhost:8501** in your browser.

### 3. Or Use the CLI

```bash
python3 assistant.py
```

Type `help` at the `job>` prompt to see available commands.

---

## First-Time Setup

1. Open the **Profile** page and fill in your name, skills, experience
2. Open **Preferences** to set your job priorities (remote, salary, location, etc.)
3. Go to **Job Board** and click **"Scan All Sources"** to fetch live jobs
4. Use **Rank** to sort jobs by your preferences
5. Start applying — the tracker will log everything

### CV Setup (Optional)

To use CV rewriting, place your CV text file in `data/cv_texts/` and update `profile_data.json`:
```json
"cv_files": {
    "My_CV": "data/cv_texts/My_CV.pdf"
}
```

---

## Project Structure

```
job-assistant/
├── dashboard.py            # Streamlit web UI (13 pages)
├── assistant.py            # CLI interface (REPL)
├── job_scanner.py          # Multi-source job scraping
├── job_ranker.py           # Preference-based scoring
├── cv_writer.py            # CV rewriting + PDF generation
├── cv_matcher.py           # Best-CV picker for each job
├── cover_letter_gen.py     # Cover letter generator
├── profile.py              # User profile manager
├── preferences.py          # Preference viewer/editor
├── optimizer.py            # Strategy & career planning
├── skills_analyzer.py      # Job fit analysis
├── skill_inventory.py      # Unified skill database
├── role_suggester.py       # Unconventional role discovery
├── tracker.py              # Application tracking
├── project_scanner.py      # Local project scanner
├── github_integrator.py    # GitHub API integration
├── cv_parser.py            # PDF CV text extraction
├── profile_data.json       # Your profile & preferences
├── requirements.txt        # Python dependencies
└── data/                   # CV files, job cache, skill inventory
```

---

## Tech Stack

- **Python 3.10+**
- **Streamlit** — web dashboard
- **Pandas + Plotly** — data analysis & charts
- **BeautifulSoup** — job board scraping
- **fpdf2** — cover letter PDF generation
- **Jinja2 + LaTeX** — CV rendering
- **python-docx** — DOCX CV output
- **pdfminer.six** — PDF text extraction
- **Rich** — CLI formatting

---

## Roadmap

- [ ] User authentication & multi-tenant support
- [ ] LLM-powered cover letter & CV generation (GPT/Claude)
- [ ] Email alerts for new job matches
- [ ] Salary benchmark & market analytics
- [ ] Mobile companion app
- [ ] API integrations (Greenhouse, Lever, etc.)

---

## License

MIT
