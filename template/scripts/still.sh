#!/bin/zsh
# Export stills: still.sh <Comp: Video|Overlay|G1..G8> <frame numbers starting at 1, comma-separated> <output dir (absolute path)> [tag]
# ⚠ Use one tag per build group (such as g3). After code changes, run rm -rf build_dev_<tag> before rerunning. Do not switch to a new tag each time (each bundle is ≈40MB).
set -e
ROOT=$(cd "$(dirname "$0")/.." && pwd); cd "$ROOT"
COMP=$1; FRAMES=$2; OUT=$3; TAG=${4:-$COMP}
[ -n "$COMP" ] && [ -n "$FRAMES" ] && [ -n "$OUT" ] || { echo "usage: still.sh <Comp> <frames> <out_dir_abs> [tag]"; exit 1; }
B=build_dev_$TAG
[ -d "$B" ] || npx remotion bundle src/index.ts --out-dir "$B" --log=error
mkdir -p "$OUT"
for N in ${(s:,:)FRAMES}; do
  npx remotion still "$B" "$COMP" "$OUT/f_$(printf %04d $N).png" --frame=$((N-1)) --log=error
done
# Clean up remotion temporary bundles untouched for more than 4 hours (only clearly dead ones: other remotion projects or agents may be rendering on this machine,
# and a short threshold would delete a bundle someone else is using). Set CLEAN_TMP=0 to turn this off.
[ "${CLEAN_TMP:-1}" = 1 ] && find "${TMPDIR:-/tmp}" -maxdepth 1 -name 'remotion-webpack-bundle-*' -mmin +240 -exec rm -rf {} + 2>/dev/null
ls "$OUT" | wc -l
