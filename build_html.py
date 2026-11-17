#!/usr/bin/env python3
"""Build self-contained public/index.html, public/status.json, and public/CNAME."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA_PATH = ROOT / "data.json"
PUBLIC_DIR = ROOT / "public"
OUT_HTML = PUBLIC_DIR / "index.html"
OUT_STATUS = PUBLIC_DIR / "status.json"
OUT_CNAME = PUBLIC_DIR / "CNAME"

HTML_TEMPLATE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>trade.wilsco.au — Hyperliquid Top Trader Tracker</title>
<style>
  :root {
    --bg: #0b0e14;
    --card: #121722;
    --card-2: #171d2b;
    --border: #232b3d;
    --row-border: rgba(35, 43, 61, 0.55);
    --text: #e6edf3;
    --muted: #8b949e;
    --green: #2ea043;
    --green-bg: rgba(46, 160, 67, 0.14);
    --red: #f85149;
    --red-bg: rgba(248, 81, 73, 0.14);
    --amber: #d29922;
    --amber-bg: rgba(210, 153, 34, 0.14);
    --blue: #58a6ff;
    --blue-bg: rgba(88, 166, 255, 0.14);
  }
  :root[data-theme="light"] {
    --bg: #f6f8fa;
    --card: #ffffff;
    --card-2: #f0f3f6;
    --border: #d0d7de;
    --row-border: rgba(208, 215, 222, 0.7);
    --text: #1f2328;
    --muted: #59636e;
    --green: #1a7f37;
    --green-bg: rgba(26, 127, 55, 0.12);
    --red: #cf222e;
    --red-bg: rgba(207, 34, 46, 0.12);
    --amber: #9a6700;
    --amber-bg: rgba(154, 103, 0, 0.12);
    --blue: #0969da;
    --blue-bg: rgba(9, 105, 218, 0.12);
  }
  .theme-btn {
    background: var(--card-2); color: var(--text); border: 1px solid var(--border);
    border-radius: 6px; padding: 5px 10px; font-size: 11px; font-weight: 600; cursor: pointer;
  }
  .theme-btn:hover { border-color: var(--blue); }
  * { box-sizing: border-box; }
  body {
    margin: 0;
    background: var(--bg);
    color: var(--text);
    font-family: ui-sans-serif, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    font-size: 13px;
    line-height: 1.45;
  }
  .mono { font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace; }
  .wrap { max-width: 1360px; margin: 0 auto; padding: 16px; }
  header {
    display: flex; flex-wrap: wrap; gap: 12px; align-items: center; justify-content: space-between;
    border-bottom: 1px solid var(--border); padding-bottom: 14px; margin-bottom: 16px;
  }
  .brand h1 { margin: 0; font-size: 18px; letter-spacing: -0.01em; }
  .brand .sub { color: var(--muted); font-size: 12px; margin-top: 2px; }
  .controls {
    display: flex; flex-wrap: wrap; gap: 10px; align-items: center;
    background: var(--card); border: 1px solid var(--border); border-radius: 8px; padding: 8px 12px;
  }
  .controls label { color: var(--muted); font-size: 11px; display: flex; flex-direction: column; gap: 2px; }
  .controls input {
    background: var(--bg); color: var(--text); border: 1px solid var(--border); border-radius: 5px;
    padding: 4px 8px; width: 105px; font-size: 12px;
  }
  .pill {
    display: inline-flex; align-items: center; gap: 5px; padding: 2px 8px; border-radius: 999px;
    font-size: 11px; font-weight: 600; border: 1px solid transparent;
  }
  .pill.green { color: var(--green); background: var(--green-bg); border-color: rgba(46,160,67,0.3); }
  .pill.red { color: var(--red); background: var(--red-bg); border-color: rgba(248,81,73,0.3); }
  .pill.amber { color: var(--amber); background: var(--amber-bg); border-color: rgba(210,153,34,0.3); }
  .pill.blue { color: var(--blue); background: var(--blue-bg); border-color: rgba(88,166,255,0.3); }
  .pill.muted { color: var(--muted); background: var(--card-2); border-color: var(--border); }

  .grid-top { display: grid; grid-template-columns: 1.2fr 1fr; gap: 16px; margin-bottom: 16px; }
  @media (max-width: 960px) { .grid-top { grid-template-columns: 1fr; } }

  .card {
    background: var(--card); border: 1px solid var(--border); border-radius: 10px; padding: 14px;
    margin-bottom: 14px;
  }
  .card h2 { margin: 0 0 10px; font-size: 14px; font-weight: 600; display: flex; align-items: center; justify-content: space-between; }
  .kpis { display: grid; grid-template-columns: repeat(auto-fit, minmax(130px, 1fr)); gap: 10px; margin-bottom: 12px; }
  .kpi { background: var(--card-2); border: 1px solid var(--border); border-radius: 8px; padding: 9px 10px; }
  .kpi .k { color: var(--muted); font-size: 11px; }
  .kpi .v { font-size: 15px; font-weight: 700; margin-top: 2px; }

  .bar-wrap { height: 8px; background: var(--red); border-radius: 999px; overflow: hidden; margin: 8px 0 12px; }
  .bar-long { height: 100%; background: var(--green); }

  table { width: 100%; border-collapse: collapse; font-size: 12px; }
  th { text-align: left; color: var(--muted); font-weight: 600; font-size: 11px; padding: 6px 8px; border-bottom: 1px solid var(--border); white-space: nowrap; }
  td { padding: 6px 8px; border-bottom: 1px solid var(--row-border); white-space: nowrap; }
  tr:last-child td { border-bottom: none; }
  .num { text-align: right; font-variant-numeric: tabular-nums; }
  .pos { color: var(--green); }
  .neg { color: var(--red); }

  .table-scroll { overflow-x: auto; max-height: 360px; overflow-y: auto; }
  .wallet-head { display: flex; flex-wrap: wrap; gap: 10px; align-items: center; justify-content: space-between; margin-bottom: 10px; }
  .wallet-title { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; }
  .wallet-title a { color: var(--blue); text-decoration: none; font-size: 11px; }
  .wallet-title a:hover { text-decoration: underline; }
  .wallet-notes { color: var(--muted); font-size: 12px; margin-bottom: 10px; }

  .tabs { display: flex; gap: 6px; margin-bottom: 8px; }
  .tab-btn {
    background: var(--card-2); color: var(--muted); border: 1px solid var(--border);
    border-radius: 6px; padding: 4px 10px; font-size: 11px; cursor: pointer;
  }
  .tab-btn.active { color: var(--text); border-color: var(--blue); background: var(--blue-bg); }
  .nav-tabs { display: flex; gap: 8px; margin-bottom: 16px; border-bottom: 1px solid var(--border); padding-bottom: 10px; }
  .nav-tab {
    background: var(--card); color: var(--muted); border: 1px solid var(--border);
    border-radius: 8px; padding: 7px 14px; font-size: 13px; font-weight: 600; cursor: pointer;
  }
  .nav-tab.active { color: var(--text); border-color: var(--blue); background: var(--blue-bg); }
  .mkt-link { color: var(--text); text-decoration: none; }
  .mkt-link:hover { color: var(--blue); text-decoration: underline; }
  .hidden { display: none; }
  footer { color: var(--muted); font-size: 11px; text-align: center; padding: 16px 0 8px; }
</style>
</head>
<body>
<div class="wrap">
  <header>
    <div class="brand">
      <h1>trade.wilsco.au <span class="pill blue">Top Traders</span></h1>
      <div class="sub" id="metaLine">Loading...</div>
    </div>
    <div class="controls" title="Stored locally in your browser only (never uploaded)">
      <label>My Equity (USDC)
        <input id="myEquity" type="number" min="0" step="100" value="10000" />
      </label>
      <label>Max Lev Cap (x)
        <input id="maxLev" type="number" min="0.5" max="50" step="0.5" value="2" />
      </label>
      <span id="freshBadge" class="pill muted">—</span>
      <button id="themeToggle" class="theme-btn" type="button" title="Toggle dark/light mode">☀ Light</button>
    </div>
  </header>

  <nav class="nav-tabs">
    <button class="nav-tab active" id="nav-hl" onclick="switchPlatform('hl')">Hyperliquid <span class="pill muted" id="hlTabCount"></span></button>
    <button class="nav-tab" id="nav-pm" onclick="switchPlatform('pm')">Polymarket <span class="pill muted" id="pmTabCount"></span></button>
  </nav>

  <div id="view-hl">
  <div class="grid-top">
    <section class="card">
      <h2>
        <span>Consensus & Net Exposure <span class="pill muted" id="copyCount"></span></span>
      </h2>
      <div class="kpis" id="consensusKpis"></div>
      <div style="display:flex;justify-content:space-between;font-size:11px;color:var(--muted);">
        <span id="longPctLabel">Long —</span>
        <span id="shortPctLabel">Short —</span>
      </div>
      <div class="bar-wrap"><div class="bar-long" id="lsBar" style="width:50%"></div></div>
      <div class="table-scroll">
        <table>
          <thead>
            <tr>
              <th>Coin</th>
              <th class="num">Long $</th>
              <th class="num">Short $</th>
              <th class="num">Net $</th>
              <th class="num">Wallets (L/S)</th>
              <th class="num">uPnL</th>
            </tr>
          </thead>
          <tbody id="topCoinsBody"></tbody>
        </table>
      </div>
    </section>

    <section class="card">
      <h2>
        <span>Last 24h Moves (Copyable Wallets)</span>
        <span class="pill muted" id="movesCount"></span>
      </h2>
      <div class="table-scroll" style="max-height: 410px;">
        <table>
          <thead>
            <tr>
              <th>Time</th>
              <th>Wallet</th>
              <th>Coin</th>
              <th>Action</th>
              <th class="num">Notional</th>
              <th class="num">Realized</th>
            </tr>
          </thead>
          <tbody id="movesBody"></tbody>
        </table>
      </div>
    </section>
  </div>

  <div id="walletsContainer"></div>
  </div><!-- /view-hl -->

  <div id="view-pm" class="hidden">
    <div class="grid-top">
      <section class="card">
        <h2>
          <span>Top Markets (Tracked Polymarket Whales)</span>
          <span class="pill muted" id="pmSummaryCount"></span>
        </h2>
        <div class="kpis" id="pmKpis"></div>
        <div class="table-scroll">
          <table>
            <thead>
              <tr>
                <th>Market</th>
                <th>Outcome</th>
                <th class="num">Price</th>
                <th class="num">Wallets</th>
                <th class="num">Open Value</th>
                <th class="num">uPnL</th>
              </tr>
            </thead>
            <tbody id="pmTopMarketsBody"></tbody>
          </table>
        </div>
      </section>

      <section class="card">
        <h2>
          <span>Last 24h Trades</span>
          <span class="pill muted" id="pmMovesCount"></span>
        </h2>
        <div class="table-scroll" style="max-height: 410px;">
          <table>
            <thead>
              <tr>
                <th>Time</th>
                <th>Wallet</th>
                <th>Market</th>
                <th>Side</th>
                <th class="num">Notional</th>
              </tr>
            </thead>
            <tbody id="pmMovesBody"></tbody>
          </table>
        </div>
      </section>
    </div>

    <div id="pmWalletsContainer"></div>
  </div><!-- /view-pm -->

  <footer>
    Read-only snapshot from public Hyperliquid <code>/info</code> & Polymarket Data <code>/v2</code> APIs. Not financial advice. Copy-sizing & theme stay in browser <code>localStorage</code>.
  </footer>
</div>

<script>
const DATA = __DATA_JSON__;

const fmtUsd = (n, decimals = 0) => {
  if (n === null || n === undefined || Number.isNaN(n)) return "—";
  const sign = n < 0 ? "-" : "";
  const abs = Math.abs(n);
  if (abs >= 1e6) return sign + "$" + (abs / 1e6).toFixed(2) + "M";
  if (abs >= 1e3 && decimals === 0) return sign + "$" + (abs / 1e3).toFixed(1) + "k";
  return sign + "$" + abs.toLocaleString("en-US", { minimumFractionDigits: decimals, maximumFractionDigits: decimals });
};
const fmtPx = (n) => {
  if (n === null || n === undefined) return "—";
  if (n >= 1000) return n.toLocaleString("en-US", { maximumFractionDigits: 2 });
  if (n >= 1) return n.toFixed(4).replace(/\.?0+$/, "");
  return n.toFixed(6).replace(/\.?0+$/, "");
};
const clsPnL = (n) => (n > 0 ? "pos" : n < 0 ? "neg" : "");
const shortAddr = (a) => a.slice(0, 6) + "…" + a.slice(-4);

const eqInput = document.getElementById("myEquity");
const levInput = document.getElementById("maxLev");
eqInput.value = localStorage.getItem("tw_equity") || "10000";
levInput.value = localStorage.getItem("tw_maxlev") || "2";

function renderMeta() {
  const gen = new Date(DATA.generatedAt);
  const ageMin = Math.max(0, Math.round((Date.now() - gen.getTime()) / 60000));
  const melb = gen.toLocaleString("en-AU", { timeZone: "Australia/Melbourne", dateStyle: "medium", timeStyle: "short" });
  document.getElementById("metaLine").textContent = `Updated ${melb} AEDT (${ageMin}m ago) · ${DATA.wallets.length} tracked wallets`;
  const badge = document.getElementById("freshBadge");
  if (ageMin <= 45) {
    badge.className = "pill green";
    badge.textContent = `Fresh (${ageMin}m)`;
  } else if (ageMin <= 120) {
    badge.className = "pill amber";
    badge.textContent = `Aging (${ageMin}m)`;
  } else {
    badge.className = "pill red";
    badge.textContent = `Stale (${ageMin}m)`;
  }
}

function renderConsensus() {
  const c = DATA.consensus;
  document.getElementById("copyCount").textContent = `${c.copyableCount} copyable`;
  const kpis = [
    { k: "Combined Equity", v: fmtUsd(c.totalEquity), cls: "" },
    { k: "Total Long", v: fmtUsd(c.totalLong), cls: "pos" },
    { k: "Total Short", v: fmtUsd(c.totalShort), cls: "neg" },
    { k: "Net Exposure", v: fmtUsd(c.netNotional), cls: clsPnL(c.netNotional) },
    { k: "Open uPnL", v: fmtUsd(c.totalUpnl), cls: clsPnL(c.totalUpnl) },
  ];
  document.getElementById("consensusKpis").innerHTML = kpis
    .map(x => `<div class="kpi"><div class="k">${x.k}</div><div class="v mono ${x.cls}">${x.v}</div></div>`)
    .join("");

  const tot = c.totalLong + c.totalShort;
  const lp = tot > 0 ? (c.totalLong / tot) * 100 : 50;
  document.getElementById("lsBar").style.width = lp.toFixed(1) + "%";
  document.getElementById("longPctLabel").textContent = `Long ${lp.toFixed(1)}%`;
  document.getElementById("shortPctLabel").textContent = `Short ${(100 - lp).toFixed(1)}%`;

  document.getElementById("topCoinsBody").innerHTML = c.topCoins.map(x => `
    <tr>
      <td class="mono"><strong>${x.coin}</strong></td>
      <td class="num mono pos">${x.longNotional > 0 ? fmtUsd(x.longNotional) : "—"}</td>
      <td class="num mono neg">${x.shortNotional > 0 ? fmtUsd(x.shortNotional) : "—"}</td>
      <td class="num mono ${clsPnL(x.netNotional)}">${fmtUsd(x.netNotional)}</td>
      <td class="num mono">${x.longWallets}L / ${x.shortWallets}S</td>
      <td class="num mono ${clsPnL(x.uPnl)}">${fmtUsd(x.uPnl)}</td>
    </tr>
  `).join("");
}

function renderMoves() {
  const moves = DATA.moves24h || [];
  document.getElementById("movesCount").textContent = `${moves.length} events`;
  if (!moves.length) {
    document.getElementById("movesBody").innerHTML = `<tr><td colspan="6" style="color:var(--muted)">No fills in last 24h</td></tr>`;
    return;
  }
  document.getElementById("movesBody").innerHTML = moves.map(m => {
    const t = new Date(m.lastTime).toLocaleTimeString("en-AU", { timeZone: "Australia/Melbourne", hour: "2-digit", minute: "2-digit" });
    const isShort = m.dir.toLowerCase().includes("short");
    const isLong = m.dir.toLowerCase().includes("long");
    const dCls = isLong ? "pos" : isShort ? "neg" : "";
    return `
      <tr>
        <td class="mono" style="color:var(--muted)">${t}</td>
        <td>${m.label}</td>
        <td class="mono"><strong>${m.coin}</strong></td>
        <td class="${dCls}">${m.dir} <span style="color:var(--muted)">(${m.fills}x)</span></td>
        <td class="num mono">${fmtUsd(m.notional)}</td>
        <td class="num mono ${clsPnL(m.closedPnl)}">${m.closedPnl !== 0 ? fmtUsd(m.closedPnl) : "—"}</td>
      </tr>
    `;
  }).join("");
}

function calcCopySize(posNotional, walletEquity, walletTotalNotional, myEq, maxLev) {
  if (myEq <= 0 || walletTotalNotional <= 0) return 0;
  // Cap effective denominator so profit-sweeping wallets don't blow up copy sizing
  const effBase = Math.max(walletEquity, walletTotalNotional / maxLev);
  return (posNotional / effBase) * myEq;
}

function renderWallets() {
  const myEq = parseFloat(eqInput.value) || 0;
  const maxLev = Math.max(0.5, parseFloat(levInput.value) || 2);
  const container = document.getElementById("walletsContainer");

  container.innerHTML = DATA.wallets.map((w, idx) => {
    const port = w.portfolio || {};
    const dPnl = port.day ? port.day.pnl : 0;
    const wPnl = port.week ? port.week.pnl : 0;
    const mPnl = port.month ? port.month.pnl : 0;
    const aPnl = port.allTime ? port.allTime.pnl : 0;
    const levCls = w.effectiveLeverage > 5 ? "amber" : "muted";
    const styleBadge = w.copyable
      ? `<span class="pill green">${w.style} · copyable</span>`
      : `<span class="pill red">${w.style} · excluded</span>`;

    const posRows = w.positions.length ? w.positions.map(p => {
      const sCls = p.side === "LONG" ? "pos" : "neg";
      const copySz = w.copyable ? calcCopySize(p.notional, w.accountValue, w.totalNotional, myEq, maxLev) : 0;
      return `
        <tr>
          <td class="mono"><strong>${p.coin}</strong></td>
          <td class="mono ${sCls}">${p.side}</td>
          <td class="num mono">${fmtUsd(p.notional)}</td>
          <td class="num mono" style="color:var(--blue)">${w.copyable ? fmtUsd(copySz) : "—"}</td>
          <td class="num mono">${fmtPx(p.entryPx)}</td>
          <td class="num mono">${fmtPx(p.markPx)}</td>
          <td class="num mono" style="color:var(--muted)">${fmtPx(p.liqPx)}</td>
          <td class="num mono ${clsPnL(p.uPnl)}">${fmtUsd(p.uPnl)}</td>
          <td class="num mono">${p.leverage || "?"}x ${p.marginType}</td>
        </tr>
      `;
    }).join("") : `<tr><td colspan="9" style="color:var(--muted)">Flat — no open positions</td></tr>`;

    const ordRows = w.openOrders.length ? w.openOrders.map(o => `
      <tr>
        <td class="mono"><strong>${o.coin}</strong></td>
        <td class="mono ${o.side === "BUY" ? "pos" : "neg"}">${o.side}</td>
        <td class="num mono">${fmtPx(o.limitPx)}</td>
        <td class="num mono">${o.sz}</td>
        <td class="num mono">${fmtUsd(o.notional)}</td>
        <td>${o.reduceOnly ? '<span class="pill amber">Reduce-Only</span>' : '<span class="pill muted">Entry/Add</span>'}</td>
      </tr>
    `).join("") : `<tr><td colspan="6" style="color:var(--muted)">No resting orders</td></tr>`;

    return `
      <section class="card">
        <div class="wallet-head">
          <div class="wallet-title">
            <strong>${w.label}</strong>
            <span class="mono" style="color:var(--muted)">${shortAddr(w.address)}</span>
            ${styleBadge}
            <span class="pill ${levCls}">${w.effectiveLeverage}x eff. lev</span>
            <a href="https://hypurrscan.io/address/${w.address}" target="_blank" rel="noopener">Hypurrscan ↗</a>
            <a href="https://app.hyperliquid.xyz/explorer/address/${w.address}" target="_blank" rel="noopener">HL Explorer ↗</a>
          </div>
          <div class="mono" style="font-size:12px;">
            24h: <span class="${clsPnL(dPnl)}">${fmtUsd(dPnl)}</span> ·
            7d: <span class="${clsPnL(wPnl)}">${fmtUsd(wPnl)}</span> ·
            30d: <span class="${clsPnL(mPnl)}">${fmtUsd(mPnl)}</span> ·
            All: <strong class="${clsPnL(aPnl)}">${fmtUsd(aPnl)}</strong>
          </div>
        </div>
        ${w.notes ? `<div class="wallet-notes">${w.notes}</div>` : ""}
        <div class="kpis">
          <div class="kpi"><div class="k">Account Equity</div><div class="v mono">${fmtUsd(w.accountValue)}</div></div>
          <div class="kpi"><div class="k">Total Notional</div><div class="v mono">${fmtUsd(w.totalNotional)}</div></div>
          <div class="kpi"><div class="k">Long / Short</div><div class="v mono"><span class="pos">${fmtUsd(w.longNotional)}</span> / <span class="neg">${fmtUsd(w.shortNotional)}</span></div></div>
          <div class="kpi"><div class="k">Unrealized PnL</div><div class="v mono ${clsPnL(w.uPnl)}">${fmtUsd(w.uPnl)}</div></div>
          <div class="kpi"><div class="k">24h Fills</div><div class="v mono">${w.fills24hCount}</div></div>
        </div>

        <div class="tabs">
          <button class="tab-btn active" onclick="switchTab(${idx}, 'pos', this)">Open Positions (${w.openPosCount})</button>
          <button class="tab-btn" onclick="switchTab(${idx}, 'ord', this)">Resting Orders (${w.openOrdersCount})</button>
        </div>

        <div id="tab-pos-${idx}" class="table-scroll">
          <table>
            <thead>
              <tr>
                <th>Coin</th><th>Side</th><th class="num">Notional</th><th class="num">Copy Size</th>
                <th class="num">Entry</th><th class="num">Mark</th><th class="num">Liq</th>
                <th class="num">uPnL</th><th class="num">Lev</th>
              </tr>
            </thead>
            <tbody>${posRows}</tbody>
          </table>
        </div>
        <div id="tab-ord-${idx}" class="table-scroll hidden">
          <table>
            <thead>
              <tr><th>Coin</th><th>Side</th><th class="num">Limit Px</th><th class="num">Size</th><th class="num">Notional</th><th>Type</th></tr>
            </thead>
            <tbody>${ordRows}</tbody>
          </table>
        </div>
      </section>
    `;
  }).join("");
}

window.switchTab = (idx, which, btn) => {
  const posEl = document.getElementById(`tab-pos-${idx}`);
  const ordEl = document.getElementById(`tab-ord-${idx}`);
  posEl.classList.toggle("hidden", which !== "pos");
  ordEl.classList.toggle("hidden", which !== "ord");
  btn.parentElement.querySelectorAll(".tab-btn").forEach(b => b.classList.remove("active"));
  btn.classList.add("active");
};

eqInput.addEventListener("input", () => { localStorage.setItem("tw_equity", eqInput.value); renderWallets(); });
levInput.addEventListener("input", () => { localStorage.setItem("tw_maxlev", levInput.value); renderWallets(); });

const themeBtn = document.getElementById("themeToggle");
function applyTheme(t) {
  document.documentElement.setAttribute("data-theme", t);
  themeBtn.textContent = t === "light" ? "🌙 Dark" : "☀ Light";
  localStorage.setItem("tw_theme", t);
}
applyTheme(localStorage.getItem("tw_theme") || "dark");
themeBtn.addEventListener("click", () => {
  const cur = document.documentElement.getAttribute("data-theme") || "dark";
  applyTheme(cur === "dark" ? "light" : "dark");
});

function renderPolymarket() {
  const pm = DATA.polymarket || { summary: { walletCount: 0, totalOpenValue: 0, totalUpnl: 0, topMarkets: [] }, moves24h: [], wallets: [] };
  const s = pm.summary || {};
  document.getElementById("hlTabCount").textContent = DATA.wallets.length;
  document.getElementById("pmTabCount").textContent = (pm.wallets || []).length;
  document.getElementById("pmSummaryCount").textContent = `${s.walletCount || 0} tracked`;

  const kpis = [
    { k: "Tracked Whales", v: String(s.walletCount || 0), cls: "" },
    { k: "Combined Open Value", v: fmtUsd(s.totalOpenValue || 0), cls: "" },
    { k: "Open uPnL", v: fmtUsd(s.totalUpnl || 0), cls: clsPnL(s.totalUpnl || 0) },
  ];
  document.getElementById("pmKpis").innerHTML = kpis
    .map(x => `<div class="kpi"><div class="k">${x.k}</div><div class="v mono ${x.cls}">${x.v}</div></div>`)
    .join("");

  const trunc = (str, n = 48) => (str && str.length > n ? str.slice(0, n - 1) + "…" : (str || "—"));
  const mktUrl = (slug) => slug ? `https://polymarket.com/event/${slug}` : "https://polymarket.com";

  document.getElementById("pmTopMarketsBody").innerHTML = (s.topMarkets || []).map(m => `
    <tr>
      <td title="${(m.title || "").replace(/"/g, "&quot;")}"><a class="mkt-link" href="${mktUrl(m.eventSlug)}" target="_blank" rel="noopener">${trunc(m.title, 44)}</a></td>
      <td><span class="pill ${m.outcome === "Yes" ? "green" : m.outcome === "No" ? "red" : "blue"}">${m.outcome}</span></td>
      <td class="num mono">${(m.currentPrice * 100).toFixed(1)}¢</td>
      <td class="num mono">${m.wallets}</td>
      <td class="num mono">${fmtUsd(m.totalValue)}</td>
      <td class="num mono ${clsPnL(m.uPnl)}">${fmtUsd(m.uPnl)}</td>
    </tr>
  `).join("") || `<tr><td colspan="6" style="color:var(--muted)">No open markets</td></tr>`;

  const moves = pm.moves24h || [];
  document.getElementById("pmMovesCount").textContent = `${moves.length} events`;
  document.getElementById("pmMovesBody").innerHTML = moves.length ? moves.map(m => {
    const t = new Date(m.lastTime * 1000).toLocaleTimeString("en-AU", { timeZone: "Australia/Melbourne", hour: "2-digit", minute: "2-digit" });
    const sCls = m.side === "BUY" ? "pos" : "neg";
    return `
      <tr>
        <td class="mono" style="color:var(--muted)">${t}</td>
        <td>${m.label}</td>
        <td title="${(m.title || "").replace(/"/g, "&quot;")}"><a class="mkt-link" href="${mktUrl(m.eventSlug)}" target="_blank" rel="noopener">${trunc(m.title, 34)}</a> <span style="color:var(--muted)">(${m.outcome})</span></td>
        <td class="mono ${sCls}">${m.side} <span style="color:var(--muted)">(${m.fills}x)</span></td>
        <td class="num mono">${fmtUsd(m.notional)}</td>
      </tr>
    `;
  }).join("") : `<tr><td colspan="5" style="color:var(--muted)">No trades in last 24h</td></tr>`;

  document.getElementById("pmWalletsContainer").innerHTML = (pm.wallets || []).map(w => {
    const rankStr = w.monthRank ? `#${w.monthRank} 30d` : "conviction";
    const posRows = (w.positions || []).length ? w.positions.map(p => `
      <tr>
        <td title="${(p.title || "").replace(/"/g, "&quot;")}"><a class="mkt-link" href="${mktUrl(p.eventSlug)}" target="_blank" rel="noopener">${trunc(p.title, 52)}</a></td>
        <td><span class="pill ${p.outcome === "Yes" ? "green" : p.outcome === "No" ? "red" : "blue"}">${p.outcome}</span></td>
        <td class="num mono">${fmtUsd(p.currentValue)}</td>
        <td class="num mono">${(p.avgPrice * 100).toFixed(1)}¢</td>
        <td class="num mono">${(p.currentPrice * 100).toFixed(1)}¢</td>
        <td class="num mono ${clsPnL(p.uPnl)}">${fmtUsd(p.uPnl)}</td>
        <td class="num mono ${clsPnL(p.pctPnl)}">${p.pctPnl > 0 ? "+" : ""}${p.pctPnl}%</td>
        <td class="mono" style="color:var(--muted)">${p.endDate || "—"}</td>
      </tr>
    `).join("") : `<tr><td colspan="8" style="color:var(--muted)">No open positions</td></tr>`;

    return `
      <section class="card">
        <div class="wallet-head">
          <div class="wallet-title">
            <strong>${w.label}</strong>
            <span class="mono" style="color:var(--muted)">${shortAddr(w.address)}</span>
            <span class="pill green">${rankStr}</span>
            <a href="https://polymarket.com/profile/${w.address}" target="_blank" rel="noopener">Polymarket Profile ↗</a>
          </div>
          <div class="mono" style="font-size:12px;">
            ${w.monthPnl !== null ? `30d: <span class="${clsPnL(w.monthPnl)}">${fmtUsd(w.monthPnl)}</span> · ` : ""}
            ${w.monthVol !== null ? `30d Vol: <span>${fmtUsd(w.monthVol)}</span> · ` : ""}
            ${w.allPnl !== null ? `All: <strong class="${clsPnL(w.allPnl)}">${fmtUsd(w.allPnl)}</strong>` : ""}
          </div>
        </div>
        ${w.notes ? `<div class="wallet-notes">${w.notes}</div>` : ""}
        <div class="kpis">
          <div class="kpi"><div class="k">Open Value</div><div class="v mono">${fmtUsd(w.openValue)}</div></div>
          <div class="kpi"><div class="k">Cost Basis</div><div class="v mono">${fmtUsd(w.totalCost)}</div></div>
          <div class="kpi"><div class="k">Unrealized PnL</div><div class="v mono ${clsPnL(w.uPnl)}">${fmtUsd(w.uPnl)}</div></div>
          <div class="kpi"><div class="k">Open Markets</div><div class="v mono">${w.openPosCount}</div></div>
          <div class="kpi"><div class="k">24h Trades</div><div class="v mono">${w.trades24hCount}</div></div>
        </div>
        <div class="table-scroll">
          <table>
            <thead>
              <tr>
                <th>Market</th><th>Outcome</th><th class="num">Value</th><th class="num">Avg Px</th>
                <th class="num">Curr Px</th><th class="num">uPnL</th><th class="num">ROI</th><th>Ends</th>
              </tr>
            </thead>
            <tbody>${posRows}</tbody>
          </table>
        </div>
      </section>
    `;
  }).join("");
}

window.switchPlatform = (which) => {
  const isPm = which === "pm";
  document.getElementById("view-hl").classList.toggle("hidden", isPm);
  document.getElementById("view-pm").classList.toggle("hidden", !isPm);
  document.getElementById("nav-hl").classList.toggle("active", !isPm);
  document.getElementById("nav-pm").classList.toggle("active", isPm);
  localStorage.setItem("tw_platform", which);
};

renderMeta();
renderConsensus();
renderMoves();
renderWallets();
renderPolymarket();
const initPlat = location.hash === "#polymarket" ? "pm" : (localStorage.getItem("tw_platform") || "hl");
switchPlatform(initPlat);
</script>
</body>
</html>
"""


def main() -> int:
    data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    PUBLIC_DIR.mkdir(parents=True, exist_ok=True)

    html = HTML_TEMPLATE.replace("__DATA_JSON__", json.dumps(data))
    OUT_HTML.write_text(html, encoding="utf-8")
    OUT_CNAME.write_text("trade.wilsco.au\n", encoding="utf-8")

    status = {
        "generatedAt": data["generatedAt"],
        "walletCount": len(data.get("wallets", [])),
        "copyableCount": data.get("consensus", {}).get("copyableCount", 0),
        "moves24hCount": len(data.get("moves24h", [])),
        "errors": data.get("errors", []),
    }
    OUT_STATUS.write_text(json.dumps(status, indent=2), encoding="utf-8")
    print(f"Built {OUT_HTML} ({len(html)} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
