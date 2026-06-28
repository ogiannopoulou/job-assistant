#!/usr/bin/env python3
"""Job Assistant Dashboard — Streamlit UI for your personal job search copilot."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import date, datetime

from profile import load_profile, summarize as profile_summary
from job_scanner import scan_all, save_results, load_results, is_valid_job
from cv_matcher import recommend_cv, CV_PROFILES
from cover_letter_gen import generate as gen_cover_letter
from role_suggester import suggest_roles, add_role, list_suggested, scan_real_jobs_for_role
from tracker import add as track_add, update as track_update, list_applications, summary as track_summary
from skills_analyzer import analyze_job_fit, ALL_SKILLS
from optimizer import generate_digest, suggest_next_action, suggest_skill_gaps, \
    generate_career_plan, suggest_courses
from preferences import show as show_prefs, set_pref as set_preference, list_keys as list_prefs
from job_ranker import rank_jobs, format_ranked, load_inventory as load_skill_inv
from github_integrator import load_results as load_github_repos
from cv_writer import rewrite_cv, auto_rewrite_cv, get_base_cv_for_job, list_available_cvs

st.set_page_config(
    page_title="Job Assistant",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    .big-number { font-size: 2.2rem; font-weight: 700; }
    .medium-number { font-size: 1.4rem; font-weight: 600; }
    .st-emotion-cache-1wivap2 { padding: 1.5rem 1rem; }
    .fit-strong { color: #00cc66; font-weight: 600; }
    .fit-moderate { color: #ffaa00; font-weight: 600; }
    .fit-weak { color: #888; }
    .fit-unlikely { color: #ff4444; }
</style>
""", unsafe_allow_html=True)


def load_profile_data():
    if "profile" not in st.session_state:
        st.session_state.profile = load_profile()
    return st.session_state.profile


def load_job_data():
    if "jobs" not in st.session_state:
        st.session_state.jobs = load_results()
    return st.session_state.jobs


def load_app_data():
    if "apps" not in st.session_state:
        st.session_state.apps = list_applications()
    return st.session_state.apps


def page_dashboard():
    st.title(" Dashboard")
    profile = load_profile_data()
    jobs_raw = load_job_data()
    apps = load_app_data()

    jobs = [j for j in jobs_raw if is_valid_job(j)]
    analyzed = []
    for j in jobs:
        if "_analysis" not in j:
            a = analyze_job_fit(j.get("title", ""), j.get("description", ""))
            j["_analysis"] = a
        analyzed.append(j)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("Jobs Found", len(jobs))
        st.markdown('</div>', unsafe_allow_html=True)
    with col2:
        strong = sum(1 for j in analyzed if j["_analysis"]["fit_label"] == "strong")
        st.metric("Strong Matches", strong, delta=f"{strong/len(analyzed)*100:.0f}%" if analyzed else "")
    with col3:
        st.metric("Applications", len(apps))
    with col4:
        active = sum(1 for a in apps if a.get("status") not in ("rejected", "withdrawn", "accepted"))
        st.metric("Active", active)

    st.divider()

    left, right = st.columns([1.5, 1])

    with left:
        st.subheader("Jobs by Source")
        if analyzed:
            src_counts = {}
            for j in analyzed:
                s = j.get("source", "Unknown")
                src_counts[s] = src_counts.get(s, 0) + 1
            src_df = pd.DataFrame({"Source": list(src_counts.keys()), "Count": list(src_counts.values())})
            fig = px.pie(src_df, values="Count", names="Source",
                         color_discrete_sequence=px.colors.qualitative.Pastel,
                         hole=0.4)
            fig.update_layout(margin=dict(l=20, r=20, t=30, b=20), height=280)
            ev_src = st.plotly_chart(fig, key="src_chart", on_select="rerun", width="stretch")
            if ev_src and ev_src.selection and ev_src.selection.points:
                clicked = ev_src.selection.points[0]
                src_label = clicked.get("label") or clicked.get("name")
                if src_label:
                    st.session_state.dash_src_filter = src_label

    with right:
        st.subheader("Fit Distribution")
        if analyzed:
            fit_counts = {"strong": 0, "moderate": 0, "weak": 0, "unlikely": 0}
            for j in analyzed:
                fit_counts[j["_analysis"]["fit_label"]] += 1
            fit_df = pd.DataFrame({"Fit": list(fit_counts.keys()), "Count": list(fit_counts.values())})
            colors = {"strong": "#00cc66", "moderate": "#ffaa00", "weak": "#888", "unlikely": "#ff4444"}
            fig = px.bar(fit_df, x="Fit", y="Count", color="Fit",
                         color_discrete_map=colors, text="Count")
            fig.update_layout(showlegend=False, margin=dict(l=20, r=20, t=30, b=20), height=280)
            ev_fit = st.plotly_chart(fig, key="fit_chart", on_select="rerun", width="stretch")
            if ev_fit and ev_fit.selection and ev_fit.selection.points:
                clicked = ev_fit.selection.points[0]
                fit_label = clicked.get("x") or clicked.get("label")
                if fit_label:
                    st.session_state.dash_fit_filter = fit_label

    st.divider()

    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader("Application Status")
        if apps:
            status_counts = {}
            for a in apps:
                s = a.get("status", "unknown")
                status_counts[s] = status_counts.get(s, 0) + 1
            status_df = pd.DataFrame({"Status": list(status_counts.keys()), "Count": list(status_counts.values())})
            fig = px.bar(status_df, x="Status", y="Count", color="Status", text="Count")
            fig.update_layout(showlegend=False, margin=dict(l=20, r=20, t=30, b=20), height=250)
            st.plotly_chart(fig, width="stretch")
        else:
            st.info("No applications yet. Use the Job Board to start applying!")

    with col_b:
        st.subheader("Skills Coverage")
        all_matched = {"legal_administrative": set(), "sales_customer_service": set(),
                       "it_tools": set(), "soft_skills": set(), "languages": set(), "sectors": set()}
        for j in analyzed:
            ms = j["_analysis"].get("matched_skills", {})
            for cat, skills in ms.items():
                all_matched[cat].update(skills)

        categories = []
        have = []
        total = []
        for cat, skills in ALL_SKILLS.items():
            if cat == "platforms":
                continue
            categories.append(cat.replace("_", " ").title())
            have.append(len(all_matched.get(cat, set())))
            total.append(len(skills))

        radar_df = pd.DataFrame({
            "Category": categories * 2,
            "Count": have + total,
            "Type": ["Matched"] * len(categories) + ["Available"] * len(categories)
        })
        fig = px.bar(radar_df, x="Category", y="Count", color="Type", barmode="group",
                     color_discrete_sequence=["#00cc66", "#3366cc"])
        fig.update_layout(margin=dict(l=20, r=20, t=30, b=20), height=250, legend=dict(orientation="h", y=1.1))
        ev_skill = st.plotly_chart(fig, key="skill_chart", on_select="rerun", width="stretch")
        if ev_skill and ev_skill.selection and ev_skill.selection.points:
            clicked = ev_skill.selection.points[0]
            cat_label = clicked.get("x") or clicked.get("label")
            if cat_label:
                st.session_state.dash_skill_filter = cat_label

    with st.expander(" Quick Stats"):
        p = profile
        st.markdown(f"""
        - **{p['name']}** — {p['location']}
        - **{len(p['education'])}** degrees, **{len(p['experience'])}** positions
        - **{len(p['cv_files'])}** CV versions available
        - **{len(p['languages'])}** languages spoken
        - Target: {', '.join(p['target_roles'][:3])}...
        """)

        st.markdown("---")
        if apps:
            due = [a for a in apps if a.get("deadline") and a["deadline"] not in ("", "Apply directly", "Check link")]
            if due:
                st.markdown("**Upcoming deadlines:**")
                for a in due[:5]:
                    st.markdown(f"- {a['position'][:50]} @ {a['company']} — _deadline: {a['deadline']}_")

    # ── Click-to-filter: show filtered jobs from chart clicks ──
    dash_src = st.session_state.pop("dash_src_filter", None)
    dash_fit = st.session_state.pop("dash_fit_filter", None)
    dash_skill = st.session_state.pop("dash_skill_filter", None)

    if dash_src or dash_fit or dash_skill:
        st.divider()
        st.subheader(" Filtered Jobs")

        filtered = analyzed
        filter_desc = []
        if dash_src:
            filtered = [j for j in filtered if j.get("source", "") == dash_src]
            filter_desc.append(f"source = **{dash_src}**")
        if dash_fit:
            filtered = [j for j in filtered if j["_analysis"]["fit_label"] == dash_fit]
            filter_desc.append(f"fit = **{dash_fit}**")
        if dash_skill:
            cat_key = dash_skill.lower().replace(" ", "_")
            filtered = [j for j in filtered if any(
                s.lower() in (j.get("title", "") + j.get("description", "")).lower()
                for skills in j["_analysis"].get("matched_skills", {}).values()
                for s in skills
            )]
            filter_desc.append(f"skills in **{dash_skill}**")

        st.markdown(f"  |  ".join(filter_desc) + f" — **{len(filtered)}** jobs")
        st.markdown("Click a chart slice above to filter. Click again or reload to clear.")

        if filtered:
            for j in filtered[:20]:
                a = j["_analysis"]
                fit = a["fit_label"]
                fit_emoji = {"strong": "🟢", "moderate": "🟡", "weak": "⚪", "unlikely": "🔴"}.get(fit, "")
                with st.expander(f"{fit_emoji} **{j.get('title', '?')[:90]}** — {j.get('organization', '?')[:40]}", expanded=False):
                    st.markdown(f"**Source:** {j.get('source', '?')}  |  **Location:** {j.get('location', '?')}  |  **Deadline:** {j.get('deadline', '?')}")
                    if j.get("link"):
                        st.markdown(f"**Link:** [{j['link'][:80]}]({j['link']})")
                    matched = a.get("matched_skills", {})
                    all_ms = [s for skills in matched.values() for s in skills]
                    if all_ms:
                        st.markdown(f"**Matched skills:** {', '.join(all_ms)}")
        else:
            st.info("No jobs match the selected filter.")


def page_job_board():
    st.title(" Job Board")

    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        if st.button(" Run New Scan", width="stretch"):
            with st.spinner("Scanning LinkedIn, INPA, RemoteOK, Himalayas, Remotive for legal/admin/sales jobs..."):
                jobs = scan_all()
                save_results(jobs)
                st.session_state.jobs = jobs
                st.rerun()

    jobs_raw = load_job_data()
    jobs = [j for j in jobs_raw if is_valid_job(j)]

    if not jobs:
        st.warning("No jobs found. Run a scan first!")
        return

    for j in jobs:
        if "_analysis" not in j:
            a = analyze_job_fit(j.get("title", ""), j.get("description", ""))
            j["_analysis"] = a
        if "_cv_recommendation" not in j and "_cv_rec" not in j:
            rec = recommend_cv(j.get("title", ""), j.get("description", ""))
            j["_cv_rec"] = rec

    src_filter = st.multiselect("Source", options=sorted(set(j.get("source", "?") for j in jobs)),
                                 default=[])
    fit_filter = st.multiselect("Fit", options=["strong", "moderate", "weak", "unlikely"], default=[])

    filtered = jobs
    if src_filter:
        filtered = [j for j in filtered if j.get("source") in src_filter]
    if fit_filter:
        filtered = [j for j in filtered if j["_analysis"]["fit_label"] in fit_filter]

    st.markdown(f"**{len(filtered)}** jobs matching filters")

    for i, j in enumerate(filtered):
        a = j["_analysis"]
        rec = j.get("_cv_rec", {})
        fit = a["fit_label"]
        fit_emoji = {"strong": "🟢", "moderate": "🟡", "weak": "⚪", "unlikely": "🔴"}.get(fit, "")
        best_cat = a.get("best_category", "").replace("_", " ").title() if a.get("best_category") else "?"

        with st.expander(f"{fit_emoji} **{j.get('title', '?')[:90]}** — {j.get('organization', '?')[:40]}", expanded=False):
            c1, c2 = st.columns([3, 1])
            with c1:
                st.markdown(f"**Organization:** {j.get('organization', '?')}")
                st.markdown(f"**Location:** {j.get('location', '?')}")
                st.markdown(f"**Source:** {j.get('source', '?')}")
                st.markdown(f"**Deadline:** {j.get('deadline', '?')}")
                if j.get("link"):
                    st.markdown(f"**Link:** [{j['link'][:70]}...]({j['link']})")
                st.markdown(f"**Found:** {j.get('date_found', '?')}")
            with c2:
                fit_style = {"strong": "fit-strong", "moderate": "fit-moderate",
                             "weak": "fit-weak", "unlikely": "fit-unlikely"}
                st.markdown(f'<p class="{fit_style.get(fit, "")}" style="font-size:1.3rem;">{fit.upper()}</p>',
                            unsafe_allow_html=True)
                st.markdown(f"**Category:** {best_cat}")
                st.markdown(f"**Best CV:** {rec.get('cv_key', '?')}")
                st.markdown(f"**Score:** {a.get('best_score', '?')}")

            matched = a.get("matched_skills", {})
            all_ms = []
            for cat, skills in matched.items():
                for s in skills:
                    all_ms.append(s)
            if all_ms:
                st.markdown(f"**Matched skills:** {', '.join(all_ms)}")

            if st.button(f" Apply — {j.get('title', '')[:40]}", key=f"apply_{i}"):
                st.session_state.selected_job = j
                st.info(f"Selected: {j.get('title', '')[:60]} — switch to Cover Letter tab to generate.")


def page_skills():
    st.title(" Skills Analysis")

    jobs_raw = load_job_data()
    jobs = [j for j in jobs_raw if is_valid_job(j)]

    if not jobs:
        st.warning("No jobs loaded. Run a scan first.")
        return

    for j in jobs:
        if "_analysis" not in j:
            a = analyze_job_fit(j.get("title", ""), j.get("description", ""))
            j["_analysis"] = a

    st.subheader("Fit Overview")

    fit_data = []
    for j in jobs:
        a = j["_analysis"]
        fit_data.append({
            "title": j.get("title", "")[:60],
            "org": j.get("organization", "")[:25],
            "fit": a["fit_label"],
            "score": a["best_score"],
            "category": a.get("best_category", "").replace("_", " ").title() if a.get("best_category") else "?",
        })
    fit_df = pd.DataFrame(fit_data)

    colors = {"strong": "#00cc66", "moderate": "#ffaa00", "weak": "#888", "unlikely": "#ff4444"}
    fig = px.bar(fit_df.sort_values("score", ascending=True), y="title", x="score",
                 color="fit", color_discrete_map=colors, orientation="h",
                 hover_data={"org": True, "category": True})
    fig.update_layout(height=max(400, len(fit_df) * 25), margin=dict(l=10, r=10, t=20, b=20),
                      xaxis_title="Match Score", yaxis_title="", showlegend=True)
    st.plotly_chart(fig, width="stretch")

    st.divider()
    st.subheader("Skills Radar (Your Profile vs Job Market)")

    profile = load_profile_data()
    your_skills = {}
    for cat, skills in ALL_SKILLS.items():
        if cat == "platforms":
            continue
        your_skills[cat] = len(skills)

    market_skills = {"legal_administrative": set(), "sales_customer_service": set(),
                     "it_tools": set(), "soft_skills": set(), "languages": set(), "sectors": set()}
    for j in jobs:
        ms = j["_analysis"].get("matched_skills", {})
        for cat, skills in ms.items():
            if cat in market_skills:
                market_skills[cat].update(skills)

    radar_cats = []
    your_vals = []
    market_vals = []
    for cat, total_skills in ALL_SKILLS.items():
        if cat == "platforms":
            continue
        radar_cats.append(cat.replace("_", " ").title())
        your_vals.append(len(total_skills))
        market_vals.append(len(market_skills.get(cat, set())))

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(r=your_vals, theta=radar_cats, fill="toself",
                                   name="Your Skills", line_color="#3366cc"))
    fig.add_trace(go.Scatterpolar(r=market_vals, theta=radar_cats, fill="toself",
                                   name="In Job Listings", line_color="#00cc66"))
    fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, max(your_vals + market_vals) + 2])),
                      height=400, margin=dict(l=40, r=40, t=20, b=20))
    st.plotly_chart(fig, width="stretch")

    st.divider()
    st.subheader("Category Heatmap")

    cat_data = {}
    for j in jobs:
        a = j["_analysis"]
        cat_scores = a.get("category_scores", {})
        for cat, info in cat_scores.items():
            if cat not in cat_data:
                cat_data[cat] = []
            cat_data[cat].append(info["score"])

    heat_rows = []
    for cat, scores in cat_data.items():
        heat_rows.append({
            "Category": cat.replace("_", " ").title(),
            "Avg Score": round(sum(scores) / len(scores), 1),
            "Max Score": max(scores),
            "Jobs Matching": sum(1 for s in scores if s >= 1),
        })
    heat_df = pd.DataFrame(heat_rows).sort_values("Avg Score", ascending=False)

    fig = px.imshow(
        [heat_df["Avg Score"].values],
        x=heat_df["Category"].values,
        y=["Avg Match"],
        color_continuous_scale="Blues",
        text_auto=True,
        aspect="auto",
    )
    fig.update_layout(height=120, margin=dict(l=10, r=10, t=10, b=40))
    st.plotly_chart(fig, width="stretch")

    st.dataframe(heat_df, width="stretch", hide_index=True)

    st.divider()
    st.subheader("Per-Job Skills Breakdown")

    job_titles = [f"{j.get('title', '?')[:70]} — {j.get('organization', '?')[:25]}" for j in jobs]
    selected = st.selectbox("Select a job to inspect", range(len(job_titles)),
                            format_func=lambda i: job_titles[i] if i < len(job_titles) else "")
    if selected < len(job_titles):
        j = jobs[selected]
        a = j["_analysis"]
        st.markdown(f"### {j.get('title', '?')}")
        st.markdown(f"**{j.get('organization', '?')}** — Fit: **{a['fit_label'].upper()}**")

        ms = a.get("matched_skills", {})
        cols = st.columns(len(ms))
        for ci, (cat, skills) in enumerate(ms.items()):
            with cols[ci]:
                st.markdown(f"**{cat.replace('_', ' ').title()}**")
                if skills:
                    for s in skills:
                        st.markdown(f"- {s}")
                else:
                    st.markdown("_(none)_")


def page_tracker():
    st.title(" Application Tracker")

    apps = load_app_data()

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total", len(apps))
    with col2:
        active = sum(1 for a in apps if a.get("status") not in ("rejected", "withdrawn", "accepted"))
        st.metric("Active", active)
    with col3:
        interviewed = sum(1 for a in apps if a.get("status") in ("interview_scheduled", "interviewed"))
        st.metric("Interviews", interviewed)
    with col4:
        accepted = sum(1 for a in apps if a.get("status") == "accepted")
        st.metric("Accepted", accepted)

    st.divider()

    if apps:
        status_order = ["discovered", "preparing", "submitted", "under_review",
                        "interview_scheduled", "interviewed", "accepted", "rejected", "withdrawn"]
        pipeline_data = []
        for s in status_order:
            cnt = sum(1 for a in apps if a.get("status") == s)
            if cnt:
                pipeline_data.append({"Status": s.replace("_", " ").title(), "Count": cnt, "raw": s})

        if pipeline_data:
            df = pd.DataFrame(pipeline_data)
            colors = {
                "discovered": "#aaa", "preparing": "#6699ff", "submitted": "#3366cc",
                "under_review": "#ffaa00", "interview_scheduled": "#ff6600",
                "interviewed": "#cc3300", "accepted": "#00cc66",
                "rejected": "#ff4444", "withdrawn": "#888"
            }
            df["color"] = df["raw"].map(lambda x: colors.get(x, "#aaa"))
            fig = px.funnel(df, x="Count", y="Status", color="raw",
                            color_discrete_map=colors, text="Count")
            fig.update_layout(height=400, showlegend=False, margin=dict(l=10, r=10, t=10, b=10))
            st.plotly_chart(fig, width="stretch")

    st.divider()

    app_tab1, app_tab2 = st.tabs([" All Applications", " + Add New"])

    with app_tab1:
        if apps:
            df_apps = pd.DataFrame(apps)
            display_cols = ["date", "company", "position", "status", "deadline", "cv_used"]
            cols_present = [c for c in display_cols if c in df_apps.columns]
            st.dataframe(df_apps[cols_present], width="stretch", hide_index=True)

            st.subheader("Update Status")
            active_apps = [a for a in apps if a.get("status") not in ("rejected", "withdrawn", "accepted")]
            if active_apps:
                app_options = [f"{a['position'][:50]} @ {a['company']} ({a.get('status', '?')})"
                              for a in active_apps]
                sel_idx = st.selectbox("Select application", range(len(app_options)),
                                       format_func=lambda i: app_options[i])
                new_status = st.selectbox("New status", [
                    "preparing", "submitted", "under_review", "interview_scheduled",
                    "interviewed", "accepted", "rejected", "withdrawn"
                ])
                if st.button("Update Status"):
                    a = active_apps[sel_idx]
                    track_update(a["company"], a["position"], new_status)
                    st.session_state.apps = list_applications()
                    st.success(f"Updated {a['position'][:40]} → {new_status}")
                    st.rerun()
            else:
                st.info("No active applications to update.")
        else:
            st.info("No applications tracked yet.")

    with app_tab2:
        with st.form("add_application"):
            col_a, col_b = st.columns(2)
            with col_a:
                company = st.text_input("Company")
                position = st.text_input("Position")
                source = st.text_input("Source (e.g. EURAXESS, LinkedIn)")
            with col_b:
                cv_options = list(CV_PROFILES.keys())
                cv_used = st.selectbox("CV Used", cv_options)
                deadline = st.date_input("Deadline", value=None)
                link = st.text_input("Link (URL)")
            notes = st.text_area("Notes", height=68)
            submitted = st.form_submit_button(" Add Application", width="stretch")
            if submitted and company and position:
                dl_str = deadline.strftime("%Y-%m-%d") if deadline else ""
                track_add(company, position, source, cv_used, dl_str, "discovered", link, notes)
                st.session_state.apps = list_applications()
                st.success(f"Tracked: {position} @ {company}")
                st.rerun()
            elif submitted:
                st.warning("Company and Position are required.")


def page_profile():
    st.title(" Profile")
    profile = load_profile_data()

    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown(f"### {profile['name']}")
        st.markdown(f" {profile['location']}  ·  {profile['email']}  ·  {profile.get('phone', '')}")
        st.markdown(f"**Languages:** {', '.join(f'{lang} ({prof})' for lang, prof in profile.get('languages', {}).items())}")
    with col2:
        st.markdown("**Target Roles:**")
        for r in profile.get("target_roles", []):
            st.markdown(f"- {r}")

    st.divider()

    edu_tab, exp_tab, skills_tab, cvs_tab = st.tabs(
        ["Education", "Experience", "Skills", "CV Versions"]
    )

    with edu_tab:
        for e in profile.get("education", []):
            with st.container(border=True):
                st.markdown(f"**{e['degree']}**  —  {e['institution']} ({e['year']})")
                if e.get("thesis"):
                    st.markdown(f"_Thesis:_ {e['thesis']}")

    with exp_tab:
        for e in profile.get("experience", []):
            with st.container(border=True):
                st.markdown(f"**{e['role']}** @ {e['institution']}")
                st.markdown(f"_{e.get('period', '')}_")
                if e.get("topics"):
                    st.markdown(f"Topics: {', '.join(e['topics'])}")
                if e.get("collaborators"):
                    st.markdown(f"Collaborators: {', '.join(e['collaborators'])}")

    with skills_tab:
        for cat, skills in profile.get("technical_skills", {}).items():
            st.markdown(f"**{cat.replace('_', ' ').title()}:** {', '.join(skills)}")

        st.divider()
        st.markdown("**Portfolio Projects (Local)**")
        for proj in profile.get("portfolio_projects", []):
            icon = "✅" if proj.get("exists") else "❌"
            st.markdown(f"{icon} **{proj['name']}** — {proj['description']}")
            if proj.get("exists"):
                st.markdown(f"  `{proj['path']}`")

        st.divider()
        st.markdown("**Professional Profiles**")
        st.markdown("- [LinkedIn](#) _(edit in profile)_")
        st.markdown("- [GitHub](#) _(edit in profile)_")

    with cvs_tab:
        cvs = profile.get("cv_files", {})
        st.markdown(f"**{len(cvs)}** CV versions:")
        cols = st.columns(3)
        for i, (key, path) in enumerate(cvs.items()):
            with cols[i % 3]:
                exists = Path(path).exists()
                icon = "✅" if exists else "❌"
                st.markdown(f"{icon} **{key}**")
                st.markdown(f"`{Path(path).name}`")
                if not exists:
                    st.markdown(f"<span style='color:#ff4444;font-size:0.8em;'>missing</span>",
                                unsafe_allow_html=True)

        st.divider()
        st.markdown("**CV Effectiveness**")
        from optimizer import analyze_effectiveness
        apps_data = list_applications()
        effect = analyze_effectiveness(apps_data)
        cv_stats = effect.get("cv_stats", {})
        if cv_stats:
            cv_df = pd.DataFrame([
                {"CV": cv, "Apps": s["total"], "Interviews": s["interview"], "Accepted": s["accepted"]}
                for cv, s in sorted(cv_stats.items(), key=lambda x: -x[1]["total"])
            ])
            st.dataframe(cv_df, hide_index=True, use_container_width=True)
        else:
            st.caption("No application data yet — apply to see which CVs perform best.")


def page_role_suggester():
    st.title(" Role Suggester")
    st.markdown("Roles adjacent to your skills that you haven't considered — **with real job listings**.")

    profile = load_profile_data()
    suggested = suggest_roles(profile)

    if not suggested:
        st.success("You've already covered all adjacent roles in your target list!")
        return

    for i, role in enumerate(suggested):
        with st.expander(f"{i+1}. **{role['title']}**  [{role['sector']}]  — Match: {role['score']}/?", expanded=i == 0):
            c1, c2, c3 = st.columns(3)
            with c1:
                st.markdown(f"💰 **{role['avg_salary_eur']}**")
            with c2:
                st.markdown(f"🌍 **{role['remote']}**")
            with c3:
                st.markdown(f"😌 **{role['stress']}**")

            st.markdown(f"**Why you fit:** {role['why_match']}")
            st.markdown(f"**Skill gaps:** {', '.join(role['skill_gaps'][:5])}")
            st.markdown(f"**1-month prep:** {role['one_month_prep']}")

            # Check if role is already in targets
            already = any(role["title"].lower() in t.lower() for t in profile.get("target_roles", []))
            if not already:
                col_a, col_b = st.columns([1, 5])
                with col_a:
                    if st.button(f"➕ Add to targets", key=f"add_role_{i}"):
                        if add_role(role["title"]):
                            st.success(f"Added '{role['title']}' to target_roles!")
                            st.rerun()
                        else:
                            st.warning("Could not add.")
            else:
                st.info("✅ Already in your target roles")

            # Real job listings for this role
            st.divider()
            st.markdown("** Real listings for this role category:**")
            with st.spinner("Searching job boards..."):
                real_jobs = scan_real_jobs_for_role(role["title"], max_results=4)

            if real_jobs:
                for j in real_jobs:
                    title = j.get("title", "?")
                    org = j.get("organization", "?")
                    loc = j.get("location", "?")
                    link = j.get("link", "")
                    src = j.get("source", "?")
                    st.markdown(f"- **{title}** @ {org} ({loc}) — [{src}]({link})" if link
                                else f"- **{title}** @ {org} ({loc}) — {src}")

            # Always show search links prominently
            from role_suggester import SEARCH_LINKS
            link = SEARCH_LINKS.get(role["title"], "")
            st.markdown("**Search for these roles:**")
            col_l, col_i, col_e = st.columns(3)
            with col_l:
                if link:
                    st.markdown(f"[🔍 Search LinkedIn](https://www.{link})")
            with col_i:
                q = role['title'].split('/')[0].replace('(', '').replace(')', '')
                st.markdown(f"[🔍 Search Indeed](https://www.indeed.com/jobs?q={q.replace(' ', '+')})")
            with col_e:
                if any(w in role['title'].lower() for w in ['scientist', 'research', 'engineer']):
                    st.markdown(f"[🔍 Search EURAXESS](https://euraxess.ec.europa.eu/jobs/search?keywords={q.replace(' ', '+')})")

    st.divider()
    st.markdown("**Want to see more roles?** Run `profile` → target_roles in the CLI to review your current list.")


def _text_to_pdf(text: str, filename: str = "cover_letter.pdf") -> bytes:
    """Convert cover letter text to a professional PDF with DejaVu font and proper layout."""
    from fpdf import FPDF
    from io import BytesIO

    FONT_DIR = "/usr/share/fonts/truetype/dejavu"

    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=22)
    pdf.set_margins(24, 18, 24)

    pdf.add_font("DejaVu", "", f"{FONT_DIR}/DejaVuSans.ttf", uni=True)
    pdf.add_font("DejaVu", "B", f"{FONT_DIR}/DejaVuSans-Bold.ttf", uni=True)
    pdf.add_font("DejaVuSerif", "", f"{FONT_DIR}/DejaVuSerif.ttf", uni=True)
    pdf.add_font("DejaVuSerif", "B", f"{FONT_DIR}/DejaVuSerif-Bold.ttf", uni=True)

    page_w = pdf.w - pdf.l_margin - pdf.r_margin

    # Sender block
    pdf.set_font("DejaVu", "B", 12)
    profile = load_profile_data()
    sender_name = profile.get("name", "Your Name")
    sender_email = profile.get("email", "email@example.com")
    sender_phone = profile.get("phone", "")
    sender_location = profile.get("location", "")
    contact = "  |  ".join(filter(None, [sender_email, sender_phone]))
    pdf.cell(0, 7, sender_name, new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("DejaVu", "", 8.5)
    pdf.set_text_color(100, 100, 100)
    if contact:
        pdf.cell(0, 4.5, contact, new_x="LMARGIN", new_y="NEXT")
    if sender_location:
        pdf.cell(0, 4.5, sender_location, new_x="LMARGIN", new_y="NEXT")
    pdf.set_text_color(0, 0, 0)

    # Horizontal rule
    pdf.ln(3)
    pdf.set_draw_color(200, 200, 200)
    pdf.line(pdf.l_margin, pdf.get_y(), pdf.w - pdf.r_margin, pdf.get_y())
    pdf.ln(6)

    # Parse and render body
    pdf.set_font("DejaVu", "", 10.5)
    line_h = 5.8

    blocks = text.strip().split("\n\n")
    for i, block in enumerate(blocks):
        block = block.strip()
        if not block:
            continue

        lines = block.split("\n")

        # Subject line (starts with "Subject:")
        if lines[0].startswith("Subject:"):
            pdf.set_font("DejaVu", "B", 10.5)
            pdf.multi_cell(0, line_h, lines[0], align="L")
            pdf.set_font("DejaVu", "", 10.5)
            for line in lines[1:]:
                pdf.multi_cell(0, line_h, line, align="L")
            pdf.ln(2)
            continue

        # Salutation (single line ending with comma)
        if len(lines) == 1 and lines[0].strip().endswith(","):
            pdf.multi_cell(0, line_h, lines[0], align="L")
            pdf.ln(1)
            continue

        # Closing / Signature block
        if lines[0].strip().startswith("Best regards") or lines[0].strip().startswith("Sincerely"):
            pdf.ln(3)
            for line in lines:
                pdf.multi_cell(0, line_h, line, align="L")
            continue

        # Regular paragraph
        para_text = " ".join(line.strip() for line in lines if line.strip())
        if para_text:
            pdf.multi_cell(0, line_h, para_text, align="L")
            pdf.ln(2)

    buf = BytesIO()
    pdf.output(buf)
    return buf.getvalue()


def _autofill_from_job():
    """Callback: when a job is picked from the selectbox, fill form fields."""
    picked = st.session_state.cl_selector
    if picked == "— Custom entry —":
        return
    jobs_raw = load_job_data()
    jobs = [j for j in jobs_raw if is_valid_job(j)]
    job_options = [f"{j.get('title', '?')[:80]} — {j.get('organization', '?')[:30]}" for j in jobs]
    if picked in job_options:
        idx = job_options.index(picked)
        j = jobs[idx]
        st.session_state["cl_title"] = j.get("title", "")
        st.session_state["cl_company"] = j.get("organization", "")
        st.session_state["cl_source"] = j.get("source", "website")


def page_cover_letter():
    st.title(" Cover Letter Generator v2")

    profile = load_profile_data()

    jobs_raw = load_job_data()
    jobs = [j for j in jobs_raw if is_valid_job(j)]

    if "cl_content" not in st.session_state:
        st.session_state.cl_content = ""
    if "cl_title" not in st.session_state:
        st.session_state.cl_title = ""
    if "cl_company" not in st.session_state:
        st.session_state.cl_company = ""
    if "cl_source" not in st.session_state:
        st.session_state.cl_source = "website"
    if "cl_style" not in st.session_state:
        st.session_state.cl_style = "auto"

    # Job picker — outside form so it can update session state freely
    if jobs:
        job_options = [f"{j.get('title', '?')[:80]} — {j.get('organization', '?')[:30]}" for j in jobs]
        st.selectbox("Pick from scanned jobs (auto-fills below)",
                     ["— Custom entry —"] + job_options,
                     key="cl_selector", on_change=_autofill_from_job)

    with st.form("cl_form"):
        col_a, col_b = st.columns(2)
        with col_a:
            st.text_input("Position Title", key="cl_title")
            st.text_input("Company", key="cl_company")

        with col_b:
            st.text_input("Source (advertised on)", key="cl_source")
            st.selectbox("Writing Style", ["auto", "professional", "research", "industry", "concise"],
                          key="cl_style",
                          help="auto detects from job title; research for academic, industry for engineering, concise for data")
            st.text_area("Custom paragraph (optional)",
                          placeholder="Add a tailored paragraph about why you're a good fit...",
                          height=100, key="cl_custom_par")
            st.text_input("Why this company? (optional)",
                           placeholder="e.g. its leadership in aerospace", key="cl_company_reason")

        submitted = st.form_submit_button(" Generate Cover Letter", width="stretch")

    if submitted:
        title = st.session_state.get("cl_title", "")
        company = st.session_state.get("cl_company", "")
        source = st.session_state.get("cl_source", "website")
        style = st.session_state.get("cl_style", "auto")
        custom_par = st.session_state.get("cl_custom_par", "")
        company_reason = st.session_state.get("cl_company_reason", "")

        if not title or not company:
            st.warning("Position Title and Company are required.")
        else:
            try:
                content = gen_cover_letter(title, company, source,
                                            custom_paragraph=custom_par,
                                            company_reason=company_reason,
                                            style=style,
                                            job_description="",
                                            output_dir=None)
                st.session_state.cl_content = content
                st.session_state.cl_style_used = style
            except Exception as e:
                st.error(f"Error generating cover letter: {e}")

    if st.session_state.cl_content:
        st.divider()
        st.subheader(" Edit & Export")

        edited = st.text_area("Edit your cover letter below",
                               value=st.session_state.cl_content,
                               height=400,
                               key="cl_editor")

        col_d1, col_d2, col_d3 = st.columns([1, 1, 3])
        with col_d1:
            safe_name = "cover_letter.txt"
            st.download_button(" Download .txt", edited,
                                file_name=safe_name, mime="text/plain",
                                use_container_width=True)
        with col_d2:
            pdf_bytes = _text_to_pdf(edited, "cover_letter.pdf")
            st.download_button(" Download PDF", pdf_bytes,
                                file_name="cover_letter.pdf",
                                mime="application/pdf",
                                use_container_width=True)

        title = st.session_state.get("cl_title", "")
        rec = recommend_cv(title, "")
        st.info(f" Recommended CV: **{rec['cv_key']}** ({rec['cv_path']})")



def page_cv_writer():
    st.title(" CV Writer")
    st.markdown("Rewrite any CV to match a target job — outputs **LaTeX→PDF** and/or **DOCX→PDF**.")

    profile = load_profile_data()
    jobs_raw = load_job_data()
    jobs = [j for j in jobs_raw if is_valid_job(j)]

    tab1, tab2 = st.tabs([" From Scanned Job", " Custom Entry"])

    with tab1:
        if jobs:
            job_options = [f"{i}. {j.get('title', '?')[:70]} @ {j.get('organization', '?')[:25]}"
                           for i, j in enumerate(jobs)]
            sel_idx = st.selectbox("Select a job", range(len(job_options)),
                                    format_func=lambda i: job_options[i] if i < len(job_options) else "",
                                    key="cvw_job_idx")
            j = jobs[sel_idx]
            st.markdown(f"**{j.get('title', '?')}**")
            st.markdown(f"{j.get('organization', '?')} — {j.get('location', '?')}")

            with st.expander("Job Description"):
                desc = j.get("description", "No description available.")
                st.text(desc[:2000] if desc else "N/A")
        else:
            st.warning("No jobs found. Run a scan first.")
            st.stop()

    with tab2:
        j = {}
        j["title"] = st.text_input("Job Title", key="cvw_title")
        j["organization"] = st.text_input("Organization", key="cvw_org")
        j["description"] = st.text_area("Description (optional)", key="cvw_desc", height=150)

    # Common controls
    st.divider()

    col1, col2, col3 = st.columns(3)
    with col1:
        avail_cvs = list_available_cvs()
        suggested = get_base_cv_for_job(j.get("title", ""))
        cv_options = avail_cvs
        default_idx = cv_options.index(suggested) if suggested in cv_options else 0
        base_cv = st.selectbox("Base CV", cv_options, index=default_idx,
                                help="Which CV to use as starting point")
    with col2:
        fmt_options = ["latex", "docx", "both"]
        fmt_choice = st.selectbox("Output formats", fmt_options, index=2,
                                   help="both = LaTeX PDF + DOCX PDF")
    with col3:
        st.markdown("### &nbsp;")
        if st.button(" Generate Optimized CV", width="stretch", type="primary"):
            title = j.get("title", "")
            org = j.get("organization", "")
            desc = j.get("description", "")

            if not title:
                st.warning("Job title is required.")
                st.stop()

            formats = ["latex", "docx"] if fmt_choice == "both" else [fmt_choice]
            st.info(f"Rewriting **{base_cv}** CV for **{title}** @ {org}...")

            with st.spinner("Generating CV (LaTeX compilation + DOCX conversion)..."):
                try:
                    result = rewrite_cv(
                        base_cv_key=base_cv,
                        job_title=title,
                        job_description=desc or "",
                        organization=org,
                        formats=formats,
                    )
                    st.success("CV generated successfully!")

                    for fmt in formats:
                        r = result.get("format_results", {}).get(fmt, {})
                        if "error" in r:
                            st.error(f"{fmt}: {r['error']}")
                        else:
                            for ext, path in r.items():
                                if Path(path).exists():
                                    data = Path(path).read_bytes()
                                    filename = Path(path).name
                                    mime = {"pdf": "application/pdf", "tex": "text/plain",
                                           "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"}.get(ext, "")
                                    st.download_button(
                                        f" Download {fmt.upper()} {ext.upper()} ({Path(path).stat().st_size//1024} KB)",
                                        data=data, file_name=filename, mime=mime,
                                        use_container_width=True,
                                    )

                    # Show LaTeX preview
                    if "latex_source" in result:
                        with st.expander(" LaTeX Source Preview", expanded=False):
                            st.code(result["latex_source"], language="latex")

                except Exception as e:
                    st.error(f"Error: {e}")

    st.divider()
    st.markdown("**Tip:** You can also use `cv write <N>` in the CLI with `--base` and `--formats` flags.")


def page_optimizer():
    st.title(" Optimizer")
    
    tab1, tab2, tab3 = st.tabs([" Next Action", " Skill Gaps", " Weekly Digest"])
    
    with tab1:
        st.subheader("Recommended Next Action")
        action = suggest_next_action()
        priority = action.get("priority", "low")
        color = {"high": "red", "medium": "orange", "low": "gray"}.get(priority, "gray")
        st.markdown(f'<p style="color:{color};font-size:1.3rem;font-weight:600;">[{priority.upper()}] {action["message"]}</p>',
                    unsafe_allow_html=True)
        st.markdown(f'**Detail:** {action.get("detail", "")}')
        
        st.divider()
        st.subheader("Ranked Jobs (Live)")
        jobs_raw = load_job_data()
        valid = [j for j in jobs_raw if is_valid_job(j)]
        if valid:
            ranked = rank_jobs(valid)
            for i, j in enumerate(ranked[:10]):
                s = j.get("_scores", {})
                total = s.get("total_score", 0)
                with st.container(border=True):
                    c1, c2 = st.columns([4, 1])
                    with c1:
                        st.markdown(f"**{i+1}. {j.get('title', '?')[:70]}**")
                        st.markdown(f"{j.get('organization', '?')} — {j.get('source', '?')}")
                    with c2:
                        st.markdown(f'<p style="font-size:1.5rem;font-weight:700;">{total}</p>', unsafe_allow_html=True)
                    if st.button(f"Apply →", key=f"opt_apply_{i}"):
                        st.session_state.selected_job = j
                        st.switch_page("dashboard")
        else:
            st.info("Run a job scan first.")
    
    with tab2:
        st.subheader("Skill Gaps")
        inv = load_skill_inv()
        gaps = suggest_skill_gaps(inv) if inv else []
        if gaps:
            for g in gaps:
                sev = g.get("severity", "low")
                icon = {"high": "🔴", "medium": "🟡", "low": "⚪"}.get(sev, "⚪")
                st.markdown(f"{icon} **{g['skill']}** — {g['message']}")
        else:
            st.success("No skill gaps detected!")
        
        st.divider()
        st.subheader("Your Skill Inventory")
        if inv:
            cats = {}
            for name, data in inv.items():
                for cat in data.get("categories", []):
                    cats.setdefault(cat, []).append(name)
            for cat, skills in sorted(cats.items(), key=lambda x: -len(x[1])):
                with st.expander(f"{cat.replace('_', ' ').title()} ({len(skills)} skills)"):
                    for s in skills:
                        d = inv.get(s, {})
                        st.markdown(f"- **{s}** — {d.get('project_count', 0)} projects, {d.get('cv_count', 0)} CVs")
    
    with tab3:
        st.subheader("Weekly Digest")
        digest = generate_digest()
        st.text(digest)
        if st.button(" Regenerate"):
            st.rerun()

def page_preferences():
    st.title(" Preferences")

    tab1, tab2 = st.tabs([" Current Preferences", " Edit Preferences"])

    with tab1:
        st.subheader("Your Preferences")
        prefs_text = show_prefs()
        st.text(prefs_text)

    with tab2:
        st.subheader("Change a Preference")
        valid_keys = list(list_prefs().split("\n"))
        with st.form("pref_form"):
            if "pref_keys" not in st.session_state:
                from profile import RAW_PROFILE
                st.session_state.pref_keys = list(RAW_PROFILE.get("preferences", {}).keys())
            key = st.selectbox("Preference", st.session_state.pref_keys)
            value = st.text_input("New value", placeholder="e.g. True, 55000, 4")
            submitted = st.form_submit_button(" Update")
            if submitted and key and value:
                result = set_preference(key, value)
                st.success(result)
                st.rerun()

    st.divider()
    st.markdown("**Tip:** Run `plan` in the Career Plan tab to see how your preferences shape your recommended path.")


def page_career_plan():
    st.title(" Career Plan")

    if st.button(" Generate / Refresh Plan"):
        st.session_state.plan = generate_career_plan()
        st.rerun()

    if "plan" not in st.session_state:
        st.session_state.plan = generate_career_plan()

    st.markdown(st.session_state.plan)


def page_courses():
    st.title(" Courses")

    from optimizer import ITALY_CAREER_PATHS as career_paths

    # Path selector
    path_titles = [p["title"] for p in career_paths]
    selected = st.selectbox("Career Path", ["All"] + path_titles)

    if selected == "All":
        result = suggest_courses()
    else:
        result = suggest_courses(selected)

    st.markdown(result)


def page_session_context():
    st.title(" Session Context")

    ctx_path = Path(__file__).parent / "data" / "session_context.json"
    if not ctx_path.exists():
        st.warning("No session context saved yet.")
        return

    import json
    with open(ctx_path) as f:
        ctx = json.load(f)

    with st.expander(" Your Priorities", expanded=True):
        for d in ctx.get("critical_context", {}).get("desires", ["No priorities saved yet."]):
            st.markdown(f"- {d}")

    decisions = ctx.get("decisions_made", {})
    if decisions:
        with st.expander(" Decisions Made", expanded=False):
            for k, v in decisions.items():
                st.markdown(f"- **{k.replace('_', ' ').title()}**: {v}")


def main():
    profile = load_profile_data()

    st.sidebar.markdown(f"###  Job Assistant")
    st.sidebar.markdown(f"_{profile['name']}_")
    st.sidebar.divider()

    page = st.sidebar.radio(
        "Navigate",
        [" Dashboard", " Job Board", " Skills Analysis", " Tracker",
         " Profile", " Preferences", " Career Plan", " Courses",
         " Session Context", " Role Suggester", " Cover Letter", " CV Writer", " Optimizer"],
        index=0,
        label_visibility="collapsed",
    )

    st.sidebar.divider()

    jobs = load_job_data()
    apps = load_app_data()
    valid_jobs = [j for j in jobs if is_valid_job(j)]
    st.sidebar.markdown(f"Jobs: **{len(valid_jobs)}** | Apps: **{len(apps)}**")

    st.sidebar.markdown("---")
    st.sidebar.markdown("`v1.0`", help="Job Assistant Dashboard")

    pages = {
        " Dashboard": page_dashboard,
        " Job Board": page_job_board,
        " Skills Analysis": page_skills,
        " Tracker": page_tracker,
        " Profile": page_profile,
        " Preferences": page_preferences,
        " Career Plan": page_career_plan,
        " Courses": page_courses,
        " Session Context": page_session_context,
        " Role Suggester": page_role_suggester,
        " Cover Letter": page_cover_letter,
        " CV Writer": page_cv_writer,
        " Optimizer": page_optimizer,
    }

    pages[page]()


if __name__ == "__main__":
    main()
