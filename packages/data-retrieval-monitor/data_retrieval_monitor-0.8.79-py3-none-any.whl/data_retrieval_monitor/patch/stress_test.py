# stress_test.py

import concurrent.futures
import time

import requests

BASE = "http://localhost:8050"


def hit_root(i: int) -> float:
    t0 = time.perf_counter()
    r = requests.get(BASE + "/", timeout=10)
    dt = time.perf_counter() - t0
    print(f"req {i:03d} -> {r.status_code} in {dt:.3f}s")
    return dt


if __name__ == "__main__":
    N = 100
    with concurrent.futures.ThreadPoolExecutor(max_workers=N) as ex:
        list(ex.map(hit_root, range(N)))