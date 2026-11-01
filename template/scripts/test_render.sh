#!/bin/zsh
# Test-render 30 frames to measure fps: test_render.sh <Comp> <start frame, starting at 1> [tag]   30 frames normally take 3–12 s; under 3 fps, check filters and DOM
set -e
ROOT=$(cd "$(dirname "$0")/.." && pwd); cd "$ROOT"
COMP=$1; A=$2; TAG=${3:-$COMP}; B=build_dev_$TAG
[ -n "$COMP" ] && [ -n "$A" ] || { echo "usage: test_render.sh <Comp> <start_frame> [tag]"; exit 1; }
[ -d "$B" ] || npx remotion bundle src/index.ts --out-dir "$B" --log=error
OUT=$(mktemp -d "${TMPDIR:-/tmp}/explainer_test_${TAG}_XXXXXX")   # No dots in the template: Remotion treats .XXXXXX as an image-sequence extension and refuses to render
trap 'rm -rf "$OUT"' EXIT
time npx remotion render "$B" "$COMP" "$OUT" --sequence --image-format=jpeg --frames=$((A-1))-$((A+28)) --log=error
ls "$OUT" | wc -l
