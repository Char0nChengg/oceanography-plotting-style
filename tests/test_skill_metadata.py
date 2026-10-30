from __future__ import annotations

import re
from pathlib import Path

import pytest

import ocean_plot

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
        "README.md",
        "README.en.md",
        "CHANGELOG.md",
        "docs/style-philosophy.md",
        "docs/style-philosophy.en.md",
        "docs/tutorials/README.md",
        ".github/workflows/ci.yml",
        ".github/workflows/release.yml",
        "references/figure-catalog.md",
        "references/netcdf-profiles.md",
        "references/style-reference.md",
        "references/data-prep.md",
        "references/figure-recipes.md",
        "references/recipes/README.md",
        "scripts/ocean_plot.py",
        "scripts/ocean_vocab.py",
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


def test_version_is_consistent():
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    match = re.search(r'^version = "([^"]+)"', pyproject, re.M)
    assert match, "pyproject.toml must define a version"
    version = match.group(1)
    assert version == ocean_plot.__version__
    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    assert f"## [{version}]" in changelog


def test_relative_links_exist():
    documents = [
        ROOT / "README.md",
        ROOT / "README.en.md",
        ROOT / "SKILL.md",
        *sorted((ROOT / "docs").rglob("*.md")),
        *sorted((ROOT / "references").rglob("*.md")),
    ]
    for document in documents:
        text = document.read_text(encoding="utf-8")
        for target in re.findall(r"!?\[[^\]]*\]\(([^)]+)\)", text):
            if target.startswith(("http://", "https://", "#", "mailto:")):
                continue
            relative = target.split("#", 1)[0]
            assert (document.parent / relative).exists(), (
                f"{document.name}: missing {target}"
            )


def test_design_stance_is_linked_from_both_readmes():
    assert "设计立场" in (ROOT / "README.md").read_text(encoding="utf-8")
    assert "Design stance" in (ROOT / "README.en.md").read_text(encoding="utf-8")


def test_tutorials_are_marked_human_only():
    skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
    tutorials = (ROOT / "docs" / "tutorials" / "README.md").read_text(encoding="utf-8")
    assert "docs/tutorials" in skill
    assert "默认忽略" in skill or "默认不读" in skill
    assert "给 AI 的说明" in tutorials
    assert "作者本人" in tutorials
    assert "尽量不使用 AI 辅助创作" in tutorials
