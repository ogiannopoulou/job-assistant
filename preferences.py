"""Preferences — view and edit your job search preferences."""

from profile import get_preferences, set_preference, RAW_PROFILE, summarize_preferences

PREF_DESCRIPTIONS = {
    "remote": "Only remote/hybrid jobs?",
    "min_salary_eur": "Minimum annual salary in EUR",
    "eu_mobility": "Open to working anywhere in EU?",
    "location_flexibility": "Where? (italy_greece / eu / anywhere)",
    "work_life_balance": "Work-life balance priority (1=doesn't matter, 5=critical)",
    "stress_tolerance": "Stress tolerance (1=avoid all stress, 5=thrive under pressure)",
    "family_proximity": "How important is being near family? (1-5)",
    "travel_opportunity": "Desire for travel (1=never, 5=as much as possible)",
    "prefer_industry": "Prefer industry over academia?",
    "prefer_remote_first": "Prefer remote-first companies?",
    "prefer_no_weekends": "Want weekends off?",
    "prefer_flexible_hours": "Want flexible hours?",
    "max_commute_minutes": "Max commute in minutes (0 = must be remote)",
}


def show():
    prefs = get_preferences()
    lines = summarize_preferences(prefs)
    return "\n".join(lines)


def set_pref(key: str, value: str) -> str:
    valid = RAW_PROFILE.get("preferences", {}).keys()
    if key not in valid:
        descs = "\n".join(f"  {k}: {v}" for k, v in PREF_DESCRIPTIONS.items())
        return f"Unknown preference '{key}'. Valid:\n{descs}"
    if set_preference(key, value):
        return f"✅ {key} = {value}"
    return f"Failed to set {key}"


def list_keys():
    lines = ["Available preferences:", ""]
    for k, v in PREF_DESCRIPTIONS.items():
        default = RAW_PROFILE.get("preferences", {}).get(k, "?")
        lines.append(f"  {k}: {v}  (default: {default})")
    return "\n".join(lines)


if __name__ == "__main__":
    import sys
    if len(sys.argv) == 1:
        print(show())
    elif sys.argv[1] == "list":
        print(list_keys())
    elif len(sys.argv) == 3:
        print(set_pref(sys.argv[1], sys.argv[2]))
    else:
        print("Usage: python preferences.py [list | <key> <value>]")
