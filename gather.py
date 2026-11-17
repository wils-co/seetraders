#!/usr/bin/env python3
"""Fetch live Hyperliquid wallet positions, orders, PnL, and 24h moves."""

from __future__ import annotations

import json
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

API_URL = "https://api.hyperliquid.xyz/info"
ROOT = Path(__file__).resolve().parent
WALLETS_PATH = ROOT / "wallets.json"
OUT_PATH = ROOT / "data.json"


def post_info(payload: dict[str, Any], retries: int = 2) -> Any:
    """POST to Hyperliquid /info with urllib and curl fallback for macOS SSL."""
    body = json.dumps(payload).encode("utf-8")
    last_err: Exception | None = None
    for attempt in range(retries + 1):
        try:
            req = urllib.request.Request(
                API_URL,
                data=body,
                headers={"Content-Type": "application/json", "User-Agent": "trade.wilsco.au/1.0"},
            )
            with urllib.request.urlopen(req, timeout=15) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.URLError as exc:
            if "CERTIFICATE_VERIFY_FAILED" in str(exc):
                out = subprocess.check_output(
                    ["curl", "-sS", "-X", "POST", API_URL, "-H", "Content-Type: application/json", "-d", body.decode("utf-8")],
                    timeout=15,
                )
                return json.loads(out.decode("utf-8"))
            last_err = exc
        except Exception as exc:
            last_err = exc
        if attempt < retries:
            time.sleep(0.5 * (attempt + 1))
    raise RuntimeError(f"Hyperliquid API failed for {payload.get('type')}: {last_err}")


def compute_max_dd(pnl_history: list[list[Any]]) -> float:
    peak = float("-inf")
    max_dd = 0.0
    for _, val in pnl_history:
        fv = float(val)
        if fv > peak:
            peak = fv
        dd = peak - fv
        if dd > max_dd:
            max_dd = dd
    return max_dd


def parse_portfolio(raw_port: list[list[Any]]) -> dict[str, dict[str, float]]:
    pmap = dict(raw_port)
    out: dict[str, dict[str, float]] = {}
    for tf in ("day", "week", "month", "allTime", "perpAllTime"):
        entry = pmap.get(tf)
        if not entry:
            continue
        hist = entry.get("pnlHistory", [])
        pnl = float(hist[-1][1]) if hist else 0.0
        out[tf] = {
            "pnl": round(pnl, 2),
            "vol": round(float(entry.get("vlm", 0)), 2),
            "maxDd": round(compute_max_dd(hist), 2),
        }
    return out


def aggregate_24h_moves(fills: list[dict[str, Any]], label: str, address: str) -> list[dict[str, Any]]:
    """Aggregate raw fills into per-(coin, dir) 24h moves."""
    buckets: dict[tuple[str, str], dict[str, Any]] = {}
    for f in fills:
        coin = f.get("coin", "?")
        direction = f.get("dir", "Trade")
        px = float(f.get("px", 0))
        sz = float(f.get("sz", 0))
        closed_pnl = float(f.get("closedPnl", 0))
        ts = int(f.get("time", 0))
        key = (coin, direction)
        b = buckets.setdefault(
            key,
            {
                "address": address,
                "label": label,
                "coin": coin,
                "dir": direction,
                "notional": 0.0,
                "size": 0.0,
                "closedPnl": 0.0,
                "fills": 0,
                "lastTime": 0,
            },
        )
        b["notional"] += px * sz
        b["size"] += sz
        b["closedPnl"] += closed_pnl
        b["fills"] += 1
        if ts > b["lastTime"]:
            b["lastTime"] = ts

    moves = []
    for b in buckets.values():
        b["notional"] = round(b["notional"], 2)
        b["size"] = round(b["size"], 6)
        b["closedPnl"] = round(b["closedPnl"], 2)
        moves.append(b)
    return moves


def fetch_wallet(meta: dict[str, Any], mids: dict[str, str], since_ms: int) -> dict[str, Any]:
    addr = meta["address"].lower()
    label = meta.get("label", addr[:10])

    ch = post_info({"type": "clearinghouseState", "user": addr})
    ms = ch.get("marginSummary", {})
    acct_val = float(ms.get("accountValue", 0))
    total_ntl = float(ms.get("totalNtlPos", 0))
    margin_used = float(ms.get("totalMarginUsed", 0))

    positions = []
    long_ntl = 0.0
    short_ntl = 0.0
    total_upnl = 0.0

    for item in ch.get("assetPositions", []):
        p = item.get("position", {})
        szi = float(p.get("szi", 0))
        if szi == 0:
            continue
        coin = p["coin"]
        side = "LONG" if szi > 0 else "SHORT"
        ntl = abs(float(p.get("positionValue", 0)))
        upnl = float(p.get("unrealizedPnl", 0))
        entry_px = float(p.get("entryPx", 0))
        liq_px_raw = p.get("liquidationPx")
        liq_px = float(liq_px_raw) if liq_px_raw is not None else None
        mark_px = float(mids[coin]) if coin in mids else None
        lev = p.get("leverage", {})
        roe = float(p.get("returnOnEquity", 0)) * 100.0

        if side == "LONG":
            long_ntl += ntl
        else:
            short_ntl += ntl
        total_upnl += upnl

        positions.append(
            {
                "coin": coin,
                "side": side,
                "szi": szi,
                "notional": round(ntl, 2),
                "entryPx": entry_px,
                "markPx": mark_px,
                "liqPx": liq_px,
                "uPnl": round(upnl, 2),
                "roePct": round(roe, 2),
                "leverage": lev.get("value"),
                "marginType": lev.get("type", "cross"),
            }
        )

    positions.sort(key=lambda x: x["notional"], reverse=True)

    raw_orders = post_info({"type": "openOrders", "user": addr})
    orders = []
    for o in raw_orders:
        limit_px = float(o.get("limitPx", 0))
        sz = float(o.get("sz", 0))
        orders.append(
            {
                "coin": o.get("coin", "?"),
                "side": "BUY" if o.get("side") == "B" else "SELL",
                "limitPx": limit_px,
                "sz": sz,
                "notional": round(limit_px * sz, 2),
                "reduceOnly": bool(o.get("reduceOnly", False)),
                "timestamp": int(o.get("timestamp", 0)),
            }
        )
    orders.sort(key=lambda x: x["notional"], reverse=True)

    raw_port = post_info({"type": "portfolio", "user": addr})
    portfolio = parse_portfolio(raw_port)

    fills_24h = post_info({"type": "userFillsByTime", "user": addr, "startTime": since_ms})
    moves_24h = aggregate_24h_moves(fills_24h, label, addr) if meta.get("copyable", True) else []

    eff_lev = (total_ntl / acct_val) if acct_val > 0 else 0.0

    return {
        "address": addr,
        "label": label,
        "style": meta.get("style", "swing"),
        "copyable": bool(meta.get("copyable", True)),
        "notes": meta.get("notes", ""),
        "accountValue": round(acct_val, 2),
        "totalNotional": round(total_ntl, 2),
        "marginUsed": round(margin_used, 2),
        "effectiveLeverage": round(eff_lev, 2),
        "longNotional": round(long_ntl, 2),
        "shortNotional": round(short_ntl, 2),
        "uPnl": round(total_upnl, 2),
        "openPosCount": len(positions),
        "openOrdersCount": len(orders),
        "positions": positions,
        "openOrders": orders[:25],
        "portfolio": portfolio,
        "fills24hCount": len(fills_24h),
        "moves24h": moves_24h,
    }


def build_consensus(wallets: list[dict[str, Any]]) -> dict[str, Any]:
    copyable = [w for w in wallets if w.get("copyable")]
    total_eq = sum(w["accountValue"] for w in copyable)
    total_long = sum(w["longNotional"] for w in copyable)
    total_short = sum(w["shortNotional"] for w in copyable)
    total_upnl = sum(w["uPnl"] for w in copyable)

    coins: dict[str, dict[str, Any]] = {}
    for w in copyable:
        for p in w["positions"]:
            c = coins.setdefault(
                p["coin"],
                {
                    "coin": p["coin"],
                    "longNotional": 0.0,
                    "shortNotional": 0.0,
                    "longWallets": 0,
                    "shortWallets": 0,
                    "uPnl": 0.0,
                },
            )
            if p["side"] == "LONG":
                c["longNotional"] += p["notional"]
                c["longWallets"] += 1
            else:
                c["shortNotional"] += p["notional"]
                c["shortWallets"] += 1
            c["uPnl"] += p["uPnl"]

    coin_list = []
    for c in coins.values():
        net = c["longNotional"] - c["shortNotional"]
        c["longNotional"] = round(c["longNotional"], 2)
        c["shortNotional"] = round(c["shortNotional"], 2)
        c["netNotional"] = round(net, 2)
        c["uPnl"] = round(c["uPnl"], 2)
        coin_list.append(c)

    coin_list.sort(key=lambda x: abs(x["netNotional"]), reverse=True)

    return {
        "copyableCount": len(copyable),
        "totalEquity": round(total_eq, 2),
        "totalLong": round(total_long, 2),
        "totalShort": round(total_short, 2),
        "netNotional": round(total_long - total_short, 2),
        "totalUpnl": round(total_upnl, 2),
        "topCoins": coin_list[:15],
    }


def main() -> int:
    cfg = json.loads(WALLETS_PATH.read_text(encoding="utf-8"))
    enabled = [w for w in cfg.get("wallets", []) if w.get("enabled", True)]

    now_dt = datetime.now(timezone.utc)
    since_ms = int(now_dt.timestamp() * 1000) - 86_400_000
    mids = post_info({"type": "allMids"})

    wallets_out = []
    errors = []
    for w in enabled:
        try:
            wallets_out.append(fetch_wallet(w, mids, since_ms))
        except Exception as exc:
            errors.append({"address": w.get("address"), "error": str(exc)})
            print(f"WARN: failed {w.get('address')}: {exc}", file=sys.stderr)

    all_moves = []
    for w in wallets_out:
        all_moves.extend(w.pop("moves24h", []))
    all_moves.sort(key=lambda x: x["lastTime"], reverse=True)

    payload = {
        "generatedAt": now_dt.isoformat(),
        "generatedMs": int(now_dt.timestamp() * 1000),
        "consensus": build_consensus(wallets_out),
        "moves24h": all_moves[:60],
        "wallets": wallets_out,
        "errors": errors,
    }

    OUT_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Wrote {OUT_PATH.name}: {len(wallets_out)} wallets, {len(all_moves)} 24h moves, {len(errors)} errors")
    return 0 if wallets_out else 1


if __name__ == "__main__":
    raise SystemExit(main())
