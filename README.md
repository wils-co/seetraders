# trade.wilsco.au

Read-only Hyperliquid top-trader position tracker, consensus view, and 24h move feed.
Built with zero external Python/JS dependencies so it runs identically on GitHub Actions and locally on macOS.

## Architecture

- `wallets.json` — curated list of wallets (`style`, `copyable`, `enabled`, `notes`).
- `gather.py` — queries Hyperliquid `/info` (`clearinghouseState`, `openOrders`, `portfolio`, `userFillsByTime`, `allMids`) and writes `data.json`.
- `build_html.py` — compiles `data.json` into a self-contained `public/index.html`, `public/status.json`, and `public/CNAME`.
- `.github/workflows/deploy.yml` — runs every 30 minutes on GitHub Actions and deploys `./public` to GitHub Pages (keeps `main` free of automated data commits).

## Run Locally

```bash
chmod +x run.sh
./run.sh
open public/index.html
```

## GitHub Pages + Custom Domain Setup

1. In GitHub repo **Settings → Pages → Build and deployment**, set **Source** to **GitHub Actions**.
2. In Cloudflare DNS for `wilsco.au`, add a `CNAME` record:
   - Name: `trade`
   - Target: `wils-co.github.io`
   - Proxy status: DNS only (until SSL cert issues, then Proxied works too).
3. In GitHub repo **Settings → Pages → Custom domain**, enter `trade.wilsco.au` and enable **Enforce HTTPS**.
