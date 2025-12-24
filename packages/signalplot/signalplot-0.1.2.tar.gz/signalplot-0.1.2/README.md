# SignalPlot

SignalPlot is a minimalist plotting library built on pure Matplotlib. It enforces clean defaults that prioritize data over decoration. Every figure aims for clarity, scale honesty, and visual restraint.

SignalPlot targets analysts, engineers, and researchers who want publication ready plots without manual styling work. The library avoids high level styling layers and works directly with Matplotlib primitives.

## Design Philosophy

SignalPlot treats plots as analytical instruments. The figure should communicate structure, variation, and scale with minimal distraction. Decorative elements dilute interpretation. Honest axes preserve trust.

The style favors light backgrounds, thin spines, restrained color, and direct annotation. Figures remain readable in print, slides, and reports.

The visual approach draws inspiration from Edward Tufte, William Cleveland, and John Tukey. SignalPlot does not reproduce any single doctrine. It applies practical principles that improve readability and analytical trust.

## What SignalPlot Does

SignalPlot applies a consistent minimalist style to Matplotlib figures. It removes unnecessary chart elements. It enforces honest scales. It standardizes typography and spacing. It saves figures at publication quality resolution by default.

The library stays small by design. It does not wrap Matplotlib. It sets disciplined defaults and provides a few helpers for common patterns.

## What SignalPlot Does Not Do

SignalPlot does not depend on Seaborn or any high level styling framework. It does not add decorative themes. It does not alter data or exaggerate effects. It does not hide Matplotlib behavior behind abstractions.

## Style Contract

Figures use a white or near white background. Primary data appears in black or dark gray. Secondary elements appear in lighter gray. One accent color may appear for emphasis.

Top and right spines remain hidden. Left and bottom spines stay thin and light. Gridlines appear only on the y axis and remain subtle.

Axes labels remain optional. Titles carry descriptive meaning. Direct labels replace legends when practical. Typography stays consistent and modest.

Bar charts start at zero. Scales remain linear unless data demands otherwise.

### Always

- Use pure Matplotlib: rely on Matplotlib primitives, not styling wrappers or theme systems.
- Keep the palette restrained: black or dark gray for primary data, medium gray for secondary structure, and a single red accent (via `signalplot.ACCENT`) for emphasis only.
- Remove chartjunk: no 3D, shadows, gradients, or decorative textures.
- Keep framing light: hide top and right spines; keep left and bottom spines thin, light, and just outside the data where appropriate.
- Prefer minimal grids: at most subtle y-axis gridlines when they genuinely aid reading values; avoid x-axis grids unless essential.
- Let titles carry meaning: prefer descriptive titles and direct labels on lines/bars/points; fall back to legends only when direct labels are impractical.
- Use consistent typography: a clean sans-serif font, modest font sizes, and rare emphasis (bold/italics only when needed).
- Export at publication quality: save figures at 300 DPI with tight bounding boxes and a white background (SignalPlot’s defaults via `apply()` and `save()`).

### Never

- Never rely on high-level styling libraries: avoid seaborn and similar systems for appearance; SignalPlot assumes plain Matplotlib.
- Never add decorative clutter: skip extra gridlines, borders, background colors, and ornaments that do not improve interpretation.
- Never use more than one strong accent color: additional emphasis should come from position, annotation, or form, not a rainbow palette.
- Never distort axes or scales: do not truncate axes to exaggerate effects; bar charts, in particular, should start the y-axis at zero.

## Installation

SignalPlot installs like any small Python utility.

pip install signalplot

## Basic Usage

Import SignalPlot once at the start of your script. Create plots with standard Matplotlib calls. SignalPlot applies its defaults automatically.

```python
import matplotlib.pyplot as plt
import signalplot

signalplot.apply()

plt.plot(x, y)
plt.title("Monthly demand by region")
plt.savefig("monthly_demand.png", dpi=300, bbox_inches="tight", facecolor="white")
plt.show()
```

## Intended Audience

SignalPlot serves practitioners who care about analytical integrity. It fits academic work, internal reports, policy analysis, and engineering workflows. It favors repeatability and trust over style experimentation.

## License

MIT License.

## Name

SignalPlot reflects the core promise. High signal. Low noise.
