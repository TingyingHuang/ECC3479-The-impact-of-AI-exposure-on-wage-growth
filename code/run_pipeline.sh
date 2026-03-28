#!/usr/bin/env bash
set -euo pipefail

# Run full data preparation pipeline from repository root.
python code/profile_raw_data.py
python code/mapping_aioe_to_anzsco.py
python code/index_hilda_files.py
python code/profile_hilda_variables.py
python code/build_hilda_minipanel.py

echo "Pipeline completed. Clean outputs are in data/clean/."
