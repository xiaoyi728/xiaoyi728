#!/usr/bin/env python3
"""从 GitHub API 取真实数据 -> snapshot.json（只用标准库，Actions 里直接跑）。

  export GITHUB_TOKEN=...   # 或本机已 gh auth login
  python3 scripts/fetch_stats.py
"""
import json
import os
import subprocess
import sys
import urllib.error
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
API = "https://api.github.com"
LOGIN = os.environ.get("PROFILE_LOGIN", "xiaoyi728")


def token():
    t = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if t:
        return t
    try:
        return subprocess.check_output(["gh", "auth", "token"], text=True).strip()
    except Exception:
        sys.exit("no token: set GITHUB_TOKEN or run `gh auth login`")


TOK = token()


def req(path, data=None):
    url = path if path.startswith("http") else API + path
    body = json.dumps(data).encode() if data is not None else None
    r = urllib.request.Request(url, data=body, method="POST" if data else "GET")
    r.add_header("Authorization", f"bearer {TOK}")
    r.add_header("Accept", "application/vnd.github+json")
    r.add_header("User-Agent", "profile-readme-builder")
    if body:
        r.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(r, timeout=30) as resp:
        return json.load(resp)


def main():
    user = req(f"/users/{LOGIN}")

    gql = req(
        "/graphql",
        {
            "query": """query($login:String!){
              user(login:$login){
                contributionsCollection{
                  contributionYears
                  contributionCalendar{
                    totalContributions
                    weeks{ contributionDays{ contributionCount } }
                  }
                }
                repositories(first:100,privacy:PUBLIC,ownerAffiliations:OWNER,
                             orderBy:{field:PUSHED_AT,direction:DESC}){
                  nodes{ name isFork stargazerCount }
                }
              }
            }""",
            "variables": {"login": LOGIN},
        },
    )
    if "errors" in gql:
        sys.exit(f"graphql error: {gql['errors']}")

    u = gql["data"]["user"]
    cal = u["contributionsCollection"]["contributionCalendar"]
    repos = [n for n in u["repositories"]["nodes"] if n]

    weeks = [sum(d["contributionCount"] for d in w["contributionDays"]) for w in cal["weeks"]]

    # 语言只统计「自己拥有的非 fork 仓库」，否则 fork 的百万级代码会把比例带偏
    lang = {}
    for r in repos:
        if r["isFork"]:
            continue
        try:
            for k, v in req(f"/repos/{LOGIN}/{r['name']}/languages").items():
                lang[k] = lang.get(k, 0) + v
        except urllib.error.HTTPError as e:
            print(f"skip {r['name']}: {e}", file=sys.stderr)

    snap = {
        "login": LOGIN,
        "name": user.get("name") or LOGIN,
        "followers": user.get("followers", 0),
        "following": user.get("following", 0),
        "publicRepos": user.get("public_repos", 0),
        "stars": sum(r["stargazerCount"] for r in repos),
        "contributions": cal["totalContributions"],
        "years": len(u["contributionsCollection"]["contributionYears"]),
        "languages": dict(sorted(lang.items(), key=lambda kv: -kv[1])),
        "weeks": weeks,
    }
    with open(os.path.join(ROOT, "snapshot.json"), "w", encoding="utf-8") as f:
        json.dump(snap, f, ensure_ascii=False, indent=2)
    print(json.dumps({k: v for k, v in snap.items() if k != "weeks"}, ensure_ascii=False)[:300])


if __name__ == "__main__":
    main()
