#!/usr/bin/env python3
"""Job Assistant CLI -- Your personalized job search copilot."""

import sys
import json
from pathlib import Path
from datetime import date

sys.path.insert(0, str(Path(__file__).parent))

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.markdown import Markdown
    from rich.prompt import Prompt, Confirm
    from rich import box
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

from profile import load_profile, summarize as profile_summary, save_profile, PORTFOLIO_BASE
from job_scanner import scan_all, save_results, load_results
from cv_matcher import match_cv, recommend_cv, CV_PROFILES
from job_scanner import is_valid_job
from cover_letter_gen import generate as gen_cover_letter
from role_suggester import suggest_roles, add_role, list_suggested
from tracker import add as track_add, update as track_update, list_applications, summary as track_summary
from skills_analyzer import analyze_job_fit, suggest_cv_and_tips
from job_ranker import rank_jobs, format_ranked, load_inventory as load_skill_inv
from optimizer import generate_digest, suggest_next_action, suggest_skill_gaps, \
    generate_career_plan, suggest_courses
from preferences import show as show_prefs, set_pref as set_preference, list_keys as list_prefs
from cv_writer import rewrite_cv, auto_rewrite_cv, get_base_cv_for_job, list_available_cvs

console = Console() if RICH_AVAILABLE else None


def pr(text, style=None):
    if console:
        if style:
            console.print(text, style=style)
        else:
            console.print(text)
    else:
        print(text)


def panel(title, content, style="cyan"):
    if console:
        console.print(Panel(content, title=title, border_style=style))
    else:
        print(f"=== {title} ===")
        print(content)


def cmd_profile():
    panel("YOUR PROFILE", profile_summary(), "green")


def cmd_scan():
    pr("[yellow]Scanning job sources...[/yellow]")
    sources = ["euraxess", "mur", "linkedin", "remoteok", "weworkremotely", "indeed", "egu"]
    jobs = scan_all(sources)
    path = save_results(jobs)
    pr(f"[green]Found {len(jobs)} jobs. Saved to {path}[/green]")

    if jobs:
        table = Table(title=f"Jobs Found ({len(jobs)})", box=box.ROUNDED)
        table.add_column("#", style="dim")
        table.add_column("Title")
        table.add_column("Organization")
        table.add_column("Source")
        table.add_column("Deadline")
        for i, j in enumerate(jobs[:25], 1):
            table.add_row(str(i), j.get("title", "?")[:60], j.get("organization", "?")[:25],
                         j.get("source", "?"), j.get("deadline", "?")[:15])
        if console:
            console.print(table)
        else:
            for i, j in enumerate(jobs[:15], 1):
                print(f"{i}. {j['title'][:60]} - {j.get('organization', '?')}")
    return jobs


def cmd_analyze():
    jobs = load_results()
    if not jobs:
        pr("[yellow]No jobs loaded. Run 'scan' first.[/yellow]")
        return

    for j in jobs:
        analysis = analyze_job_fit(j.get("title", ""), j.get("description", ""))
        j["_analysis"] = analysis

    if console:
        table = Table(title="Skills Match Analysis", box=box.ROUNDED)
        table.add_column("#")
        table.add_column("Title", width=40)
        table.add_column("Org", width=15)
        table.add_column("Fit")
        table.add_column("Best CV")
        table.add_column("Category")
        for i, j in enumerate(jobs[:20], 1):
            a = j.get("_analysis", {})
            fit = a.get("fit_label", "?")
            fit_style = {"strong": "green", "moderate": "yellow", "weak": "dim", "unlikely": "red"}.get(fit, "")
            best_cat = a.get("best_category", "?").replace("_", " ").title()
            rec = recommend_cv(j.get("title", ""))
            table.add_row(str(i), j.get("title", "?")[:40], j.get("organization", "?")[:15],
                         f"[{fit_style}]{fit}[/{fit_style}]" if fit_style else fit,
                         rec["cv_key"], best_cat)
        console.print(table)
    else:
        for i, j in enumerate(jobs[:20], 1):
            a = j.get("_analysis", {})
            print(f"{i}. {j['title'][:50]} | Fit: {a.get('fit_label', '?')} | CV: {j.get('_cv_recommendation', '?')}")

    strong = sum(1 for j in jobs if j.get("_analysis", {}).get("fit_label") == "strong")
    moderate = sum(1 for j in jobs if j.get("_analysis", {}).get("fit_label") == "moderate")
    if console:
        console.print(f"\n[bold]Summary:[/bold] {strong} strong matches, {moderate} moderate matches out of {len(jobs)} jobs")
        if strong:
            console.print("[green]Strong matches are worth prioritizing![/green]")
    else:
        print(f"\nSummary: {strong} strong, {moderate} moderate out of {len(jobs)} jobs")
    return jobs


def cmd_match():
    jobs = load_results()
    if not jobs:
        pr("[yellow]No jobs loaded. Run 'scan' first.[/yellow]")
        return

    for j in jobs:
        rec = recommend_cv(j.get("title", ""), j.get("description", ""))
        j["_cv_recommendation"] = rec["cv_key"]

    pr("[green]CV recommendations added to jobs.[/green]")
    table = Table(title="Jobs with CV Match", box=box.ROUNDED)
    table.add_column("#")
    table.add_column("Title", width=45)
    table.add_column("Organization", width=20)
    table.add_column("Best CV")
    table.add_column("Score")
    for i, j in enumerate(jobs[:20], 1):
        rec = j.get("_cv_recommendation", "?")
        score = sum(1 for kw in CV_PROFILES.get(rec, {}).get("focus", [])
                   if kw.lower() in (j.get("title", "") + j.get("description", "")).lower())
        table.add_row(str(i), j.get("title", "?")[:45], j.get("organization", "?")[:20], rec, str(score))
    if console:
        console.print(table)
    return jobs


def cmd_apply():
    jobs = load_results()
    if not jobs:
        pr("[yellow]No jobs loaded. Run 'scan' first.[/yellow]")
        return

    for i, j in enumerate(jobs[:20], 1):
        rec = recommend_cv(j.get("title", ""))
        analysis = analyze_job_fit(j.get("title", ""))
        fit = analysis["fit_label"]
        fit_icon = {"strong": "✅", "moderate": "📌", "weak": "👀", "unlikely": ""}.get(fit, "")

        if console:
            console.print(f"[bold]{i}.[/bold] {j['title'][:70]} {fit_icon}")
            console.print(f"    [dim]{j.get('organization', '?')} | CV: {rec['cv_key']} | Fit: {fit}[/dim]")
        else:
            print(f"{i}. {j['title'][:70]} {fit_icon}")
            print(f"   {j.get('organization', '?')} | CV: {rec['cv_key']} | Fit: {fit}")

    if console:
        choice = Prompt.ask("[yellow]Which job to apply to? (number or 'q')[/yellow]")
    else:
        choice = input("Which job to apply to? (number or q): ")

    if choice.lower() in ("q", "quit", "exit"):
        return

    try:
        idx = int(choice) - 1
        job = jobs[idx]
    except (ValueError, IndexError):
        pr("[red]Invalid choice[/red]")
        return

    title = job.get("title", "Position")
    company = job.get("organization", "Company")
    link = job.get("link", "")
    source = job.get("source", "website")
    rec = recommend_cv(title)
    cv_path = rec.get("cv_path", "")

    if console:
        console.print(f"\n[bold]Applying for:[/bold] {title}")
        console.print(f"[bold]Company:[/bold] {company}")
        console.print(f"[bold]Link:[/bold] {link}")
        console.print(f"[bold]Recommended CV:[/bold] {rec['cv_key']} -> {cv_path}")
    else:
        print(f"\nApplying for: {title}")
        print(f"Company: {company}")
        print(f"Link: {link}")
        print(f"Recommended CV: {rec['cv_key']} -> {cv_path}")

    if Confirm.ask("Generate cover letter?", default=True) if console else \
          input("Generate cover letter? (y/n): ").lower().startswith("y"):
        cl_dir = Path(__file__).parent / "cover_letters"
        if console:
            style_choice = Prompt.ask(
                "Style?", default="auto",
                choices=["auto", "professional", "research", "industry", "concise"]
            )
        else:
            style_choice = input("Style? (auto/professional/research/industry/concise): ") or "auto"
        try:
            cl_path = gen_cover_letter(
                title, company, source,
                output_dir=str(cl_dir),
                style=style_choice,
                job_description=job.get("description", ""),
            )
            pr(f"[green]Cover letter saved: {cl_path}[/green]")
            if console:
                preview = Confirm.ask("Preview cover letter?", default=False)
                if preview:
                    content = Path(cl_path).read_text()
                    console.print(Panel(content[:800], title="COVER LETTER (preview)", border_style="green"))
        except Exception as e:
            cl_path = gen_cover_letter(title, company, source, output_dir=str(cl_dir))
            pr(f"[green]Cover letter saved (simple): {cl_path}[/green]")

    track_add(company, title, source, rec["cv_key"],
              job.get("deadline", ""), "preparing", link)

    if console:
        console.print(f"\n[bold green]Tracked! Status: preparing[/bold green]")
        console.print(f"[yellow]Next steps:[/yellow]")
        console.print(f"  1. Open link and review requirements")
        console.print(f"  2. Attach CV: {rec['cv_key']}")
        console.print(f"  3. Customize cover letter")
        console.print(f"  4. Submit and update status with 'status' command")
    else:
        print(f"\nTracked! Status: preparing")
        print(f"Next: review requirements, customize, submit")


def cmd_status():
    if console:
        s = track_summary()
        console.print(Panel(s, title="APPLICATION STATUS", border_style="cyan"))
    else:
        print(track_summary())

    rows = list_applications()
    if rows:
        table = Table(title="Recent Applications", box=box.ROUNDED)
        table.add_column("Date")
        table.add_column("Company")
        table.add_column("Position", width=40)
        table.add_column("Status")
        for r in rows[-10:]:
            table.add_row(r.get("date", "?")[:10], r.get("company", "?")[:20],
                         r.get("position", "?")[:40], r.get("status", "?"))
        if console:
            console.print(table)
        else:
            for r in rows[-5:]:
                print(f"{r['date']} | {r['company'][:20]} | {r['position'][:40]} | {r['status']}")


def cmd_update_status():
    rows = list_applications()
    active = [r for r in rows if r["status"] not in ("rejected", "withdrawn", "accepted")]
    if not active:
        pr("[yellow]No active applications to update.[/yellow]")
        return

    for i, r in enumerate(active, 1):
        if console:
            console.print(f"[bold]{i}.[/bold] {r['position'][:60]} @ {r['company']} [dim]({r['status']})[/dim]")
        else:
            print(f"{i}. {r['position'][:60]} @ {r['company']} ({r['status']})")

    if console:
        choice = Prompt.ask("[yellow]Which one to update? (number)[/yellow]")
    else:
        choice = input("Which one to update? (number): ")

    try:
        idx = int(choice) - 1
        row = active[idx]
    except (ValueError, IndexError):
        pr("[red]Invalid choice[/red]")
        return

    statuses = ["preparing", "submitted", "under_review", "interview_scheduled",
                "interviewed", "rejected", "accepted", "withdrawn"]

    if console:
        for i, s in enumerate(statuses, 1):
            console.print(f"  {i}. {s}")
        new_status = Prompt.ask("[yellow]New status (number)[/yellow]")
    else:
        for i, s in enumerate(statuses, 1):
            print(f"  {i}. {s}")
        new_status = input("New status (number): ")

    try:
        new_status = statuses[int(new_status) - 1]
    except (ValueError, IndexError):
        pr("[red]Invalid[/red]")
        return

    track_update(row["company"], row["position"], new_status)
    if console:
        console.print(f"[green]Updated![/green]")


def cmd_rank():
    from job_ranker import rank_jobs, format_ranked
    from job_scanner import load_results
    jobs = load_results()
    if not jobs:
        pr("[yellow]No jobs loaded. Run 'scan' first.[/yellow]")
        return
    valid = [j for j in jobs if j.get("title", "") and len(j["title"]) > 5]
    ranked = rank_jobs(valid)
    panel(f"JOBS RANKED BY YOUR PREFERENCES ({len(ranked)} total)", format_ranked(ranked), "cyan")
    return ranked


def cmd_gaps():
    gaps = suggest_skill_gaps()
    if not gaps:
        panel("SKILL GAPS", "No critical gaps found!", "green")
    else:
        text = "\n".join(f"  • {g['message']}" for g in gaps)
        panel("SKILL GAPS", text, "yellow")


def cmd_optimize():
    action = suggest_next_action()
    content = f"[bold]{action['message']}[/bold]\n{action['detail']}"
    style = {"high": "red", "medium": "yellow", "low": "cyan"}.get(action["priority"], "")
    panel("NEXT ACTION", content, style)


def cmd_digest():
    panel("WEEKLY DIGEST", generate_digest(), "cyan")


def cmd_preferences(args=""):
    if not args:
        panel("YOUR PREFERENCES", show_prefs(), "cyan")
    elif args.startswith("set "):
        rest = args[4:]
        if " " in rest:
            key, val = rest.split(" ", 1)
            result = set_preference(key, val)
            pr(f"[green]{result}[/green]" if "✅" in result else f"[red]{result}[/red]")
        else:
            pr("[red]Usage: preferences set <key> <value>[/red]")
    elif args == "list":
        pr(list_prefs())
    else:
        pr("[red]Usage: preferences [set <key> <value> | list][/red]")


def cmd_plan():
    panel("CAREER ROADMAP", generate_career_plan(), "green")


def cmd_context():
    ctx_path = Path(__file__).parent / "data" / "session_context.json"
    if not ctx_path.exists():
        pr("[yellow]No session context saved yet. Run 'plan' first.[/yellow]")
        return
    with open(ctx_path) as f:
        ctx = json.load(f)

    lines = []
    lines.append(f"[bold]Session Context — {ctx.get('last_updated', '?')}[/bold]")
    lines.append("")

    market = ctx.get("remote_eu_job_market", {})
    matches = market.get("matches_found", [])
    if matches:
        lines.append("[bold]Remote EU Job Matches Found:[/bold]")
        for m in matches:
            lines.append(f"  • {m['role']} @ {m['company']} ({m['location']}) — {m['salary']}")
        lines.append("")

    crit = ctx.get("critical_context", {})
    lines.append("[bold]Your Priorities:[/bold]")
    for d in crit.get("desires", []):
        lines.append(f"  • {d}")
    lines.append("")

    if console:
        console.print(Panel("\n".join(lines), title="SESSION CONTEXT", border_style="magenta"))
    else:
        print("\n".join(lines))


def cmd_courses(args=""):
    if args:
        result = suggest_courses(args)
    else:
        result = suggest_courses()
    panel("RECOMMENDED COURSES", result, "yellow")


def cmd_suggest():
    suggested = suggest_roles()
    panel("UNCONVENTIONAL ROLES", list_suggested(), "yellow")

    if not suggested:
        return

    try:
        if console:
            choice = Prompt.ask("[yellow]Add a role? (number, 'all', or 'n')[/yellow]")
        else:
            choice = input("Add a role? (number, 'all', or 'n'): ")
    except (EOFError, KeyboardInterrupt):
        return

    if choice.lower() in ("n", "no", ""):
        return
    if choice.lower() == "all":
        added = 0
        for role in suggested:
            if add_role(role["title"]):
                added += 1
        pr(f"[green]Added {added} new roles to your target_roles![/green]")
        return

    try:
        idx = int(choice) - 1
        role = suggested[idx]
        if add_role(role["title"]):
            pr(f"[green]Added '{role['title']}' to your target_roles![/green]")
        else:
            pr("[yellow]Role already in your target list.[/yellow]")
    except (ValueError, IndexError):
        pr("[red]Invalid choice[/red]")


def cmd_cv(args=""):
    if args == "list":
        p = load_profile()
        cvs = p.get("cv_files", {})
        if not cvs:
            pr("[yellow]No CV files registered.[/yellow]")
            return
        lines = ["Available CVs:", ""]
        for key, path in sorted(cvs.items()):
            desc = CV_PROFILES.get(key, {}).get("description", "")
            lines.append(f"  {key}: {path}")
            if desc:
                lines.append(f"     {desc}")
        panel("CV INVENTORY", "\n".join(lines), "cyan")
        return

    if args == "stats":
        from optimizer import analyze_effectiveness
        apps_data = None
        try:
            from tracker import list_applications
            apps_data = list_applications()
        except Exception:
            pass
        effect = analyze_effectiveness(apps_data)
        cv_stats = effect.get("cv_stats", {})
        if not cv_stats:
            pr("[yellow]No application stats yet. Apply to some jobs first.[/yellow]")
            return
        lines = ["CV Effectiveness (by interview rate):", ""]
        sorted_cvs = sorted(cv_stats.items(), key=lambda x: -x[1]["interview"])
        for cv, stats in sorted_cvs:
            rate = stats["interview"] / max(stats["total"], 1) * 100
            lines.append(f"  {cv}: {stats['total']} apps, {stats['interview']} interviews ({rate:.0f}%)")
        panel("CV EFFECTIVENESS", "\n".join(lines), "cyan")
        return

    if args.startswith("write"):
        parts = args.split()
        job_idx = None
        base_key = None
        formats = ["latex", "docx"]
        for p in parts[1:]:
            if p.startswith("--base="):
                base_key = p.split("=", 1)[1]
            elif p.startswith("--formats="):
                formats = p.split("=", 1)[1].split(",")
            elif p.startswith("--"):
                continue
            else:
                try:
                    job_idx = int(p) - 1
                except ValueError:
                    pr(f"[red]Unknown argument: {p}[/red]")
                    return

        jobs = load_results()
        valid = [j for j in jobs if is_valid_job(j)]

        if job_idx is not None and 0 <= job_idx < len(valid):
            j = valid[job_idx]
            title = j.get("title", "")
            org = j.get("organization", "")
            desc = j.get("description", "")
        else:
            pr("[yellow]No valid job index. Enter job details manually:[/yellow]")
            title = input("  Job title: ").strip()
            org = input("  Organization: ").strip()
            desc = input("  Description (or leave blank): ").strip()

        if not title:
            pr("[red]Job title required.[/red]")
            return

        if base_key is None:
            base_key = get_base_cv_for_job(title)
            pr(f"[cyan]Auto-selected base CV: [bold]{base_key}[/bold][/cyan]")

        pr(f"[green]Rewriting CV from '{base_key}' for [bold]{title}[/bold] @ {org}...[/green]")
        pr(f"[dim]Formats: {', '.join(formats)}[/dim]")

        try:
            result = rewrite_cv(
                base_cv_key=base_key,
                job_title=title,
                job_description=desc,
                organization=org,
                formats=formats,
            )
            lines = ["[green]✓ CV written successfully![/green]", ""]
            for fmt in formats:
                r = result.get("format_results", {}).get(fmt, {})
                if "error" in r:
                    lines.append(f"[red]  {fmt}: ERROR — {r['error']}[/red]")
                else:
                    for k, v in r.items():
                        if v and Path(v).exists():
                            lines.append(f"  [{fmt}] {k}: {v} ({Path(v).stat().st_size} bytes)")
            panel("CV GENERATED", "\n".join(lines), "green")

        except Exception as e:
            pr(f"[red]Error generating CV: {e}[/red]")
        return

    jobs = load_results()
    if not jobs:
        pr("[yellow]No jobs loaded. Run 'scan' first. Use 'cv list' to see all CVs.[/yellow]")
        return
    if console:
        table = Table(title="CV Recommendations for Loaded Jobs", box=box.ROUNDED)
        table.add_column("#")
        table.add_column("Title", width=40)
        table.add_column("Organization", width=18)
        table.add_column("Best CV")
        table.add_column("Score")
        for i, j in enumerate(jobs[:15], 1):
            rec = recommend_cv(j.get("title", ""), j.get("description", ""))
            table.add_row(str(i), j.get("title", "?")[:40], j.get("organization", "?")[:18],
                         rec["cv_key"], str(rec["match_score"]))
        console.print(table)
    else:
        for i, j in enumerate(jobs[:15], 1):
            rec = recommend_cv(j.get("title", ""), j.get("description", ""))
            print(f"{i}. {j['title'][:45]} | CV: {rec['cv_key']} (score: {rec['match_score']})")


def cmd_help():
    help_text = """
# Job Assistant v2.0 — Your Personalized Job Search Copilot

## Core commands:
| Command | Description |
|---------|-------------|
| `profile` | Show your profile + preferences summary |
| `preferences` | Show/edit your job preferences (remote, salary, stress, etc.) |
| `scan` | Scan job sources (EURAXESS, MUR, Indeed, remote boards, EGU) |
| `rank` | Rank loaded jobs by YOUR preferences |
| `apply` | Apply to a job (track + cover letter) |
| `status` | Show application status |
| `update` | Update application status |

## Analysis & Strategy:
| Command | Description |
|---------|-------------|
| `analyze` / `a` | Analyze how your skills match each job |
| `match` / `m` | Match CVs to found jobs |
| `gaps` | Show skill gaps between your profile and jobs |
| `optimize` | Suggest next best action |
| `digest` | Generate weekly digest |
| `plan` | Generate a full career roadmap with courses & next steps |
| `courses` | List recommended courses |
| `context` | Show saved session context |

## Application Preparation:
| Command | Description |
|---------|-------------|
| `cv [list|stats|write]` | CV management: list, stats, or rewrite+generate PDFs |
| `cv write <N> [--base=key] [--formats=latex,docx]` | Rewrite CV for job #N |
| `suggest` | Find unconventional roles matching your skills |

## How to use:
  1. `preferences` — Set your preferences first
  2. `plan` — Get a personalized career roadmap + courses
  3. `suggest` — Discover roles you haven't considered
  4. `scan` → `rank` → `apply` — Find, prioritize, and apply

## CV Versions:
  - English: Demo_User_CV_English (tech, software)
"""
    if console:
        console.print(Markdown(help_text))
    else:
        print(help_text)


def main():
    if console:
        console.print(Panel.fit(
            "[bold cyan]🛡️  JOB ASSISTANT v1.0[/bold cyan]\n"
            "[dim]Your personalized job search copilot[/dim]",
            border_style="cyan"
        ))
        console.print("Type [bold]help[/bold] for commands, [bold]quit[/bold] to exit.\n")
    else:
        print("=== JOB ASSISTANT v1.0 ===")
        print("Type 'help' for commands, 'quit' to exit.")

    while True:
        try:
            if console:
                cmd = Prompt.ask("[bold cyan]job[/bold cyan]")
            else:
                cmd = input("\njob> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if not cmd:
            continue

        cmd = cmd.lower().strip()

        if cmd in ("quit", "exit", "q"):
            pr("[yellow]Good luck with your search![/yellow]")
            break
        elif cmd == "profile":
            cmd_profile()
        elif cmd.startswith("preferences"):
            args = cmd[len("preferences"):].strip()
            cmd_preferences(args)
        elif cmd == "plan":
            cmd_plan()
        elif cmd == "courses" or cmd.startswith("courses "):
            args = cmd[len("courses"):].strip()
            cmd_courses(args)
        elif cmd == "context":
            cmd_context()
        elif cmd == "scan":
            cmd_scan()
        elif cmd in ("match", "m"):
            cmd_match()
        elif cmd in ("analyze", "a"):
            cmd_analyze()
        elif cmd == "apply":
            cmd_apply()
        elif cmd == "status":
            cmd_status()
        elif cmd == "update":
            cmd_update_status()
        elif cmd == "rank":
            cmd_rank()
        elif cmd == "gaps":
            cmd_gaps()
        elif cmd == "optimize":
            cmd_optimize()
        elif cmd == "digest":
            cmd_digest()
        elif cmd == "suggest":
            cmd_suggest()
        elif cmd.startswith("cv"):
            args = cmd[len("cv"):].strip()
            cmd_cv(args)
        elif cmd in ("help", "h", "?"):
            cmd_help()
        else:
            pr(f"[red]Unknown command: {cmd}. Type 'help'.[/red]")


if __name__ == "__main__":
    main()
