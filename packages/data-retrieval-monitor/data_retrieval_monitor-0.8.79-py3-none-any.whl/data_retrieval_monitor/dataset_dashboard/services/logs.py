from __future__ import annotations
from typing import Optional
from urllib.parse import quote

class LogLinker:
    def __init__(self, log_root: str):
        self.root = log_root

    def href_for(self, path_or_url: Optional[str]) -> Optional[str]:
        if not path_or_url:
            return None
        s = str(path_or_url)
        if s.startswith("http://") or s.startswith("https://"):
            return s
        return "file://" + quote(s)

def register_log_routes(server, linker: LogLinker):
    return
