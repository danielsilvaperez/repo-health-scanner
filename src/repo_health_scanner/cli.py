from __future__ import annotations

import argparse
import json

from .analyzer import analyze_repo
from .html_report import render_html


def _md(report: dict) -> str:
    lines = []
    lines.append(f"# Repo Health Report: `{report['repo']}`")
    lines.append("")
    lines.append(f"**Score:** {report['total_score']}/{report['max_score']}")
    lines.append("")
    lines.append("## Checks")
    for c in report["checks"]:
        emoji = {"pass": "✅", "warn": "⚠️", "fail": "❌"}.get(c["status"], "•")
        lines.append(f"- {emoji} **{c['name']}**: {c['score']}/{c['max_score']} — {c['details']}")
    lines.append("")
    lines.append("## Recommendations")
    for r in report["recommendations"]:
        lines.append(f"- {r}")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(prog="repohealth", description="GitHub repository health scanner")
    sub = parser.add_subparsers(dest="command", required=True)

    scan = sub.add_parser("scan", help="Scan a GitHub repo (owner/name)")
    scan.add_argument("repo", help="GitHub repo slug, e.g. owner/repo")
    scan.add_argument("--format", choices=["json", "markdown", "html"], default="markdown")
    scan.add_argument("--out", help="Optional output file path")

    args = parser.parse_args()

    if args.command == "scan":
        report = analyze_repo(args.repo).to_dict()
        if args.format == "json":
            output = json.dumps(report, indent=2)
        elif args.format == "html":
            output = render_html(report)
        else:
            output = _md(report)
        if args.out:
            with open(args.out, "w", encoding="utf-8") as f:
                f.write(output)
        else:
            print(output)

    return 0
