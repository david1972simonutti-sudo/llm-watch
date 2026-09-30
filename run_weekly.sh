#!/bin/bash
# run_weekly.sh — lancé par launchd le lundi 8h (ou à la demande).
# Utilise directement le Python du venv : launchd a un PATH minimal.
PROJECT_DIR="$HOME/llm-watch"          # adapte si tu l'as mis ailleurs
cd "$PROJECT_DIR" || exit 1
mkdir -p logs

if [ -x "venv/bin/python" ]; then
  PY="venv/bin/python"
else
  PY="python3"
fi

"$PY" collect.py >> "logs/run_$(date +%Y-%m-%d).log" 2>&1
