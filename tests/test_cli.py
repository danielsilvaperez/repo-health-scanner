from repo_health_scanner.cli import _md


def test_markdown_render_contains_score():
    report = {
        "repo": "x/y",
        "total_score": 80,
        "max_score": 100,
        "checks": [{"name": "CI health", "score": 20, "max_score": 20, "status": "pass", "details": "ok"}],
        "recommendations": ["keep going"],
    }
    out = _md(report)
    assert "80/100" in out
    assert "CI health" in out
