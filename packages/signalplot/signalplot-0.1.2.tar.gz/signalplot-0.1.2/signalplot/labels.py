from __future__ import annotations

from typing import Any, Optional

import matplotlib as mpl

from .style import ACCENT

__all__ = [
    "direct_label",
    "note",
    "emphasize_last",
    "accent_point",
    "event_line",
]


def direct_label(
    ax: mpl.axes.Axes,
    x: float,
    y: float,
    text: str,
    *,
    dx: float = 0.0,
    dy: float = 0.0,
    use_accent: bool = False,
    ha: str = "left",
    va: str = "center",
    **kwargs: Any,
) -> mpl.axes.Axes:
    """Place a direct label near a data point.

    Typical use is to label the last point of a line instead of using a legend.
    """

    color = ACCENT if use_accent else "0.1"
    ax.text(
        x + dx,
        y + dy,
        text,
        ha=ha,
        va=va,
        color=color,
        fontsize=mpl.rcParams["font.size"],
        **kwargs,
    )
    return ax


def note(
    ax: mpl.axes.Axes,
    x: float,
    y: float,
    text: str,
    **kwargs: Any,
) -> mpl.axes.Axes:
    """Attach a short note with a simple arrow, avoiding legends."""

    ax.annotate(
        text,
        xy=(x, y),
        xytext=(10, 10),
        textcoords="offset points",
        arrowprops={"arrowstyle": "-", "color": "0.35", "linewidth": 0.8},
        color="0.15",
        **kwargs,
    )
    return ax


def emphasize_last(
    ax: mpl.axes.Axes,
    x: float,
    y: float,
    *,
    size: float = 30.0,
    **kwargs: Any,
) -> mpl.axes.Axes:
    """Emphasize a final point in a series using the accent color."""

    ax.scatter([x], [y], s=size, color=ACCENT, zorder=3, **kwargs)
    return ax


def accent_point(
    ax: mpl.axes.Axes,
    x: float,
    y: float,
    *,
    label: Optional[str] = None,
    color: Optional[str] = None,
    size: float = 30.0,
    zorder: int = 3,
    **kwargs: Any,
) -> mpl.axes.Axes:
    """Highlight a single point with the accent color.

    Optionally add a short text label offset slightly from the point.
    """

    c = color or ACCENT
    ax.scatter([x], [y], s=size, color=c, zorder=zorder, **kwargs)

    if label:
        ax.text(
            x,
            y,
            label,
            ha="left",
            va="bottom",
            color=c,
            fontsize=mpl.rcParams["font.size"],
        )

    return ax


def event_line(
    ax: mpl.axes.Axes,
    x: Any,
    *,
    text: Optional[str] = None,
    y_text: float = 0.9,
    color: Optional[str] = None,
    linewidth: float = 1.0,
    linestyle: str = "--",
    **kwargs: Any,
) -> mpl.axes.Axes:
    """Draw a vertical event marker with optional label.

    `x` can be a numeric value or datetime, consistent with `axvline`.
    If 0 <= y_text <= 1, it is treated as a fraction of the data y-span.
    Otherwise it is interpreted directly in data coordinates.
    """

    c = color or ACCENT
    ax.axvline(x, color=c, linewidth=linewidth, linestyle=linestyle, **kwargs)

    if text is not None:
        y0, y1 = ax.get_ylim()
        if 0.0 <= y_text <= 1.0:
            y = y0 + y_text * (y1 - y0)
        else:
            y = y_text

        ax.text(
            x,
            y,
            text,
            ha="left",
            va="center",
            color=c,
            fontsize=mpl.rcParams["font.size"],
        )

    return ax


