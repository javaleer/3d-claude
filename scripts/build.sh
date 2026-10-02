#!/usr/bin/env bash
# Build a model with whichever Blender is available:
#   1. the project venv with pip `bpy` (cloud sessions, created by scripts/setup.sh)
#   2. any python3 that can `import bpy`
#   3. a Blender executable ($BLENDER, `blender` on PATH, or the macOS app)
# Usage: bash scripts/build.sh <slug> [--check]
set -euo pipefail
cd "$(dirname "$0")/.."

for py in .venv/bin/python python3.11 python3; do
  if command -v "$py" >/dev/null 2>&1 && "$py" -c "import bpy" >/dev/null 2>&1; then
    exec "$py" scripts/build_model.py "$@"
  fi
done

for b in "${BLENDER:-}" blender /Applications/Blender.app/Contents/MacOS/Blender; do
  if [ -n "$b" ] && command -v "$b" >/dev/null 2>&1; then
    exec "$b" --background --factory-startup --python scripts/build_model.py -- "$@"
  fi
done

echo "No Blender found. Run: bash scripts/setup.sh" >&2
exit 1
