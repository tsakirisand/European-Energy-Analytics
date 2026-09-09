#!/usr/bin/env bash
set -e

echo "=================================================="
echo "EUROPEAN ENERGY ANALYTICS — SYSTEM STARTUP"
echo "=================================================="

cd "$(dirname "$0")"

# 1. Initialize DB & Run Pipeline
python3 pipeline_runner.py

echo ""
echo "=================================================="
echo "LAUNCHING STREAMLIT DASHBOARD..."
echo "=================================================="

APP_PORT="${PORT:-8501}"
# 2. Launch Streamlit
streamlit run dashboard/app.py --server.port "${APP_PORT}" --server.address 0.0.0.0
