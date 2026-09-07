#!/usr/bin/env python3
"""Read advisory Codex quota snapshots locally; adapted from upstream PR #9.

Exit 0: recent windows below threshold; 1: recent window at threshold;
2: missing, stale or incomplete data. Never calls a model or prints rollout text.
"""
from __future__ import annotations

import argparse
from datetime import datetime
import json
import math
import os
from pathlib import Path
import sys
import time


def latest_snapshot(sessions):
    latest = None
    # ponytail: scan rollouts linearly; add an incremental index if local history becomes slow.
    for path in sessions.glob("*/*/*/rollout-*.jsonl"):
        try:
            with path.open(encoding="utf-8", errors="replace") as stream:
                for line in stream:
                    if '"rate_limits"' not in line:
                        continue
                    try:
                        event = json.loads(line)
                        if not isinstance(event, dict):
                            continue
                        stamp = datetime.fromisoformat(event.get("timestamp", "").replace("Z", "+00:00"))
                        if stamp.tzinfo is None:
                            continue
                        timestamp = stamp.timestamp()
                        payload = event.get("payload")
                        info = payload.get("info") if isinstance(payload, dict) else None
                        for holder in (event, payload, info):
                            snap = holder.get("rate_limits") if isinstance(holder, dict) else None
                            if isinstance(snap, dict) and snap and (latest is None or timestamp >= latest[0]):
                                latest = timestamp, snap, str(path)
                    except (ValueError, TypeError, AttributeError, OverflowError):
                        continue
        except OSError:
            continue
    return latest


def quota_status(snapshot, threshold, max_age, now):
    if snapshot is None or not 0 <= now - snapshot[0] <= max_age:
        return 2
    used = []
    for name in ("primary", "secondary"):
        window = snapshot[1].get(name)
        if not isinstance(window, dict):
            return 2
        percent, reset = window.get("used_percent"), window.get("resets_at")
        if (type(percent) not in (int, float) or not math.isfinite(percent) or not 0 <= percent <= 100
                or type(reset) not in (int, float) or not math.isfinite(reset) or reset <= now):
            return 2
        used.append(percent)
    return int(max(used) >= threshold)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sessions", type=Path,
                        default=Path(os.environ.get("CODEX_HOME", "~/.codex")).expanduser() / "sessions")
    parser.add_argument("--threshold", type=float, default=95)
    parser.add_argument("--max-age", type=int, default=3600, help="Freshness limit in seconds (default one hour).")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    if not 0 < args.threshold <= 100 or args.max_age < 1:
        parser.error("threshold must be in (0, 100] and max-age must be positive")
    snapshot = latest_snapshot(args.sessions)
    code = quota_status(snapshot, args.threshold, args.max_age, time.time())
    # Emit only known quota fields, never arbitrary rollout payloads or transcript text.
    windows = {}
    if snapshot:
        for name in ("primary", "secondary"):
            window = snapshot[1].get(name)
            if isinstance(window, dict):
                windows[name] = {key: window[key] for key in ("used_percent", "resets_at", "window_minutes")
                                 if key in window and type(window[key]) in (int, float) and math.isfinite(window[key])}
    result = {"status": ("below threshold", "threshold reached", "unknown/stale/incomplete")[code],
              "advisory": True, "snapshot_at": snapshot[0] if snapshot else None, "windows": windows}
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print("Codex quota (cached, advisory): " + result["status"])
        for name, window in windows.items():
            print(f"{name}: {window}")
        print("A cached snapshot cannot prove current availability; inspect CLI diagnostics on failure.")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
