from __future__ import annotations

from typing import Iterable, Tuple

import matplotlib as mpl

__all__ = [
    "tidy_axes",
    "finish",
    "force_bar_zero",
    "add_range_frame",
    "style_line_plot",
    "style_scatter_plot",
    "style_bar_plot",
]


_BLACK = "#000000"
_DARKGRAY = "#404040"
_GRAY = "#808080"
_VERY_LIGHT_GRAY = "#E8E8E8"
_WHITE = "#FFFFFF"


def tidy_axes(ax: mpl.axes.Axes) -> mpl.axes.Axes:
    """Clean up axes spines and ticks to follow the style contract."""

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("0.35")
    ax.spines["bottom"].set_color("0.35")
    ax.spines["left"].set_linewidth(0.8)
    ax.spines["bottom"].set_linewidth(0.8)
    ax.tick_params(colors="0.25", width=0.8, length=3)

    return ax


def finish(ax: mpl.axes.Axes) -> mpl.axes.Axes:
    """Apply final cosmetic tweaks to an axes.

    Currently this is a thin alias of `tidy_axes` so that examples using
    either name remain valid.
    """

    return tidy_axes(ax)


def force_bar_zero(ax: mpl.axes.Axes) -> mpl.axes.Axes:
    """Force bar chart y-axis to start at zero, preserving honest scale."""

    lo, hi = ax.get_ylim()
    if hi <= 0:
        hi = 1.0
    ax.set_ylim(bottom=0, top=hi)
    return ax


def _data_bounds(data: Iterable[float]) -> Tuple[float, float]:
    seq = list(data)
    if not seq:
        return 0.0, 0.0
    return float(min(seq)), float(max(seq))


def add_range_frame(
    ax: mpl.axes.Axes,
    x_data: Iterable[float] | None = None,
    y_data: Iterable[float] | None = None,
) -> mpl.axes.Axes:
    """Shorten axes spines so they span only the data range.

    This is adapted from the older range-frame helper and keeps the
    spines visually tied to the data instead of the full axis domain.
    """

    if x_data is not None:
        x_min, x_max = _data_bounds(x_data)
        ax.spines["bottom"].set_bounds(x_min, x_max)

    if y_data is not None:
        y_min, y_max = _data_bounds(y_data)
        ax.spines["left"].set_bounds(y_min, y_max)

    return ax


def style_line_plot(ax: mpl.axes.Axes, *, emphasize_last: bool = False) -> mpl.axes.Axes:
    """Apply a restrained hierarchy of line styles to an axes."""

    tidy_axes(ax)

    lines = ax.get_lines()
    line_colors = [_BLACK, _DARKGRAY, _GRAY]
    line_styles = ["-", "--", ":"]

    for i, line in enumerate(lines):
        color = line_colors[i % len(line_colors)]
        style = line_styles[i % len(line_styles)]

        line.set_color(color)
        line.set_linestyle(style)
        line.set_linewidth(1.2)

        if emphasize_last and i == len(lines) - 1:
            line.set_linewidth(2.0)
            line.set_color(_BLACK)

    return ax


def style_scatter_plot(ax: mpl.axes.Axes) -> mpl.axes.Axes:
    """Style scatter collections with neutral points."""

    tidy_axes(ax)

    for collection in ax.collections:
        collection.set_edgecolors(_BLACK)
        collection.set_facecolors(_WHITE)
        collection.set_linewidths(1.0)

    return ax


def style_bar_plot(ax: mpl.axes.Axes, *, horizontal: bool = False) -> mpl.axes.Axes:
    """Style bar charts with alternating light fills and clean edges."""

    tidy_axes(ax)

    for i, patch in enumerate(ax.patches):
        patch.set_facecolor(_WHITE if i % 2 == 0 else _VERY_LIGHT_GRAY)
        patch.set_edgecolor(_BLACK)
        patch.set_linewidth(1.0)

    if horizontal:
        ax.spines["left"].set_visible(False)
        ax.tick_params(left=False)

    return ax



