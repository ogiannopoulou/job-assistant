"""GitHub Integrator — fetches repo data from public GitHub API."""

import json
import time
import urllib.request
import urllib.error
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"
GITHUB_USER = ""
API_BASE = f"https://api.github.com/users/{GITHUB_USER}" if GITHUB_USER else ""


def fetch_json(url: str, retries: int = 2) -> dict | list | None:
    if not url:
        return None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "job-assistant"})
            with urllib.request.urlopen(req, timeout=15) as resp:
                return json.loads(resp.read().decode())
        except urllib.error.HTTPError as e:
            if e.code == 403:
                remaining = e.headers.get("X-RateLimit-Remaining", "0")
                reset_time = int(e.headers.get("X-RateLimit-Reset", "0"))
                wait = max(reset_time - time.time() + 5, 0)
                print(f"  Rate limited. Waiting {wait:.0f}s...")
                time.sleep(min(wait, 60))
                continue
            elif e.code == 404:
                return None
            else:
                print(f"  HTTP {e.code}: {url}")
                return None
        except Exception as e:
            print(f"  Error: {e}")
            return None
    return None


def fetch_all_repos() -> list:
    if not GITHUB_USER:
        return []
    repos = []
    page = 1
    while True:
        url = f"{API_BASE}/repos?per_page=100&page={page}&sort=updated"
        data = fetch_json(url)
        if not data or len(data) == 0:
            break
        repos.extend(data)
        page += 1
        time.sleep(0.5)
    return repos


def fetch_languages(repo_full_name: str) -> dict:
    if not GITHUB_USER:
        return {}
    url = f"https://api.github.com/repos/{repo_full_name}/languages"
    return fetch_json(url) or {}


def fetch_readme(repo_full_name: str) -> str:
    if not GITHUB_USER:
        return ""
    url = f"https://api.github.com/repos/{repo_full_name}/readme"
    data = fetch_json(url)
    if data and "content" in data:
        import base64
        try:
            return base64.b64decode(data["content"]).decode("utf-8")[:2000]
        except Exception:
            pass
    return ""


def scan_all() -> list:
    if not GITHUB_USER:
        return []
    print(f"Fetching repos for {GITHUB_USER}...")
    repos = fetch_all_repos()
    print(f"  Found {len(repos)} repos")
    results = []
    for i, repo in enumerate(repos):
        name = repo.get("name", "unknown")
        print(f"  [{i+1}/{len(repos)}] {name}")
        full_name = repo.get("full_name", "")
        langs = fetch_languages(full_name)
        readme = fetch_readme(full_name)
        time.sleep(0.5)
        results.append({
            "name": name,
            "full_name": full_name,
            "url": repo.get("html_url", ""),
            "description": repo.get("description") or "",
            "fork": repo.get("fork", False),
            "language": repo.get("language"),
            "languages": langs,
            "topics": repo.get("topics", []),
            "stars": repo.get("stargazers_count", 0),
            "forks": repo.get("forks_count", 0),
            "created": repo.get("created_at", ""),
            "updated": repo.get("updated_at", ""),
            "readme_preview": readme[:500] if readme else "",
        })
    return results


def save_results(repos: list = None):
    if repos is None:
        repos = scan_all()
    path = DATA_DIR / "github_repos.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(repos, f, indent=2, default=str)
    print(f"Saved {len(repos)} repos to {path}")
    return path


def load_results() -> list:
    path = DATA_DIR / "github_repos.json"
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return []


def get_summary() -> str:
    repos = load_results()
    if not repos:
        return "No GitHub data yet."
    own = [r for r in repos if not r.get("fork")]
    forked = [r for r in repos if r.get("fork")]
    all_langs = {}
    for r in repos:
        for lang, count in r.get("languages", {}).items():
            all_langs[lang] = all_langs.get(lang, 0) + count
    lines = [
        f"GitHub repos: {len(repos)} ({len(own)} own, {len(forked)} forked)",
        "",
        "Languages:",
    ]
    for lang, count in sorted(all_langs.items(), key=lambda x: -x[1])[:10]:
        lines.append(f"  {lang}: {count} bytes")
    lines.append("")
    lines.append("Own repos:")
    for r in sorted(own, key=lambda x: -x["stars"]):
        lines.append(f"  {r['name']}: {r['stars']} stars — {r.get('description', 'no desc')[:60]}")
    return "\n".join(lines)


if __name__ == "__main__":
    save_results()
    print(get_summary())
