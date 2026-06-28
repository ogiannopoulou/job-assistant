"""Application Tracker -- logs applications, deadlines, status."""

import csv
from datetime import date, datetime
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)

TRACKER_FILE = DATA_DIR / "applications.csv"
FIELDS = ["date", "company", "position", "source", "cv_used", "deadline",
          "status", "link", "notes", "last_updated"]


def _ensure_file():
    if not TRACKER_FILE.exists():
        with open(TRACKER_FILE, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(FIELDS)


def add(company: str, position: str, source: str = "", cv_used: str = "",
        deadline: str = "", status: str = "discovered", link: str = "",
        notes: str = ""):
    _ensure_file()
    with open(TRACKER_FILE, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow([str(date.today()), company, position, source, cv_used,
                    deadline, status, link, notes, datetime.now().isoformat()])
    print(f"  [+] Logged: {position} @ {company} [{status}]")


def update(company: str, position: str, status: str, notes: str = ""):
    _ensure_file()
    rows = []
    updated = False
    with open(TRACKER_FILE, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["company"] == company and row["position"] == position:
                row["status"] = status
                if notes:
                    row["notes"] = notes
                row["last_updated"] = datetime.now().isoformat()
                updated = True
            rows.append(row)

    if updated:
        with open(TRACKER_FILE, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=FIELDS)
            w.writeheader()
            w.writerows(rows)
        print(f"  [~] Updated: {position} @ {company} -> {status}")
    else:
        print(f"  [!] Entry not found for {position} @ {company}")


def list_applications(status: str = None):
    _ensure_file()
    with open(TRACKER_FILE, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    if status:
        rows = [r for r in rows if r["status"] == status]
    return rows


def summary():
    rows = list_applications()
    if not rows:
        return "No applications tracked yet."
    counts = {}
    for r in rows:
        s = r["status"]
        counts[s] = counts.get(s, 0) + 1
    lines = [f"Total applications: {len(rows)}"]
    for s, c in sorted(counts.items()):
        lines.append(f"  {s}: {c}")
    return "\n".join(lines)


def get_pending_deadlines():
    rows = list_applications()
    today = date.today()
    pending = []
    for r in rows:
        try:
            dl = datetime.strptime(r["deadline"], "%d/%m/%Y").date() if r["deadline"] else None
            if dl and dl >= today and r["status"] in ("discovered", "preparing"):
                pending.append(r)
        except (ValueError, TypeError):
            pass
    return sorted(pending, key=lambda x: x.get("deadline", ""))


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "summary":
        print(summary())
    else:
        print(list_applications())
