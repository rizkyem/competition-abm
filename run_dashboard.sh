#!/bin/bash
# Launch the NetLogo-style browser dashboard.
cd "$(dirname "$0")" || exit 1
if [ ! -x ".venv/bin/streamlit" ]; then
  echo "Setting up virtual environment (first run only)..."
  python3 -m venv .venv
  .venv/bin/pip install -r requirements.txt
fi
echo "Starting dashboard at http://localhost:8501 ..."
exec .venv/bin/streamlit run app.py
