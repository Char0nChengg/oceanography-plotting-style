from __future__ import annotations

import pytest

import ocean_journal as oj


def test_journal_widths_and_aliases():
    agu = oj.get_journal("AGU")
    assert agu.key == "agu"
    assert agu.width_in("double") > agu.width_in("single")
    assert oj.get_journal("jgr").key == "agu"
    assert oj.get_journal("nature").body_pt < oj.get_journal("generic").body_pt


def test_figure_size_respects_max_height():
    width, height = oj.figure_size("nature", "double", height_mm=999)
    assert width > 0
    assert height <= oj.get_journal("nature").max_height_mm / oj.MM_PER_INCH + 1e-9


def test_unknown_journal():
    with pytest.raises(ValueError, match="Unknown journal"):
        oj.get_journal("not-a-journal")


def test_available_journals():
    names = oj.available_journals()
    assert "agu" in names and "ams" in names and "nature" in names
