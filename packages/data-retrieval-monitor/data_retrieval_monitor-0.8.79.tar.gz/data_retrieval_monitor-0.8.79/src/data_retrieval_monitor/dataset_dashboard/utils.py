from datetime import datetime, timezone
import pytz

def utc_now_iso():
    return datetime.now(timezone.utc).isoformat()

def to_local_str(ts_iso, tzname="UTC"):
    if not ts_iso:
        return "-"
    try:
        dt = datetime.fromisoformat(str(ts_iso).replace("Z","+00:00"))
        tz = pytz.timezone(tzname or "UTC")
        return dt.astimezone(tz).strftime("%Y-%m-%d %H:%M:%S %Z")
    except Exception:
        return str(ts_iso)

def px(n:int) -> str:
    return f"{int(n)}px"

def tab_version(store, tab: str) -> str:
    """Return a monotonic-ish version string for the tab to bust caches on updates."""
    try:
        state = store.state()
        return (state.get("tabs", {}).get(tab, {}).get("updated_at") or "0")
    except Exception:
        return "0"