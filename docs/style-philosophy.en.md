# Design stance: restrained, legible, figure-first

> This page explains the aesthetic and technical preferences behind this project. It is not an official journal specification and does not ask other authors to adopt it; the target journal's latest author guidelines always take precedence.

## Why this stance exists

This project grew out of the author's long practice in physical-oceanography figure design, submission, and revision. Authors, journals, and reviewers have different visual traditions, and there is no single correct answer. Some common submission figures devote more attention to decoration, saturation, or stacked text than to the data itself, which can make the science harder to read. This project deliberately takes the side of **less decoration, more information** rather than following that style.

This is a personal preference, not a judgement of other authors or journals. Its value is that it is **repeatable, checkable, and deliverable**, not that it claims to be the only valid aesthetic.

## Four principles

### 1. Use cmocean, not rainbow colormaps

Continuous colormaps come from [cmocean](https://matplotlib.org/cmocean/) whenever possible. jet, rainbow, and similar maps are not used: they can create false boundaries and an implied order in data that have neither. Perceptually uniform cmocean maps are a better match for continuous ocean and atmosphere fields.

The variable determines the map, not a last-minute preference:

- bounded positive fields, amplitude, RMSE: `cmo.dense`, `cmo.speed`;
- anomalies and differences: `cmo.balance`, with symmetric `vmin/vmax`;
- temperature and salinity: `cmo.thermal`, `cmo.haline`;
- bathymetry and depth: `cmo.deep`;
- phase: `cmo.phase`;
- velocity magnitude: `cmo.speed`.

Ranges and `extend` must follow whether data are actually clipped; never guess from the sign of the variable.

### 2. Figure first, text restrained

The figure should carry the message through the image, not through long prose, a main title, and repeated labels:

- no overall figure title; use panel subtitles and `(a)`, `(b)` labels for hierarchy;
- share axes where possible; hide repeated inner tick labels and keep labels on the left column and bottom row only;
- include axis labels only when needed, and always include units;
- keep only the legends, annotations, and arrows required to read the data.

"Less text" does not mean "less information". A good figure lets the reader see structure, gradients, anomalies, and differences first, then consult the labels.

### 3. A clear colorbar without taking over the map

A colorbar is a reading tool, not part of the map. Prefer a dedicated outer column, a strip below the figure, or an inset that does not squeeze the map or section. Panels showing the same variable should share one colorbar.

Segmented, truncated, or linearly composited colorbars are acceptable when they improve legibility, provided that:

- the label contains the variable and its unit;
- there are 4–7 ticks;
- `extend` matches the actual data range;
- no physically meaningless center is forced into the scale.

### 4. Analysis figures use the same visual language

CCA, wavelet, spectral, and EMD figures are not a separate aesthetic. They follow the same rules: figure first, honest colormaps, shared coordinates, restrained text. See [figure-recipes](../references/figure-recipes.md) for figure-specific starting points.

These choices have been used in the author's own submissions and revisions and have been examined by journal editors and reviewers. That does not make them universal, and it does not replace peer review or checks of statistical assumptions. A future tutorial series will present **question-driven ocean/atmosphere statistical analysis**, connecting why an analysis is chosen, how its assumptions are checked, and how the result is drawn.

## Boundaries

- A journal's figure-preparation requirements override this project. Check the latest guidelines for width, font size, fonts, and format.
- Journal presets, CVD screening, and layout checks are empirical tools, not official certification.
- Synthetic-data templates must keep `--demo` and clear synthetic labelling; they must never masquerade as real results.
- Aesthetics are debatable; data, units, colormap ranges, and statistical assumptions must remain verifiable.
