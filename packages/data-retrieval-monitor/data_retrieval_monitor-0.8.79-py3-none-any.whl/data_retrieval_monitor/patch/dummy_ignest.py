# dummy_ingest.py

import random
from datetime import datetime, timezone

import requests

BASE = "http://localhost:8050"  # change if needed

STATUSES = [
    "succeeded",
    "running",
    "queued",
    "waiting",
    "failed",
    "overdue",
]
STAGES = ["archive", "stage", "enrich", "consolidate"]


def make_items(n: int = 60):
    items = []
    for i in range(n):
        items.append(
            {
                "dataset": f"ds_{i:03d}",
                "owner": random.choice(["owner-a", "owner-b", "owner-c"]),
                "mode": random.choice(["live", "backfill"]),
                "stage": random.choice(STAGES),
                "status": random.choice(STATUSES),
                "counts": {},
                "chunks": [],
            }
        )
    return items


if __name__ == "__main__":
    payload = {
        "tab": "data",
        "items": make_items(),
        "meta": {
            "env": "dummy",
            "ingested_at": datetime.now(timezone.utc).isoformat(),
        },
    }

    r = requests.post(f"{BASE}/ingest_snapshot", json=payload, timeout=10)
    print(r.status_code, r.text)