#!/bin/bash
# Pull the two Omarchy theme repos into omarchy/. They stay the source of
# truth for colours and wallpapers; this repo only packages them.
set -euo pipefail
cd "$(dirname "$0")/.."

for theme in fwu fwu-dark; do
  repo="https://github.com/FWU-DE/omarchy-$theme-theme.git"
  tmp=$(mktemp -d)
  git clone --quiet --depth 1 "$repo" "$tmp"
  rsync -a --delete --exclude .git "$tmp/" "omarchy/$theme/"
  echo "$theme: $(git -C "$tmp" rev-parse --short HEAD)"
  rm -rf "$tmp"
done
