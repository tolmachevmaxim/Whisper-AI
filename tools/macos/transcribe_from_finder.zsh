#!/bin/zsh
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
TRANSCRIBE_SCRIPT="$PROJECT_DIR/skill/scripts/transcribe.py"

if [[ -n "${WHISPER_PYTHON_BIN:-}" ]]; then
  PYTHON_BIN="$WHISPER_PYTHON_BIN"
elif [[ -x "$PROJECT_DIR/.venv/bin/python3" ]]; then
  PYTHON_BIN="$PROJECT_DIR/.venv/bin/python3"
elif [[ -x "$PROJECT_DIR/venv/bin/python3" ]]; then
  PYTHON_BIN="$PROJECT_DIR/venv/bin/python3"
else
  print -u2 "ERROR: Whisper AI Python environment not found."
  print -u2 "Expected one of:"
  print -u2 "  $PROJECT_DIR/.venv/bin/python3"
  print -u2 "  $PROJECT_DIR/venv/bin/python3"
  print -u2 ""
  print -u2 "Create a virtual environment and install the packages listed in README.md:"
  print -u2 "  python3 -m venv venv"
  print -u2 "  venv/bin/python3 -m pip install pydub watchdog tkinterdnd2 openai-whisper torch"
  exit 127
fi

if [[ ! -x "$PYTHON_BIN" ]]; then
  print -u2 "ERROR: Python is not executable: $PYTHON_BIN"
  exit 126
fi

if [[ ! -f "$TRANSCRIBE_SCRIPT" ]]; then
  print -u2 "ERROR: Transcribe script not found: $TRANSCRIBE_SCRIPT"
  exit 127
fi

export WHISPER_PROJECT_DIR="$PROJECT_DIR"
cd "$PROJECT_DIR"
exec "$PYTHON_BIN" "$TRANSCRIBE_SCRIPT" "$@"
