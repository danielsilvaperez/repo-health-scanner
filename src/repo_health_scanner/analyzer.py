from __future__ import annotations

import json
import re
import subprocess
from collections import Counter
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Any

COMMIT_PREFIXES = ("feat:", "fix:", "docs:", "chore:", "refactor:", "test:", "perf:")


@dataclass
class CheckResult:
    name: str
    score: int
    max_score: int
    status: str
    details: str


@dataclass
class RepoHealthReport:
    repo: str
    total_score: int
    max_score: int
    checks: list[CheckResult]
    recommendations: list[str]

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["checks"] = [asdict(c) for c in self.checks]
        return data


def run_gh(args: list[str]) -> Any:
    cmd = ["gh", "api", *args]
    out = subprocess.check_output(cmd, text=True)
    return json.loads(out)


def score_readme(repo_data: dict[str, Any], contents: list[dict[str, Any]]) -> CheckResult:
    readme = next((c for c in contents if c.get("name", "").lower().startswith("readme")), None)
    if not readme:
        return CheckResult("README quality", 0, 20, "fail", "No README file found.")

    score = 10
    size = readme.get("size", 0)
    if size > 2000:
        score += 5
    if repo_data.get("homepage"):
        score += 2
    if repo_data.get("description"):
        score += 3

    status = "pass" if score >= 16 else "warn"
    return CheckResult("README quality", min(score, 20), 20, status, f"README present (size={size} bytes).")


def score_commits(repo: str) -> CheckResult:
    commits = run_gh([f"repos/{repo}/commits?per_page=20"])
    if not commits:
        return CheckResult("Commit quality", 0, 20, "fail", "No commits found.")

    msgs = [c["commit"]["message"].splitlines()[0].strip() for c in commits]
    good = sum(1 for m in msgs if m.lower().startswith(COMMIT_PREFIXES))
    ratio = good / len(msgs)

    score = int(round(ratio * 20))
    status = "pass" if score >= 14 else "warn" if score >= 8 else "fail"
    return CheckResult(
        "Commit quality",
        score,
        20,
        status,
        f"{good}/{len(msgs)} recent commits use conventional prefixes.",
    )


def score_ci(repo: str) -> CheckResult:
    runs = run_gh([f"repos/{repo}/actions/runs?per_page=5"])
    workflow_runs = runs.get("workflow_runs", [])
    if not workflow_runs:
        return CheckResult("CI health", 5, 20, "warn", "No GitHub Actions runs found.")

    latest = workflow_runs[0]
    conclusion = latest.get("conclusion") or "unknown"
    if conclusion == "success":
        return CheckResult("CI health", 20, 20, "pass", "Latest workflow run succeeded.")
    if conclusion == "failure":
        return CheckResult("CI health", 4, 20, "fail", "Latest workflow run failed.")
    return CheckResult("CI health", 10, 20, "warn", f"Latest workflow conclusion: {conclusion}.")


def score_issues_prs(repo: str) -> CheckResult:
    prs = run_gh([f"repos/{repo}/pulls?state=open&per_page=30"])
    issues = run_gh([f"repos/{repo}/issues?state=open&per_page=30"])
    issue_only = [i for i in issues if "pull_request" not in i]

    score = 20
    details = []
    if len(prs) > 10:
        score -= 6
        details.append(f"{len(prs)} open PRs")
    if len(issue_only) > 20:
        score -= 6
        details.append(f"{len(issue_only)} open issues")

    stale_prs = sum(1 for pr in prs if _is_stale(pr.get("updated_at"), 14))
    stale_issues = sum(1 for i in issue_only if _is_stale(i.get("updated_at"), 21))
    if stale_prs:
        score -= min(6, stale_prs)
        details.append(f"{stale_prs} stale PRs")
    if stale_issues:
        score -= min(6, stale_issues)
        details.append(f"{stale_issues} stale issues")

    score = max(0, score)
    status = "pass" if score >= 15 else "warn" if score >= 8 else "fail"
    return CheckResult("Issue/PR hygiene", score, 20, status, ", ".join(details) or "Healthy backlog.")


def score_branches(repo: str) -> CheckResult:
    branches = run_gh([f"repos/{repo}/branches?per_page=100"])
    non_main = [b for b in branches if b.get("name") not in {"main", "master"}]
    stale = 0
    for b in non_main[:20]:
        sha = b["commit"]["sha"]
        c = run_gh([f"repos/{repo}/commits/{sha}"])
        if _is_stale(c.get("commit", {}).get("committer", {}).get("date"), 21):
            stale += 1

    if not non_main:
        return CheckResult("Branch freshness", 20, 20, "pass", "No long-lived feature branches.")

    score = max(0, 20 - min(10, stale * 2))
    status = "pass" if stale == 0 else "warn" if stale < 4 else "fail"
    return CheckResult("Branch freshness", score, 20, status, f"{stale}/{len(non_main)} non-main branches stale >21 days.")


def analyze_repo(repo: str) -> RepoHealthReport:
    repo_data = run_gh([f"repos/{repo}"])
    contents = run_gh([f"repos/{repo}/contents"])

    checks = [
        score_readme(repo_data, contents if isinstance(contents, list) else []),
        score_commits(repo),
        score_ci(repo),
        score_issues_prs(repo),
        score_branches(repo),
    ]
    total = sum(c.score for c in checks)
    max_score = sum(c.max_score for c in checks)

    recs: list[str] = []
    by_name = {c.name: c for c in checks}

    if by_name["Commit quality"].score < 14:
        recs.append("Adopt conventional commit prefixes consistently (feat/fix/docs/chore).")
    if by_name["CI health"].status == "fail":
        recs.append("Fix the latest failing GitHub Action before your next application push.")
    if by_name["README quality"].score < 16:
        recs.append("Upgrade README with problem, impact, setup, demo, and architecture sections.")
    if by_name["Issue/PR hygiene"].score < 15:
        recs.append("Close or label stale issues/PRs to show active maintenance.")
    if by_name["Branch freshness"].status != "pass":
        recs.append("Merge or delete stale feature branches older than 3 weeks.")

    if not recs:
        recs.append("Repo health looks strong. Keep shipping scoped commits with clear impact.")

    return RepoHealthReport(repo=repo, total_score=total, max_score=max_score, checks=checks, recommendations=recs)


def _is_stale(iso_date: str | None, days: int) -> bool:
    if not iso_date:
        return False
    dt = datetime.fromisoformat(iso_date.replace("Z", "+00:00"))
    delta = datetime.now(timezone.utc) - dt
    return delta.days > days
