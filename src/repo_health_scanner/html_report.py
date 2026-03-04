from __future__ import annotations

from html import escape


def render_html(report: dict) -> str:
    score = report["total_score"]
    max_score = report["max_score"]
    pct = int((score / max_score) * 100) if max_score else 0

    rows = []
    for c in report["checks"]:
        status_class = {
            "pass": "pass",
            "warn": "warn",
            "fail": "fail",
        }.get(c.get("status"), "warn")
        rows.append(
            f"<tr class='{status_class}'><td>{escape(c['name'])}</td><td>{c['score']}/{c['max_score']}</td><td>{escape(c['details'])}</td></tr>"
        )

    recs = "".join(f"<li>{escape(r)}</li>" for r in report.get("recommendations", []))

    return f"""<!doctype html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
  <title>Repo Health Report - {escape(report['repo'])}</title>
  <style>
    body {{ font-family: Inter, system-ui, -apple-system, Segoe UI, Roboto, sans-serif; margin: 2rem; background:#0b1020; color:#e8ecf3; }}
    .card {{ background:#121a2b; border:1px solid #24314d; border-radius:14px; padding:1rem 1.25rem; margin-bottom:1rem; }}
    .score {{ font-size:1.6rem; font-weight:700; }}
    .muted {{ color:#9fb0d0; }}
    table {{ width:100%; border-collapse: collapse; margin-top: .5rem; }}
    th, td {{ border-bottom:1px solid #253250; text-align:left; padding:.6rem; vertical-align: top; }}
    tr.pass td:first-child::before {{ content:'✅ '; }}
    tr.warn td:first-child::before {{ content:'⚠️ '; }}
    tr.fail td:first-child::before {{ content:'❌ '; }}
    .bar {{ height:10px; background:#1e2a44; border-radius:999px; overflow:hidden; margin-top:.4rem; }}
    .bar > span {{ display:block; height:100%; width:{pct}%; background:linear-gradient(90deg,#00c2ff,#4ade80); }}
    a {{ color:#7dc8ff; }}
  </style>
</head>
<body>
  <div class=\"card\">
    <h1>Repo Health Report</h1>
    <div class=\"muted\">Repository: <code>{escape(report['repo'])}</code></div>
    <div class=\"score\">Score: {score}/{max_score} ({pct}%)</div>
    <div class=\"bar\"><span></span></div>
  </div>

  <div class=\"card\">
    <h2>Checks</h2>
    <table>
      <thead><tr><th>Check</th><th>Score</th><th>Details</th></tr></thead>
      <tbody>
        {''.join(rows)}
      </tbody>
    </table>
  </div>

  <div class=\"card\">
    <h2>Recommendations</h2>
    <ul>{recs}</ul>
  </div>
</body>
</html>
"""
