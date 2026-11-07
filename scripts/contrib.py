"""Shared helpers: fetch a GitHub user's contribution calendar.

Primary source is the GraphQL API (needs a token in GITHUB_TOKEN / GH_TOKEN).
Without a token we fall back to the public contributions HTML fragment, which is
enough for local previews. Both return a sorted list of (date, count).

In CI (GITHUB_ACTIONS=true) or whenever a token is set, the fallback is never used:
a missing token, an API error or an empty calendar exits non-zero so the workflow
fails and the last good cards stay on the `output` branch.
"""
from __future__ import annotations

import datetime as dt
import json
import os
import re
import sys
import urllib.request

API = "https://api.github.com/graphql"

CALENDAR_QUERY = """
query($login: String!, $from: DateTime!, $to: DateTime!) {
  user(login: $login) {
    createdAt
    contributionsCollection(from: $from, to: $to) {
      contributionCalendar {
        totalContributions
        weeks { contributionDays { date contributionCount } }
      }
    }
  }
}
"""

CREATED_QUERY = "query($login: String!) { user(login: $login) { createdAt } }"


def _token() -> str | None:
    return os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")


def _graphql(query: str, variables: dict, token: str) -> dict:
    body = json.dumps({"query": query, "variables": variables}).encode()
    req = urllib.request.Request(
        API,
        data=body,
        headers={
            "Authorization": f"bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "profile-art-generator",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        payload = json.load(r)
    if payload.get("errors"):
        raise RuntimeError(payload["errors"])
    return payload["data"]


def _year_ranges(start_year: int, today: dt.date):
    for y in range(start_year, today.year + 1):
        start = dt.datetime(y, 1, 1)
        end = min(dt.datetime(y, 12, 31, 23, 59, 59), dt.datetime.combine(today, dt.time(23, 59, 59)))
        yield start, end


def _fetch_graphql(login: str, token: str, all_time: bool, today: dt.date) -> dict[dt.date, int]:
    days: dict[dt.date, int] = {}
    if all_time:
        created = _graphql(CREATED_QUERY, {"login": login}, token)["user"]["createdAt"]
        ranges = list(_year_ranges(int(created[:4]), today))
    else:
        end = dt.datetime.combine(today, dt.time(23, 59, 59))
        ranges = [(end - dt.timedelta(days=364, hours=23, minutes=59, seconds=59), end)]
    for start, end in ranges:
        data = _graphql(
            CALENDAR_QUERY,
            {"login": login, "from": start.isoformat() + "Z", "to": end.isoformat() + "Z"},
            token,
        )
        cal = data["user"]["contributionsCollection"]["contributionCalendar"]
        for week in cal["weeks"]:
            for d in week["contributionDays"]:
                days[dt.date.fromisoformat(d["date"])] = d["contributionCount"]
    return days


# --- token-less fallback (local previews only) -------------------------------
_CELL = re.compile(r'data-date="(\d{4}-\d{2}-\d{2})"[^>]*\bid="([^"]+)"')
_TIP = re.compile(r'<tool-tip[^>]*\bfor="([^"]+)"[^>]*>\s*([^<]*)</tool-tip>')


def _fetch_html(login: str, all_time: bool, today: dt.date) -> dict[dt.date, int]:
    def grab(url: str) -> dict[dt.date, int]:
        req = urllib.request.Request(url, headers={"User-Agent": "profile-art-generator"})
        html = urllib.request.urlopen(req, timeout=30).read().decode("utf-8", "replace")
        tips = {k: v for k, v in _TIP.findall(html)}
        out = {}
        for date, cid in _CELL.findall(html):
            m = re.match(r"(\d+)", tips.get(cid, "").replace(",", ""))
            out[dt.date.fromisoformat(date)] = int(m.group(1)) if m else 0
        return out

    base = f"https://github.com/users/{login}/contributions"
    if not all_time:
        return grab(base)
    days: dict[dt.date, int] = {}
    y = today.year
    while True:
        chunk = grab(f"{base}?from={y}-01-01&to={y}-12-31")
        chunk = {d: c for d, c in chunk.items() if d.year == y}
        # stop at the first past year with no activity (≈ before the account existed)
        if not chunk or (y < today.year and sum(chunk.values()) == 0) or y < 2008:
            break
        days.update(chunk)
        y -= 1
    return days


def fetch_calendar(login: str, all_time: bool = False, today: dt.date | None = None):
    """Return sorted [(date, count)] up to today (inclusive)."""
    today = today or dt.datetime.now(dt.timezone.utc).date()
    token = _token()
    if token:
        try:
            days = _fetch_graphql(login, token, all_time, today)
        except Exception as e:
            sys.exit(f"error: GitHub GraphQL API call failed for {login!r}: {e}")
        if not days:
            sys.exit(f"error: GitHub GraphQL API returned an empty calendar for {login!r}")
    elif os.environ.get("GITHUB_ACTIONS") == "true":
        sys.exit("error: GITHUB_TOKEN is not set; refusing to use the HTML fallback in CI")
    else:
        print("warning: no GITHUB_TOKEN, using the public HTML fallback (local preview only)", file=sys.stderr)
        days = _fetch_html(login, all_time, today)
    return sorted((d, c) for d, c in days.items() if d <= today)


def streaks(days):
    """Compute total, current and longest streak from sorted [(date, count)]."""
    total = sum(c for _, c in days)

    longest = (0, None, None)
    run, run_start = 0, None
    for d, c in days:
        if c > 0:
            if run == 0:
                run_start = d
            run += 1
            if run > longest[0]:
                longest = (run, run_start, d)
        else:
            run = 0

    # current streak: today may still be 0 without breaking it
    cur, cur_start, cur_end = 0, None, None
    idx = len(days) - 1
    if idx >= 0 and days[idx][1] == 0:
        idx -= 1
    while idx >= 0 and days[idx][1] > 0:
        cur += 1
        cur_start = days[idx][0]
        cur_end = cur_end or days[idx][0]
        idx -= 1

    return {
        "total": total,
        "first_day": next((d for d, c in days if c > 0), None),
        "current": (cur, cur_start, cur_end),
        "longest": longest,
    }
