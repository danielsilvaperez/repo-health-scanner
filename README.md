# Repo Health Scanner

A quick CLI that analyzes a GitHub repository and outputs a **recruiter-facing health score** (0-100) plus concrete fixes.

## What it checks

- README quality signal
- Commit message quality (conventional prefixes)
- CI health (latest GitHub Actions run)
- Issue/PR hygiene (stale backlog detection)
- Branch freshness (stale non-main branches)

## Usage

```bash
# Markdown report
PYTHONPATH=src python -m repo_health_scanner scan danielsilvaperez/resume-generator

# JSON report
PYTHONPATH=src python -m repo_health_scanner scan danielsilvaperez/resume-generator --format json

# Save markdown report
PYTHONPATH=src python -m repo_health_scanner scan danielsilvaperez/resume-generator --out report.md

# Save HTML dashboard report
PYTHONPATH=src python -m repo_health_scanner scan danielsilvaperez/resume-generator --format html --out report.html
```

## Example output

```markdown
# Repo Health Report: `owner/repo`

**Score:** 84/100

## Checks
- ✅ README quality: 18/20 — README present (size=4200 bytes).
- ⚠️ Commit quality: 12/20 — 12/20 recent commits use conventional prefixes.
- ✅ CI health: 20/20 — Latest workflow run succeeded.
- ✅ Issue/PR hygiene: 17/20 — Healthy backlog.
- ⚠️ Branch freshness: 17/20 — 2/8 non-main branches stale >21 days.
```

## Why this project is useful

This gives a fast quality bar for portfolio repos so internship applications can prioritize projects with the strongest engineering signal.

## Notes

- Requires GitHub CLI (`gh`) authenticated (`gh auth status` should pass).
- Works best on public repositories.
