from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Mapping, Optional

import matplotlib as mpl
import matplotlib.pyplot as plt

__all__ = [
    "SaveDefaults",
    "ACCENT",
    "apply",
    "save",
    "savefig",
    "patch_pyplot",
]


@dataclass(frozen=True)
class SaveDefaults:
    """Defaults for saving figures.

    These map directly onto Matplotlib's savefig parameters and are
    installed into rcParams by `apply()`.
    """

    dpi: int = 300
    bbox_inches: str = "tight"
    facecolor: str = "white"
    edgecolor: str = "white"


# One restrained accent color for emphasis-only marks.
ACCENT: str = "#d62728"  # muted red, readable in print


_DEFAULT_SAVE = SaveDefaults()

# Defaults used by the pyplot patching helpers. These start aligned with
# `SaveDefaults` and can be overridden by `patch_pyplot()`.
_DEFAULT_SAVEFIG: dict[str, Any] = {
    "dpi": _DEFAULT_SAVE.dpi,
    "bbox_inches": _DEFAULT_SAVE.bbox_inches,
    "facecolor": _DEFAULT_SAVE.facecolor,
    "edgecolor": _DEFAULT_SAVE.edgecolor,
}
_ORIGINAL_SAVEFIG: Optional[Callable[..., Any]] = None


def apply(
    *,
    font_family: str = "sans-serif",
    base_fontsize: int = 10,
    figure_dpi: int = 100,
    save: SaveDefaults = _DEFAULT_SAVE,
) -> None:
    """Apply SignalPlot rcParams defaults.

    Call this once near the start of your script or notebook:

    >>> import signalplot as sp
    >>> sp.apply()
    """

    mpl.rcParams.update(
        {
            # Figure / axes background
            "figure.facecolor": "white",
            "axes.facecolor": "white",
            "figure.dpi": figure_dpi,
            # Typography
            "font.family": font_family,
            "font.size": base_fontsize,
            "axes.titlesize": base_fontsize + 1,
            "axes.labelsize": base_fontsize,
            "xtick.labelsize": base_fontsize - 1,
            "ytick.labelsize": base_fontsize - 1,
            # Spines and grid
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.grid": False,
            "grid.alpha": 0.15,
            "grid.linewidth": 0.6,
            # Ticks
            "xtick.direction": "out",
            "ytick.direction": "out",
            # Save defaults
            "savefig.dpi": save.dpi,
            "savefig.bbox": save.bbox_inches,
            "savefig.facecolor": save.facecolor,
            "savefig.edgecolor": save.edgecolor,
            "savefig.transparent": False,
        }
    )


def save(
    path: str,
    *,
    dpi: Optional[int] = None,
    bbox_inches: Optional[str] = None,
    facecolor: Optional[str] = None,
    edgecolor: Optional[str] = None,
    **kwargs: Any,
) -> None:
    """Save the current figure with SignalPlot defaults unless overridden.

    After `apply()`, this is equivalent to `plt.savefig(path)` but
    makes the intended contract explicit and still allows overrides:

        sp.save("figure.png")
        sp.save("hi_res.png", dpi=600)
    """

    params: dict[str, Any] = {
        "dpi": dpi if dpi is not None else mpl.rcParams["savefig.dpi"],
        "bbox_inches": (
            bbox_inches
            if bbox_inches is not None
            else mpl.rcParams["savefig.bbox"]
        ),
        "facecolor": (
            facecolor
            if facecolor is not None
            else mpl.rcParams["savefig.facecolor"]
        ),
        "edgecolor": (
            edgecolor
            if edgecolor is not None
            else mpl.rcParams["savefig.edgecolor"]
        ),
    }
    params.update(kwargs)
    plt.savefig(path, **params)


def savefig(path: str, **kwargs: Any) -> None:
    """Alias for `save` to match Matplotlib naming.

    This makes the cookbook sketches that use `signalplot.savefig(...)`
    work without change.
    """

    save(path, **kwargs)


def patch_pyplot(defaults: Optional[Mapping[str, Any]] = None) -> None:
    """Patch `matplotlib.pyplot.savefig` to inject SignalPlot defaults.

    After calling this once, plain `plt.savefig("x.png")` will receive
    the configured defaults unless the caller overrides them.
    """

    global _ORIGINAL_SAVEFIG, _DEFAULT_SAVEFIG

    if _ORIGINAL_SAVEFIG is None:
        _ORIGINAL_SAVEFIG = plt.savefig

    cfg = dict(_DEFAULT_SAVEFIG)
    if defaults is not None:
        cfg.update(defaults)
    _DEFAULT_SAVEFIG = cfg

    def _wrapped(*args: Any, **kwargs: Any) -> Any:
        merged = dict(cfg)
        merged.update(kwargs)
        assert _ORIGINAL_SAVEFIG is not None
        return _ORIGINAL_SAVEFIG(*args, **merged)

    plt.savefig = _wrapped  # type: ignore[assignment]


