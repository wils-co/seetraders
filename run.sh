#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"
python3 gather.py
python3 build_html.py
echo "Built public/index.html ($(wc -c < public/index.html | tr -d ' ') bytes)"
