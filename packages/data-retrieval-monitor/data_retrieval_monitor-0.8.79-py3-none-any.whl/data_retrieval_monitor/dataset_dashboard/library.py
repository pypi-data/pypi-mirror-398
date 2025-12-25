import os, random, json
from pathlib import Path
from typing import List, Tuple, Dict, Optional
from .constants import DATA_STAGES, TAB_IDS, status_order_for_tab
from .config import AppConfig
from .utils import utc_now_iso

# ---------- helpers ----------
def _mk_chunks(statuses: List[str], base_dir: Path, dn: str, bucket: str, k: int) -> List[dict]:
    chunks: List[dict] = []
    for j in range(k):
        s = random.choice(statuses)
        log_path = (base_dir / dn / f"{bucket}-{j}.log")
        log_path.parent.mkdir(parents=True, exist_ok=True)
        log_path.write_text(f"{dn} {bucket} chunk {j} status={s}\n", encoding="utf-8")
        chunks.append({
            "id": f"A00-{j}",       # keep existing convention
            "status": s,
            "proc": f"https://example.com/proc/{dn}/{bucket}/{j}",
            "log": str(log_path),                   # absolute path for LogLinker
        })
    return chunks

def _maybe_save(save_dir: Optional[Path], fname: str, payload: dict) -> None:
    if not save_dir:
        return
    if isinstance(save_dir, (str, os.PathLike)):
        save_dir = Path(save_dir)
    if save_dir.suffix.lower() == ".json":
        save_dir= save_dir.parent
        # if given a file path, use its parent dir
    save_dir.mkdir(parents=True, exist_ok=True)
    (save_dir / fname).write_text(json.dumps(payload, indent=2), encoding="utf-8")

# ---------- per-owner, per-tab builders ----------
def make_data_payload_for_owner(cfg: AppConfig, owner: str, num_items: int = 12) -> Tuple[List[dict], Dict]:
    # random.seed()
    log_root = Path(cfg.log_root)
    items: List[dict] = []
    statuses = status_order_for_tab("data")
    owner_norm = (owner or cfg.default_owner).strip().lower()

    for i in range(num_items):
        dn = f"data-{owner_norm}-{i:03d}"
        mode = "backfill" if (i % 3 == 0) else "live"
        for stg in DATA_STAGES:
            k = random.randint(2, 5)
            chs = _mk_chunks(statuses, log_root, dn, stg, k)
            items.append({
                "owner": owner_norm.capitalize(),   # ← use provided owner
                "mode": mode,
                "data_name": dn,
                "stage": stg,
                "chunks": chs,
                "errors": [],
            })
    meta = {"env": cfg.environment_label, "ingested_at": utc_now_iso()}
    return items, meta

def make_features_payload_for_owner(cfg: AppConfig, owner: str, num_items: int = 12) -> Tuple[List[dict], Dict]:
    # random.seed()
    log_root = Path(cfg.log_root)
    items: List[dict] = []
    statuses = status_order_for_tab("features")
    owner_norm = (owner or cfg.default_owner).strip().lower()

    for i in range(num_items):
        dn = f"features-{owner_norm}-{i:03d}"
        k = random.randint(2, 6)
        chs = _mk_chunks(statuses, log_root, dn, "status", k)
        items.append({
            "owner": owner_norm,
            "mode": "live",
            "data_name": dn,
            "stage": "status", # Do not capitalize stage. 
            "chunks": chs,
            "errors": [],
        })
    meta = {"env": cfg.environment_label, "ingested_at": utc_now_iso()}
    
    return items, meta

def make_alphas_payload_for_owner(cfg: AppConfig, owner: str, num_items: int = 12) -> Tuple[List[dict], Dict]:
    random.seed()
    log_root = Path(cfg.log_root)
    items: List[dict] = []
    statuses = status_order_for_tab("alphas")
    owner_norm = (owner or cfg.default_owner).strip().lower()

    for i in range(num_items):
        dn = f"alphas-{owner_norm}-{i:03d}"
        k = random.randint(2, 6)
        chs = _mk_chunks(statuses, log_root, dn, "status", k)
        items.append({
            "owner": owner_norm,
            "mode": "live",
            "data_name": dn,
            "stage": "status",
            "chunks": chs,
            "errors": [],
        })
    meta = {"env": cfg.environment_label, "ingested_at": utc_now_iso()}
    return items, meta

def make_strategies_payload_for_owner(cfg: AppConfig, owner: str, num_items: int = 12) -> Tuple[List[dict], Dict]:
    random.seed()
    log_root = Path(cfg.log_root)
    items: List[dict] = []
    statuses = status_order_for_tab("strategies")
    owner_norm = (owner or cfg.default_owner).strip().lower()

    for i in range(num_items):
        dn = f"strategies-{owner_norm}-{i:03d}"
        k = random.randint(2, 6)
        chs = _mk_chunks(statuses, log_root, dn, "status", k)
        items.append({
            "owner": owner_norm,
            "mode": "live",
            "data_name": dn,
            "stage": "status",
            "chunks": chs,
            "errors": [],
        })
    meta = {"env": cfg.environment_label, "ingested_at": utc_now_iso()}
    return items, meta

# ---------- combine per owner across tabs ----------
def make_payload_for_owner(
    cfg: AppConfig, owner: str, tabs: Optional[List[str]] = None,
    num_items: int = 12, save_dir: Optional[Path] = '/Users/donggeunkim/Downloads/dataset_dashboard_repo_v5/payload_sample/'
) -> Dict:
    tabs = [t for t in (tabs or TAB_IDS) if t in TAB_IDS]
    pack: Dict[str, Dict] = {"tabs": {}}

    for t in tabs:
        if t == "data":
            items, meta = make_data_payload_for_owner(cfg, owner, num_items)
        elif t == "features":
            items, meta = make_features_payload_for_owner(cfg, owner, num_items)
        elif t == "alphas":
            items, meta = make_alphas_payload_for_owner(cfg, owner, num_items)
        else:  # strategies
            items, meta = make_strategies_payload_for_owner(cfg, owner, num_items)

        pack["tabs"][t] = {"snapshot": items, "meta": meta}
        _maybe_save(save_dir, f"{t}-{owner.lower()}.json", {"snapshot": items, "meta": meta})

    return pack

# ---------- combine across multiple owners ----------
def make_multi_owner_payload(
    cfg: AppConfig,
    owners: Optional[List[str]] = None,
    tabs: Optional[List[str]] = None,
    num_items: int = 12,
    save_dir: Optional[Path] = '/Users/donggeunkim/Downloads/dataset_dashboard_repo_v5/payload_sample/'
) -> Dict:
    """
    Combine payloads across multiple owners for the given tabs.
    Default owners (when none provided): KIMDG, KIMYD, LEEJM.
    """
    # default owners → ensure we seed more than QSG
    owners = [o for o in (owners or ["KIMDG", "KIMYD", "LEEJM"]) if o]
    tabs = [t for t in (tabs or TAB_IDS) if t in TAB_IDS]

    # pretty labels (shown if your UI uses meta.owner_labels)
    owner_labels = {o.strip().lower(): o.strip().upper() for o in owners}

    out: Dict[str, Dict] = {"tabs": {}}
    for t in tabs:
        all_items: List[dict] = []
        meta = {
            "env": cfg.environment_label,
            "ingested_at": utc_now_iso(),
            "owner_labels": owner_labels,
        }
        for o in owners:
            owner_pack = make_payload_for_owner(cfg, o, tabs=[t], num_items=num_items, save_dir=save_dir)
            part = owner_pack["tabs"][t]
            all_items.extend(part.get("snapshot") or [])
            # bump timestamp so "last write wins"
            meta["ingested_at"] = utc_now_iso()

        out["tabs"][t] = {"snapshot": all_items, "meta": meta}
        _maybe_save(save_dir, f"{t}-ALL.json", out["tabs"][t])
    return out


# --- replace this function ---
def seed_all_tabs(host, num_per_tab: int = 12) -> None:
    """
    Called by app.py on startup.

    Default owners: KIMDG, KIMYD, LEEJM.
    You can still override with env var:
      SEED_OWNERS="QSG,KIMDG" python -m dataset_dashboard.app ...
    """
    cfg = host.cfg
    env_owners = (os.getenv("SEED_OWNERS") or "").strip()
    owners = [s.strip() for s in env_owners.split(",") if s.strip()] or ["KIMDG", "KIMYD", "LEEJM"]

    combined = make_multi_owner_payload(
        cfg,
        owners=owners,
        tabs=TAB_IDS,
        num_items=num_per_tab,
        save_dir='/Users/donggeunkim/Downloads/dataset_dashboard_repo_v5/payload_sample/'  # or None to skip saving
    )

    for t in TAB_IDS:
        pack = combined["tabs"].get(t) or {"snapshot": [], "meta": {}}
        items = list(pack.get("snapshot") or [])
        meta = dict(pack.get("meta") or {})
        host.store.apply_snapshot_with_meta_tab(t, items, meta)