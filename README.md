# IFIP Working Group 10.5 website

Source for the WG 10.5 website. The site is generated from plain data files -
**to update the live content, edit a file under `data/`, commit, and push.**
You should never need to edit an HTML file to add a member, a meeting, a
report, or an event.

## How it works

- `data/*.yaml` - the actual content (officers, members, meetings, reports,
  events, competences, videos, site-wide settings). Each file has comments
  at the top explaining its fields.
- `templates/*.html` - Jinja2 templates that lay the data out as HTML. You
  only need to touch these if you're changing the page *design*, not adding
  content.
- `build.py` - reads `data/` + `templates/`, writes the finished site into
  `_site/` (git-ignored, regenerated every time).
- `css/`, `js/`, `img/`, `file/`, `Minutes/`, `Reports/` - static assets and
  historical documents, copied into `_site/` as-is.
- `.github/workflows/deploy.yml` - on every push to `main`, GitHub Actions
  runs `build.py` and publishes `_site/` to GitHub Pages automatically. You
  never need to upload anything by hand.

## Common tasks

**Add a member** - append an entry to the right list in `data/members.yaml`.

**Add a meeting** - append an entry to `meetings:` in `data/meetings.yaml`
(any position - it's sorted and grouped by year automatically at build
time). See the comments at the top of the file for the field reference.

**Add a report** - append an entry to `data/reports.yaml` with the year,
a label, and the file path. Put the actual PDF/DOC file in `Reports/`.

**Add an event** - append an entry to `past_sponsored` or `past_cosponsored`
in `data/events.yaml`. The single "next" flagship event shown on the home
page and the events page is `site.upcoming_event` in `data/site.yaml` -
update that one place when it changes and both pages stay in sync
(the old hand-written site had these drift out of sync for over a year).

**Change contact info / nav / header text** - `data/site.yaml`.

## Building locally

```
pip install -r requirements.txt
python build.py          # writes _site/
python build.py --serve  # also serves it at http://localhost:8000
```

If a rebuild fails with a Windows "Access is denied" error while deleting
`_site/`, it's almost always OneDrive syncing the freshly-copied Minutes/
files it just saw appear - wait a few seconds and run `python build.py`
again.

## What changed from the old hand-written site

- Fixed a set of real bugs found while migrating: broken `Reports\...`
  backslash links (6 report entries), a malformed nested year section in
  `events.html`, missing `alt` text on every officer photo, and a stale
  "Future events" entry that had been ~a year out of date.
- One dangling link could not be fixed, only removed: the March 31, 2025
  Lyon meeting's minutes file was never uploaded to the old site and does
  not exist anywhere in `Minutes/` - `data/meetings.yaml` records this as
  a `note` instead of a dead link. Add the real file + a `minutes_url` entry
  once it turns up.
- Removed ~38MB of exact-duplicate binary attachments (verified via
  checksum) and two unused JS files (`app.js`, `particles.js`) that no page
  referenced.
- `inertial_sensor_plot.html`, `code/` (an old Jupyter notebook + Excel
  source for the competences table), the original hand-written HTML pages,
  and the removed duplicate attachments were all kept on disk under
  `legacy-*/`-prefixed folders / their original names but are git-ignored -
  nothing was deleted, just kept out of the new repo.
