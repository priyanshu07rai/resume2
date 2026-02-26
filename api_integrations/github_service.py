import os
import requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")


def fetch_github_signals(handle):
    """
    Industrial-Grade + Deep GitHub Signal Provider.
    Returns basic metrics AND a rich repo inventory for Groq analysis.
    """
    if not handle:
        return {"exists": False, "status": "skipped", "reasoning": "No handle provided"}

    headers = {}
    if GITHUB_TOKEN:
        headers["Authorization"] = f"token {GITHUB_TOKEN}"

    try:
        # 1. Primary User Data
        user_url  = f"https://api.github.com/users/{handle}"
        user_resp = requests.get(user_url, headers=headers, timeout=10)

        if user_resp.status_code != 200:
            return {"exists": False, "status": "failed", "error": f"GitHub returned {user_resp.status_code}"}

        user_data = user_resp.json()

        # 2. Repository Deep Profile (up to 50 repos)
        repo_url   = f"https://api.github.com/users/{handle}/repos?sort=updated&per_page=50"
        repos_resp = requests.get(repo_url, headers=headers, timeout=10)
        repos      = repos_resp.json() if repos_resp.status_code == 200 else []

        languages         = {}
        activity_index    = 0
        latest_commit     = "1970-01-01T00:00:00Z"
        forked_repo_count = 0
        starred_repo_count = 0
        pinned_repo_topics = set()
        repo_inventory    = []  # Rich repo list for Groq

        for r in repos:
            lang = r.get("language")
            if lang:
                languages[lang] = languages.get(lang, 0) + 1

            if r.get("fork"):
                forked_repo_count += 1
            starred_repo_count += r.get("stargazers_count", 0)

            for topic in r.get("topics", []):
                pinned_repo_topics.add(topic)

            upd = r.get("updated_at")
            if upd and upd > latest_commit:
                latest_commit = upd

            # Build rich repo entry for Groq
            repo_inventory.append({
                "name":        r.get("name"),
                "description": r.get("description") or "",
                "language":    r.get("language") or "Unknown",
                "stars":       r.get("stargazers_count", 0),
                "forks":       r.get("forks_count", 0),
                "is_fork":     r.get("fork", False),
                "topics":      r.get("topics", []),
                "updated_at":  r.get("updated_at", ""),
                "created_at":  r.get("created_at", ""),
                "url":         r.get("html_url", ""),
                "size":        r.get("size", 0),  # KB
                "open_issues": r.get("open_issues_count", 0),
                "has_readme":  _check_readme(handle, r.get("name"), headers)
            })

        # 3. Fetch recent events (for commit activity)
        events_url  = f"https://api.github.com/users/{handle}/events/public?per_page=30"
        events_resp = requests.get(events_url, headers=headers, timeout=10)
        events      = events_resp.json() if events_resp.status_code == 200 and isinstance(events_resp.json(), list) else []

        push_events     = [e for e in events if e.get("type") == "PushEvent"]
        recent_commit_msgs = []
        for ev in push_events[:5]:
            for c in ev.get("payload", {}).get("commits", [])[:2]:
                msg = c.get("message", "")
                if msg:
                    recent_commit_msgs.append(msg[:120])

        # 4. Score Computation
        created_at     = datetime.strptime(user_data["created_at"], "%Y-%m-%dT%H:%M:%SZ")
        age_years      = (datetime.now() - created_at).days / 365
        maturity_score = min(100, round(age_years * 20))

        last_dt            = datetime.strptime(latest_commit, "%Y-%m-%dT%H:%M:%SZ")
        days_since_active  = (datetime.now() - last_dt).days
        activity_score     = max(0, 100 - days_since_active)

        return {
            "exists": True,
            "status": "success",
            "profile": {
                "handle":      handle,
                "public_repos": user_data.get("public_repos", 0),
                "followers":   user_data.get("followers", 0),
                "following":   user_data.get("following", 0),
                "bio":         user_data.get("bio") or "",
                "company":     user_data.get("company") or "",
                "location":    user_data.get("location") or "",
                "blog":        user_data.get("blog") or "",
                "created_at":  user_data.get("created_at"),
                "html_url":    user_data.get("html_url", "")
            },
            "metrics": {
                "languages":               languages,
                "activity_score":          activity_score,
                "account_maturity_score":  maturity_score,
                "repo_count":              user_data.get("public_repos", 0),
                "account_created_year":    created_at.year,
                "last_commit_days_ago":    days_since_active,
                "forked_repo_count":       forked_repo_count,
                "starred_repo_count":      starred_repo_count,
                "pinned_repo_topics":      list(pinned_repo_topics),
                "follower_count":          user_data.get("followers", 0),
                "top_language":            max(languages, key=languages.get) if languages else "Unknown"
            },
            "repo_inventory":    repo_inventory[:20],   # Top 20 repos for Groq
            "recent_commits":    recent_commit_msgs,   # Last 10 commit messages
            "reasoning":         f"GitHub verified: {age_years:.1f}yr tenure, {activity_score}% recent activity."
        }

    except Exception as e:
        print(f"GitHub API Error: {e}")
        return {"exists": None, "status": "error", "error": str(e)}


def _check_readme(handle, repo_name, headers):
    """Quick check whether a repo has a README."""
    try:
        r = requests.get(
            f"https://api.github.com/repos/{handle}/{repo_name}/readme",
            headers=headers, timeout=5
        )
        return r.status_code == 200
    except Exception:
        return False
