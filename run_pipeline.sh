#!/bin/bash
# run_pipeline.sh

# Force execution directory to match your project root
cd /opt/study-tracker

# Run the pipeline steps safely
python3 test_connection.py && \
python3 fetch_kurt.py && \
python3 generate_heatmap.py && \
python3 generate_monthly.py && \
python3 generate_stats.py && \
python3 build_dashboard.py
