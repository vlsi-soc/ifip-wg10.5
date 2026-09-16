#!/usr/bin/env python3
"""Build the IFIP WG 10.5 static site from data/*.yaml + templates/*.html.

Usage:
    python build.py            # build into _site/
    python build.py --serve    # build, then serve _site/ at http://localhost:8000

To update the live content of the site (add a member, a meeting, a report,
an event, ...), edit the relevant file under data/ and re-run this script -
you never need to touch the HTML templates or copy files onto a server by
hand. Pushing to GitHub triggers an automatic rebuild+deploy (see
.github/workflows/deploy.yml).
"""
import datetime
import http.server
import shutil
import socketserver
import sys
import time
from pathlib import Path

import jinja2
import yaml

ROOT = Path(__file__).parent
DATA_DIR = ROOT / "data"
TEMPLATES_DIR = ROOT / "templates"
OUTPUT_DIR = ROOT / "_site"

# Static content copied as-is into the built site.
STATIC_DIRS = ["css", "js", "img", "file", "Minutes", "Reports"]

MONTHS = [
    "January", "February", "March", "April", "May", "June", "July",
    "August", "September", "October", "November", "December",
]


def load_yaml(name):
    with open(DATA_DIR / f"{name}.yaml", encoding="utf-8") as f:
        return yaml.safe_load(f)


def parse_date(value):
    return datetime.date.fromisoformat(str(value))


def date_long(value):
    """'2025-10-12' -> 'October 12, 2025' (used for meeting minute lines)."""
    d = parse_date(value)
    return f"{MONTHS[d.month - 1]} {d.day}, {d.year}"


def date_euro(value):
    """'2026-10-11' -> '11 October 2026' (used for the upcoming-meeting line)."""
    d = parse_date(value)
    return f"{d.day} {MONTHS[d.month - 1]} {d.year}"


def group_by_year(entries, year_key="year", date_key=None, reverse_entries=True):
    """Group a list of dicts by year_key, sorted by year descending.

    If date_key is given, entries within a year are sorted by that date
    field descending too (used for meetings). Otherwise the original list
    order is preserved within each year (used for reports/events).
    """
    years = {}
    for entry in entries:
        years.setdefault(entry[year_key], []).append(entry)
    groups = []
    for year in sorted(years.keys(), reverse=True):
        group_entries = years[year]
        if date_key:
            group_entries = sorted(group_entries, key=lambda e: e[date_key], reverse=reverse_entries)
        groups.append({"year": year, "entries": group_entries})
    return groups


def _rmtree_with_retry(path, attempts=5, delay=1.5):
    """OneDrive sometimes briefly locks files it just finished syncing into
    _site/ (e.g. the Minutes/Reports copies), which makes rmtree() fail with
    a transient WinError 5. Retry a few times before giving up."""
    for attempt in range(attempts):
        try:
            shutil.rmtree(path)
            return
        except OSError:
            if attempt == attempts - 1:
                raise
            time.sleep(delay)


def build():
    if OUTPUT_DIR.exists():
        _rmtree_with_retry(OUTPUT_DIR)
    OUTPUT_DIR.mkdir(parents=True)

    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(str(TEMPLATES_DIR)),
        autoescape=False,
        trim_blocks=False,
        lstrip_blocks=False,
    )
    env.filters["date_long"] = date_long
    env.filters["date_euro"] = date_euro

    site = load_yaml("site")
    officers = load_yaml("officers")
    members = load_yaml("members")
    meetings = load_yaml("meetings")
    reports = load_yaml("reports")
    events = load_yaml("events")
    competences = load_yaml("competences")
    video = load_yaml("video")

    for m in meetings["meetings"]:
        m["year"] = parse_date(m["date"]).year
    meetings_by_year = group_by_year(meetings["meetings"], date_key="date")

    reports_by_year = group_by_year(reports["reports"])
    past_sponsored_by_year = group_by_year(events["past_sponsored"])
    past_cosponsored_by_year = group_by_year(events["past_cosponsored"])

    build_date = datetime.date.today().strftime(f"%B {datetime.date.today().year}")
    common = {
        "site": site,
        "build_date": build_date,
    }

    pages = {
        "index.html": {"active_page": "index"},
        "officers.html": {"active_page": "officers", "officers": officers},
        "members.html": {"active_page": "members", "members": members},
        "meetings.html": {
            "active_page": "meetings",
            "meetings": meetings,
            "meetings_by_year": meetings_by_year,
        },
        "reports.html": {"active_page": "reports", "reports_by_year": reports_by_year},
        "events.html": {
            "active_page": "events",
            "past_sponsored_by_year": past_sponsored_by_year,
            "past_cosponsored_by_year": past_cosponsored_by_year,
        },
        "competences.html": {"active_page": "competences", "competences": competences},
        "video.html": {"active_page": "video", "videos": video["videos"]},
    }

    for page_name, context in pages.items():
        template = env.get_template(page_name)
        html = template.render(**common, **context)
        (OUTPUT_DIR / page_name).write_text(html, encoding="utf-8")
        print(f"built {page_name}")

    for dirname in STATIC_DIRS:
        src = ROOT / dirname
        if src.exists():
            shutil.copytree(src, OUTPUT_DIR / dirname)
            print(f"copied {dirname}/")

    print(f"\nSite built into {OUTPUT_DIR}")


def serve():
    import os
    os.chdir(OUTPUT_DIR)
    with socketserver.TCPServer(("", 8000), http.server.SimpleHTTPRequestHandler) as httpd:
        print("Serving at http://localhost:8000 (Ctrl+C to stop)")
        httpd.serve_forever()


if __name__ == "__main__":
    build()
    if "--serve" in sys.argv:
        serve()
