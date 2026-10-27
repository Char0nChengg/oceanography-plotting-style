"""Journal-specific figure widths and font-size presets.

The numbers are practical, empirical defaults, not official journal templates
or a substitute for the current author guidelines.  Widths are in millimetres;
font sizes are in points at final printed size.  Verify the latest guidelines
before submission, especially for Nature portfolio titles.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import matplotlib as mpl

MM_PER_INCH = 25.4


@dataclass(frozen=True)
class JournalStyle:
    """One empirical journal preset.

    All widths/heights are millimetres and all font sizes are points at final
    print size.  These values are approximate and intentionally easy to edit;
    they are not a claim about a journal's official specifications.
    """

    key: str
    name: str
    single_mm: float
    one_half_mm: float
    double_mm: float
    max_height_mm: float
    body_pt: float
    tick_pt: float
    title_pt: float
    line_pt: float
    dpi: int = 300

    def width_mm(self, columns: str | float = "double") -> float:
        key = str(columns).lower().strip()
        if key in {"1", "1.0", "single", "1col", "one"}:
            return self.single_mm
        if key in {"1.5", "1.50", "one-half", "1.5col", "1.5 column"}:
            return self.one_half_mm
        if key in {"2", "2.0", "double", "2col", "two"}:
            return self.double_mm
        raise ValueError(f"columns must be single, 1.5, or double; got {columns!r}")

    def width_in(self, columns: str | float = "double") -> float:
        return self.width_mm(columns) / MM_PER_INCH


JOURNALS: dict[str, JournalStyle] = {
    "generic": JournalStyle(
        "generic", "Generic manuscript", 89, 140, 183, 240, 8, 8, 9, 0.8,
    ),
    "agu": JournalStyle(
        "agu", "AGU (JGR / GRL)",
        89, 140, 180, 240, 8, 8, 9, 0.8,
    ),
    "ams": JournalStyle(
        "ams", "American Meteorological Society",
        85, 140, 178, 235, 8, 8, 9, 0.8,
    ),
    "elsevier": JournalStyle(
        "elsevier", "Elsevier (Ocean Modelling, DSR)",
        90, 140, 190, 240, 8, 8, 9, 0.8,
    ),
    "nature": JournalStyle(
        "nature", "Nature portfolio",
        89, 120, 183, 247, 6, 6, 7, 0.6,
    ),
}

_ALIASES = {
    "jgr": "agu",
    "grl": "agu",
    "wiley": "agu",
    "ametsoc": "ams",
    "american meteorological society": "ams",
    "ocean modelling": "elsevier",
    "dsr": "elsevier",
    "nature communications": "nature",
    "nat": "nature",
}


def get_journal(name: str = "generic") -> JournalStyle:
    """Return a journal preset by key or common alias."""
    key = str(name).lower().strip()
    key = _ALIASES.get(key, key)
    try:
        return JOURNALS[key]
    except KeyError as exc:
        available = ", ".join(sorted(JOURNALS))
        raise ValueError(f"Unknown journal {name!r}; available: {available}") from exc


def figure_size(
    name: str = "generic",
    columns: str | float = "double",
    height_mm: float | None = None,
    aspect: float = 1.4,
) -> tuple[float, float]:
    """Return ``(width_in, height_in)`` capped by the journal maximum height."""
    style = get_journal(name)
    width_mm = style.width_mm(columns)
    if height_mm is None:
        if not math.isfinite(aspect) or aspect <= 0:
            raise ValueError(f"aspect must be positive and finite, got {aspect!r}")
        height_mm = width_mm / float(aspect)
    else:
        height_mm = float(height_mm)
        if not math.isfinite(height_mm) or height_mm <= 0:
            raise ValueError(f"height_mm must be positive and finite, got {height_mm!r}")
    height_mm = min(height_mm, style.max_height_mm)
    return width_mm / MM_PER_INCH, height_mm / MM_PER_INCH


def apply_journal_style(name: str = "generic") -> JournalStyle:
    """Set base font/line sizes for a journal, leaving figure layout to the caller.

    If ``set_ocean_style`` is also used, call that first and this function
    second so the journal line widths and title sizes win.
    """
    style = get_journal(name)
    mpl.rcParams.update({
        "font.size": style.body_pt,
        "axes.labelsize": style.body_pt,
        "axes.titlesize": style.title_pt,
        "xtick.labelsize": style.tick_pt,
        "ytick.labelsize": style.tick_pt,
        "legend.fontsize": max(style.tick_pt - 1, 5),
        "lines.linewidth": style.line_pt,
        "axes.linewidth": style.line_pt,
        "savefig.dpi": style.dpi,
    })
    return style


def available_journals() -> list[str]:
    return sorted(JOURNALS)
