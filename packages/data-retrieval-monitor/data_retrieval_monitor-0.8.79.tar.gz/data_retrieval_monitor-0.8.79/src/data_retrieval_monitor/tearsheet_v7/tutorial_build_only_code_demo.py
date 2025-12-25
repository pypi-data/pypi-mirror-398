# tutorial_build_only_code_demo.py
# -*- coding: utf-8 -*-
"""Minimal example: Build backtest/prediction dashboards using the new class API."""

from __future__ import annotations

from pathlib import Path

from wrapped_helper import (
    make_backtest_bundle,
    make_prediction_bundle,
)
from backtest_dashboard import BacktestTearsheet
from information_dashboard import InformationManifest, InformationTearsheet
from tearsheet_suite import Tearsheet

def main():
    output_dir = Path("output/tutorial_build_only").resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    backtest_bundle = make_backtest_bundle()
    prediction_bundle = make_prediction_bundle()

    backtest_ts = BacktestTearsheet(
        figures=[
            "snapshot",
            "yearly_returns",
            "rolling_beta",
            "rolling_volatility",
            "rolling_sharpe",
            "rolling_sortino",
            "drawdowns_periods",
            "drawdown",
            "monthly_heatmap",
            "histogram",
            "distribution",
        ],
        tables=["metrics", "eoy", "drawdown_top10"],
        data_overrides={
            "returns": "tracking_pnl",
            "benchmark": "benchmark",
            "active_tracking_pnl": "active_tracking_pnl",
        },
        title="Backtest Tearsheet",
        output_dir=str(output_dir / "backtest"),
        data_source=backtest_bundle,
    )

    prediction_manifest = InformationManifest(
        factors=[c for c in prediction_bundle.preds_lf.collect_schema().names() if c != "date"],
        lags=[0, 1, 5, 10],
        horizons=[1, 5, 20],
        summary_lag=1,
        summary_horizon=5,
    )

    prediction_ts = InformationTearsheet(
        manifest=prediction_manifest,
        figures=["IC", "sign"],
        tables=["pred_metrics"],
        data_overrides={
            "preds": "preds_lf",
            "target": "target_lf",
            "residuals": "residuals_lf",
        },
        title="Prediction Tearsheet",
        output_dir=str(output_dir / "prediction"),
        data_source=prediction_bundle,
    )

    suite_outputs = Tearsheet(
        backtest_ts,
        prediction_ts,
        title="Tutorial Build Only",
        tab_output_dir=str(output_dir),
        create_tabbed=True,
    ).render()

    paths = {
        "backtest": backtest_ts.html_path,
        "prediction": prediction_ts.html_path,
        "index": suite_outputs.get("index"),
    }

    print("Dashboard outputs:")
    for key, value in paths.items():
        print(f"  {key}: {value}")

if __name__ == "__main__":
    main()
