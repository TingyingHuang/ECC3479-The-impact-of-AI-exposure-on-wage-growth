# Project Progress Timeline

This file summarizes what was completed at each stage so reviewers can quickly understand project progress beyond commit titles.

## Stage 1: Repository and Data Access Setup

What was done:
- Initialized repository structure and Git tracking.
- Added confidentiality-safe `.gitignore` rules for HILDA raw and derived files.
- Documented HILDA access constraints and manual data placement requirements.

Why it matters:
- Ensures the project is shareable on GitHub while respecting HILDA privacy/licensing rules.

## Stage 2: Occupation Mapping Pipeline (AIOE -> ANZSCO)

Scripts:
- `code/01_profile_raw_data.py`
- `code/02_mapping_aioe_to_anzsco.py`

What was cleaned/transformed:
- Standardized SOC/ISCO/ANZSCO keys.
- Built equal-weight one-to-many mapping chain: SOC -> ISCO -> ANZSCO.
- Generated path-level mapping transparency output and QA metrics.

Main outputs:
- `data/clean/01_soc_to_isco_mapping.csv`
- `data/clean/02_isco_to_anzsco_mapping.csv`
- `data/clean/03_aioe_mapping_paths.csv`
- `data/clean/04_aioe_by_anzsco.csv`
- `data/clean/05_cleaning_qa_summary.csv`

Progress evidence:
- High mapping coverage retained (SOC to ANZSCO coverage reported in QA file).

## Stage 3: HILDA File Inventory and Variable Discovery

Scripts:
- `code/03_index_hilda_files.py`
- `code/04_profile_hilda_variables.py`

What was cleaned/transformed:
- Indexed all HILDA files by dataset and wave.
- Profiled variable presence across files/waves.
- Built a shortlist of high-coverage candidate variables for extraction.

Main outputs:
- `data/clean/06_hilda_file_index.csv`
- `data/clean/07_hilda_file_profile.csv`
- `data/clean/08_hilda_variable_index.csv`
- `data/clean/09_hilda_variable_candidates.csv`

Why it matters:
- Converts a very large restricted dataset into a manageable, transparent extraction plan.

## Stage 4: HILDA Mini-Panel Construction

Script:
- `code/05_build_hilda_minipanel.py`

What was cleaned/transformed:
- Extracted person-wave panel fields for analysis use.
- Corrected occupation variable usage to ANZSCO fields (`jbmo62`, `jbmo61`).
- Included controls needed for modeling (`hgsex`, `hgage`, `hhstate`).
- Kept interpretation flags (`jbocct`, `jbcmocc`) explicit.

Main outputs:
- `data/clean/10_hilda_combined_minipanel.csv` (restricted/local)
- `data/clean/11_hilda_combined_variable_coverage.csv` (restricted/local)

Why it matters:
- Produces analysis-ready panel structure for wage outcome modeling.

## Stage 5: Reproducibility and Reviewer Readability Improvements

What was done:
- Consolidated executable scripts in `code/` and ordered by execution sequence (`01` to `05`).
- Ordered raw and clean files by usage/generation sequence.
- Added dependency file: `requirements.txt`.
- Expanded `README.md` with end-to-end run instructions, manual steps, and expected outputs.
- Added ordered data codebook: `data/clean/00_data_codebook.md`.

Why it matters:
- Reviewers can reproduce outputs directly from README and understand progress at each stage.

## Stage 6: Build Final Analysis-Ready Datasets (12/13)

Script:
- `code/06_build_hilda_ai_analysis_panel.py`

What was cleaned/transformed:
- Merged wages, controls, and occupation-level AI exposure into one modeling table.
- Constructed core outcome variable `wage_growth_log_1y` from consecutive-year log pay changes.
- Aggregated AIOE from ANZSCO 6-digit to ANZSCO 2-digit to match HILDA occupation coding.

Main outputs:
- `data/clean/12_hilda_ai_analysis_panel.csv` (restricted/local)
- `data/clean/13_hilda_ai_analysis_qa.csv` (restricted/local)

What these outputs do:
- `12_hilda_ai_analysis_panel.csv` is an analysis-ready input dataset that can be used directly for regression.
- `13_hilda_ai_analysis_qa.csv` is a QA/audit table reporting sample size and coverage (rows, people, years, exposure match, wage-growth availability).
- These files document data readiness; they are not empirical result tables and do not by themselves provide causal conclusions.

Why it matters:
- Clearly separates data preparation completion from the next modeling stage.
- Makes the transition to estimation transparent for reviewers.

## Current State

Completed:
- End-to-end data preparation pipeline through clean, ordered outputs (01-13).
- Documentation suitable for course submission and reproducibility checks.

Next analysis step:
- Run baseline and robustness regressions using the analysis-ready panel.
