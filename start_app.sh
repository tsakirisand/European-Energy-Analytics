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

# 2. Launch Streamlit
streamlit run dashboard/app.py --server.port 8501 --server.address localhost
