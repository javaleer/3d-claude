#!/usr/bin/env bash
# One-time environment setup for Claude Code cloud sessions (and Linux boxes).
# Installs Blender as the `bpy` Python module into .venv, falling back to apt.
# Safe to re-run; it exits early when Blender is already usable.
set -uo pipefail
cd "$(dirname "$0")/.."

have_bpy() { [ -x .venv/bin/python ] && .venv/bin/python -c "import bpy" >/dev/null 2>&1; }

if have_bpy || command -v blender >/dev/null 2>&1; then
  echo "Blender already available."; exit 0
fi

# bpy needs a few X/GL libraries even in background mode.
if command -v apt-get >/dev/null 2>&1; then
  SUDO=""; [ "$(id -u)" -ne 0 ] && command -v sudo >/dev/null && SUDO="sudo"
  $SUDO apt-get update -qq || true
  $SUDO apt-get install -y -qq libxrender1 libxi6 libxkbcommon0 libxxf86vm1 libxfixes3 \
    libsm6 libgl1 libegl1 libglu1-mesa >/dev/null 2>&1 || true
fi

# bpy wheels are tied to one Python version (4.2-4.5 -> 3.11, 5.x -> 3.13).
# uv can fetch the right interpreter if the system one doesn't match.
try_venv() {  # $1 = python version, $2 = bpy spec
  echo "Trying bpy $2 on Python $1 ..."
  rm -rf .venv
  if command -v uv >/dev/null 2>&1; then
    uv venv -q --python "$1" .venv && uv pip install -q --python .venv/bin/python "bpy$2"
  elif command -v "python$1" >/dev/null 2>&1; then
    "python$1" -m venv .venv && .venv/bin/pip install -q "bpy$2"
  else
    return 1
  fi
}

if ! command -v uv >/dev/null 2>&1; then
  pip install -q uv 2>/dev/null || pip3 install -q uv 2>/dev/null || true
  export PATH="$HOME/.local/bin:$PATH"
fi

for combo in "3.11 ~=4.5.0" "3.11 ~=4.2.0" "3.13 " ; do
  set -- $combo
  if try_venv "$1" "${2:-}" && have_bpy; then
    echo "bpy ready: $(.venv/bin/python -c 'import bpy; print(bpy.app.version_string)')"
    exit 0
  fi
done

echo "pip bpy failed; falling back to apt blender"
rm -rf .venv
$SUDO apt-get install -y -qq blender && blender --version | head -1 && exit 0

echo "Could not install Blender." >&2
exit 1
