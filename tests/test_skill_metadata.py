from __future__ import annotations

import re
from pathlib import Path

import pytest

yaml = pytest.importorskip("yaml")
ROOT = Path(__file__).resolve().parents[1]


def test_skill_frontmatter():
    text = (ROOT / "SKILL.md").read_text(encoding="utf-8")
    match = re.match(r"^---\r?\n(.*?)\r?\n---\r?\n", text, re.S)
    assert match, "SKILL.md must start with YAML frontmatter"
    data = yaml.safe_load(match.group(1))
    assert re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", data["name"])
    assert data["name"] == "oceanography-plotting-style"
    assert len(data["description"]) <= 500
    assert data.get("whenToUse")


def test_required_skill_files():
    required = [
        "SKILL.md",
        "references/style-reference.md",
        "references/data-prep.md",
        "references/figure-recipes.md",
        "scripts/ocean_plot.py",
        "scripts/ocean_data.py",
        "scripts/ocean_spectral.py",
        "scripts/ocean_journal.py",
        "scripts/ocean_access.py",
        "templates/map_panel_grid.py",
        "templates/mixed_panel_grid.py",
    ]
    for relative in required:
        assert (ROOT / relative).is_file(), relative


def test_templates_require_demo_flag():
    for name in ("map_panel_grid.py", "mixed_panel_grid.py"):
        text = (ROOT / "templates" / name).read_text(encoding="utf-8")
        assert '"--demo"' in text
