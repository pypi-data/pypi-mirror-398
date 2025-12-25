from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Iterable, Dict, List, Optional, Any

from multi_dashboard import TabSpec, TabbedDashboard


@dataclass
class TearsheetSuite:
    """Render multiple tearsheets and optionally stitch them into a tabbed shell."""

    tearsheets: Iterable
    title: str = "Tearsheet Suite"
    tab_output_dir: Optional[str] = None
    create_tabbed: bool = True
    tab_titles: Optional[List[str]] = None

    def __init__(
        self,
        *tearsheets,
        title: str = "Tearsheet Suite",
        tab_output_dir: Optional[str] = None,
        create_tabbed: bool = True,
        tab_titles: Optional[List[str]] = None,
        **legacy_kwargs,
    ) -> None:
        legacy_iter = legacy_kwargs.pop("tearsheets", None)
        if legacy_kwargs:
            raise TypeError(f"Unexpected keyword arguments: {', '.join(legacy_kwargs.keys())}")
        combined: List[Any] = list(tearsheets)
        if legacy_iter is not None:
            if isinstance(legacy_iter, Iterable):
                combined.extend(list(legacy_iter))
            else:
                combined.append(legacy_iter)
        if len(combined) == 1 and not hasattr(combined[0], "render") and isinstance(combined[0], Iterable):
            combined = list(combined[0])

        self.tearsheets = combined
        self.title = title
        self.tab_output_dir = tab_output_dir
        self.create_tabbed = create_tabbed
        self.tab_titles = tab_titles

    def render(self) -> Dict[str, str]:
        ts_list = list(self.tearsheets)
        if not ts_list:
            return {}

        outputs: Dict[str, str] = {}
        tabs: List[TabSpec] = []
        inferred_parent: Optional[str] = None

        for idx, ts in enumerate(ts_list):
            path = ts.render()
            title = getattr(ts, "title", ts.__class__.__name__)
            outputs[title] = path

            tab_title = (
                self.tab_titles[idx] if self.tab_titles and idx < len(self.tab_titles) else title
            )
            tabs.append(TabSpec(title=tab_title, file_path=path))

            if inferred_parent is None:
                out_dir = getattr(ts, "output_dir", None)
                if out_dir:
                    inferred_parent = os.path.abspath(os.path.join(out_dir, os.pardir))

        if self.create_tabbed and len(tabs) >= 2:
            tab_dir = self.tab_output_dir or inferred_parent or "output/tearsheet_suite"
            tabbed = TabbedDashboard(tabs=tabs, title=self.title, output_dir=tab_dir)
            outputs["index"] = tabbed.html_path

        return outputs


# alias requested user-facing name
Tearsheet = TearsheetSuite
