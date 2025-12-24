from __future__ import annotations

from typing import Any, Iterable, Sequence, Tuple

import matplotlib as mpl
import matplotlib.pyplot as plt

from .axes import (
    add_range_frame,
    finish,
    force_bar_zero,
    style_bar_plot,
    style_line_plot,
    style_scatter_plot,
    tidy_axes,
)
from .labels import accent_point, direct_label, emphasize_last, event_line, note
from .style import ACCENT, SaveDefaults, apply, patch_pyplot, save, savefig

__version__ = "0.1.2"


def figure(
    *,
    nrows: int = 1,
    ncols: int = 1,
    figsize: Tuple[float, float] | None = None,
    sharex: bool = False,
    sharey: bool = False,
    constrained_layout: bool = True,
) -> Tuple[plt.Figure, mpl.axes.Axes | Sequence[mpl.axes.Axes]]:
    """Create a SignalPlot-styled figure.

    This is a light wrapper around :func:`matplotlib.pyplot.subplots` that
    chooses sensible defaults for analytical figures and returns the figure
    plus axes.
    """

    fig, axes = plt.subplots(
        nrows=nrows,
        ncols=ncols,
        figsize=figsize,
        sharex=sharex,
        sharey=sharey,
        constrained_layout=constrained_layout,
    )
    return fig, axes


def small_multiples(
    count: int,
    *,
    ncols: int = 3,
    sharex: bool = True,
    sharey: bool = False,
    figsize: Tuple[float, float] | None = None,
) -> Tuple[plt.Figure, Sequence[mpl.axes.Axes]]:
    """Create a grid of small-multiple axes.

    Returns the figure and a flat sequence of axes, already styled with
    :func:`tidy_axes`.
    """

    nrows = (count + ncols - 1) // ncols
    fig, axes_grid = plt.subplots(
        nrows=nrows,
        ncols=ncols,
        sharex=sharex,
        sharey=sharey,
        figsize=figsize,
        constrained_layout=True,
    )

    if isinstance(axes_grid, mpl.axes.Axes):
        axes_list = [axes_grid]
    else:
        axes_list = [ax for row in axes_grid for ax in (row if isinstance(row, Iterable) else [row])]

    # Only keep as many axes as requested and tidy them.
    axes_list = axes_list[:count]
    for ax in axes_list:
        tidy_axes(ax)

    return fig, axes_list


def band(
    ax: mpl.axes.Axes,
    x: Sequence[float],
    low: Sequence[float],
    high: Sequence[float],
    *,
    color: str = "0.9",
    edgecolor: str = "none",
    alpha: float = 1.0,
    label: str | None = None,
    zorder: int = 1,
    **kwargs: Any,
) -> mpl.axes.Axes:
    """Draw a filled band between ``low`` and ``high`` around a series.

    This is useful for confidence intervals, prediction bands, or
    uncertainty regions.
    """

    ax.fill_between(
        x,
        low,
        high,
        facecolor=color,
        edgecolor=edgecolor,
        alpha=alpha,
        label=label,
        zorder=zorder,
        **kwargs,
    )
    return ax


__all__ = [
    "__version__",
    # Stable high-level API
    "apply",
    "figure",
    "save",
    "small_multiples",
    "direct_label",
    "band",
    # Additional helpers (may expand over time)
    "savefig",
    "patch_pyplot",
    "SaveDefaults",
    "ACCENT",
    "add_range_frame",
    "tidy_axes",
    "finish",
    "style_line_plot",
    "style_scatter_plot",
    "style_bar_plot",
    "note",
    "emphasize_last",
    "accent_point",
    "event_line",
    "force_bar_zero",
]


