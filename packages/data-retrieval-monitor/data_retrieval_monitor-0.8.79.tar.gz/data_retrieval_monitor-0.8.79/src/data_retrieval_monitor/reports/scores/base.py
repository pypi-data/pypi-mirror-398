# scores/base.py
from __future__ import annotations
from typing import List, Dict, Optional, Union
import polars as pl
from .metrics import Score

class ScoreCollection:
    def __init__(self, scores: List[Score]) -> None:
        self.scores = scores

    def compute_for_frame(
        self,
        frame: Union[pl.DataFrame, pl.Series],
        rf: Optional[Union[float, pl.Series]] = None,
        periods_per_year: int = 252
    ) -> Dict[str, Dict[str, float]]:
        """
        Returns dict: {portfolio: {score_key: value}}
        Accepts pl.DataFrame (any number of columns) or pl.Series (single strategy).
        """
        if isinstance(frame, pl.Series):
            frame = frame.to_frame()

        results: Dict[str, Dict[str, float]] = {}
        for col in frame.columns:
            s = frame[col]  # pl.Series
            row: Dict[str, float] = {}
            for metric in self.scores:
                try:
                    row[metric.key] = float(metric.compute(s, rf=rf, periods_per_year=periods_per_year))
                except Exception:
                    row[metric.key] = float("nan")
            results[col] = row
        return results

    @staticmethod
    def to_pandas_tables(result_dict: Dict[str, Dict[str, float]]):
        import pandas as pd
        if not result_dict:
            return pd.DataFrame()
        df = pd.DataFrame(result_dict).T
        df.index.name = "Portfolio"
        return df