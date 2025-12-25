# scores/collection.py
from __future__ import annotations
from typing import Iterable, Optional, Dict, List
import pandas as pd

from .base import ScoreBase, ScoreContext


class ScoreCollection:
    def __init__(self, scores: Optional[Iterable[ScoreBase]] = None):
        self.scores: List[ScoreBase] = list(scores) if scores else []

    def add(self, score: ScoreBase) -> "ScoreCollection":
        self.scores.append(score)
        return self

    def names(self) -> list[str]:
        return [s.name for s in self.scores]

    def required_inputs(self) -> set[str]:
        need = set()
        for s in self.scores:
            need |= set(s.required_inputs)
        return need

    def compute_all(
        self,
        ctx: ScoreContext,
        *,
        start=None,
        end=None,
        include: Optional[Iterable[str]] = None,
        exclude: Optional[Iterable[str]] = None,
        case_insensitive: bool = True,
    ) -> pd.DataFrame:
        selected = self.scores
        if include is not None:
            inc = {x.lower() for x in include} if case_insensitive else set(include)
            selected = [s for s in selected if (s.name.lower() if case_insensitive else s.name) in inc]
        if exclude is not None:
            exc = {x.lower() for x in exclude} if case_insensitive else set(exclude)
            selected = [s for s in selected if (s.name.lower() if case_insensitive else s.name) not in exc]

        rows: Dict[str, Dict[str, float]] = {}
        for s in selected:
            rows[s.name] = s.compute(ctx, start=start, end=end)

        # unify columns
        all_cols: list[str] = []
        for d in rows.values():
            for c in d.keys():
                if c not in all_cols:
                    all_cols.append(c)

        out = pd.DataFrame(index=list(rows.keys()), columns=all_cols, dtype=float)
        for r, d in rows.items():
            for c, v in d.items():
                out.loc[r, c] = v
        return out

    def to_manifest(self) -> dict:
        return {
            "scores_available": self.names(),
            "required_inputs_union": sorted(self.required_inputs()),
        }