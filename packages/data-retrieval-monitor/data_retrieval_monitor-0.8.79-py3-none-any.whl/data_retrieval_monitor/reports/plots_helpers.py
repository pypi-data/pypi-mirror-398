# plots_helpers.py
# Centralized, subtitle-free QuantStats plotting with consistent smaller fonts.

from __future__ import annotations
import matplotlib.pyplot as plt

# import QuantStats plot wrappers (no 'compounded' kwarg!)
from quantstats.plots import (
    snapshot, earnings, returns, log_returns, yearly_returns,
    daily_returns, rolling_beta, rolling_volatility,
    rolling_sharpe, rolling_sortino, drawdown, drawdowns_periods,
    monthly_heatmap, histogram, distribution
)

# default sizes for the “portfolio summary” (top) plots vs regular plots
FIGSIZE_TOP   = (6.6, 3.6)
FIGSIZE_SMALL = (6.2, 3.2)

# compact fonts
PLOT_FONTS = dict(
    title=11,      # main title on axes
    label=9,       # x/y labels
    ticks=8,       # tick labels
    legend=8       # legend text
)

def _shrink_fonts(fig, fonts=PLOT_FONTS):
    """ Reduce title/label/tick/legend sizes on all axes of a figure. """
    for ax in fig.axes:
        # axis title
        if ax.title:
            ax.title.set_fontsize(fonts["title"])
        # labels
        ax.set_xlabel(ax.get_xlabel(), fontsize=fonts["label"])
        ax.set_ylabel(ax.get_ylabel(), fontsize=fonts["label"])
        # ticks
        ax.tick_params(axis="both", labelsize=fonts["ticks"])
        # legend
        leg = ax.get_legend()
        if leg:
            for t in leg.get_texts():
                t.set_fontsize(fonts["legend"])
    # tighten layout after font changes
    fig.tight_layout()

# Map dashboard/manifest figure keys -> callable and whether it needs benchmark
_PLOT_SPEC = {
    "snapshot":            (snapshot,          False),
    "earnings":            (earnings,          False),
    "returns":             (returns,           True),   # will pass benchmark if provided
    "log_returns":         (log_returns,       True),
    "yearly_returns":      (yearly_returns,    True),
    "daily_returns":       (daily_returns,     True),
    "rolling_beta":        (rolling_beta,      True),
    "rolling_volatility":  (rolling_volatility,True),
    "rolling_sharpe":      (rolling_sharpe,    False),
    "rolling_sortino":     (rolling_sortino,   False),
    "drawdown":            (drawdown,          False),
    "drawdowns_periods":   (drawdowns_periods, False),
    "monthly_heatmap":     (monthly_heatmap,   True),   # accepts benchmark for active returns
    "histogram":           (histogram,         True),   # can take benchmark; if None, still OK
    "distribution":        (distribution,      False)   # QS distribution() does not take benchmark
}

def make_qs_plot(
    kind: str,
    series,                       # pd.Series
    benchmark=None,               # pd.Series or None
    top_plot: bool = False,
    grayscale: bool = False
):
    """
    Build a QuantStats plot with no subtitle and compact fonts.
    Returns a Matplotlib Figure.
    """
    kind = kind.strip().lower()
    if kind not in _PLOT_SPEC:
        raise ValueError(f"Unknown plot kind: {kind}")

    func, needs_bench = _PLOT_SPEC[kind]

    # choose smaller figsizes
    figsize = FIGSIZE_TOP if top_plot else FIGSIZE_SMALL

    # Common kwargs:
    # - DO NOT pass `compounded` (older QS errors out)
    # - Force subtitle=False everywhere to remove “Date | Sharpe …”
    common = dict(
        grayscale=grayscale,
        figsize=figsize,
        subtitle=False,
        show=False,
        ylabel=""
    )

    # Build kwargs respecting whether plot needs benchmark
    if needs_bench:
        fig = func(series, benchmark, **common)
    else:
        # some functions accept title=series.name; we rely on QS defaults
        fig = func(series, **common)

    # in case some wrappers return None (older QS sometimes returns Axes)
    # try to resolve a Figure from Axes
    if fig is None:
        # attempt: current figure
        fig = plt.gcf()

    # remove any extra suptitle we might inherit, and shrink fonts
    # (QS generally uses axes titles; this is just to be safe)
    try:
        fig._suptitle = None
    except Exception:
        pass

    _shrink_fonts(fig)

    return fig