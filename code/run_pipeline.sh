#!/usr/bin/env bash
set -euo pipefail

# Run full data preparation pipeline from repository root.
python code/01_profile_raw_data.py
python code/02_mapping_aioe_to_anzsco.py
python code/03_index_hilda_files.py
python code/04_profile_hilda_variables.py
python code/05_build_hilda_minipanel.py
python code/06_build_hilda_ai_analysis_panel.py

echo "Pipeline completed. Clean outputs are in data/clean/."
