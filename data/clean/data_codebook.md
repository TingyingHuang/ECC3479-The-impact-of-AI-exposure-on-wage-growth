# Data Codebook (Clean Outputs)

This file documents the meaning and intended use of the cleaned datasets in `data/clean/`.

## 1) aioe_by_anzsco.csv

Purpose:
- Main occupation-level exposure table used to attach AI exposure to Australian occupation groups.

Unit:
- One row per `anzsco_code`.

Variables:
- `anzsco_code`: Australian occupation code (ANZSCO).
- `anzsco_title`: Occupation title.
- `aioe_mean`: Mean path-level AI exposure for this ANZSCO code.
- `aioe_sum`: Sum of path-level AI exposure contributions.
- `n_paths`: Number of mapping paths contributing to this ANZSCO code.

## 2) aioe_mapping_paths.csv

Purpose:
- Full mapping audit trail from SOC to ISCO to ANZSCO.

Unit:
- One row per SOC-ISCO-ANZSCO path.

Variables:
- `soc_code`, `soc_title`: Source SOC occupation.
- `aioe`: Original AIOE score at SOC level.
- `isco_code`, `isco_title`: Intermediate ISCO occupation.
- `n_isco`: Number of ISCO matches for the SOC code.
- `aioe_soc_split`: AIOE after SOC-level equal split.
- `anzsco_code`, `anzsco_title`: Final ANZSCO occupation.
- `n_anzsco`: Number of ANZSCO matches for the ISCO code.
- `aioe_path`: Final path-level exposure contribution.

## 3) soc_to_isco_mapping.csv

Purpose:
- Cleaned SOC to ISCO crosswalk used by the mapping pipeline.

Variables:
- `soc_code`: SOC 2010 code.
- `isco_code`: ISCO-08 code.
- `isco_title`: ISCO occupation title.

## 4) isco_to_anzsco_mapping.csv

Purpose:
- Cleaned ISCO to ANZSCO crosswalk used by the mapping pipeline.

Variables:
- `isco_code`: ISCO-08 code.
- `anzsco_code`: ANZSCO code.
- `anzsco_title`: ANZSCO occupation title.

## 5) cleaning_qa_summary.csv

Purpose:
- Quality checks and mapping coverage diagnostics.

Unit:
- One row per QA metric.

Variables:
- `metric`: Metric name.
- `value`: Metric value.

## 6) hilda_combined_minipanel.csv (restricted, local only)

Purpose:
- Analysis-ready person-wave mini panel from HILDA Combined files.

Unit:
- One row per person (`xwaveid`) per survey wave/year.

Key variables:
- `xwaveid`: Person identifier.
- `wave`: Survey wave letter.
- `year`: Calendar year derived from wave.
- `jbmo62`: 2-digit ANZSCO 2006 for current main job.
- `jbmo61`: 1-digit ANZSCO 2006 for current main job.
- `crpay`, `jbmspay`, `jbmpays`, `hehearn`: Pay/earnings measures (different survey definitions).
- `hgsex`: Sex.
- `hgage`: Age.
- `hhstate`: State.
- `jbocct`: Tenure in current occupation (years).
- `jbcmocc`: Occupation change indicator variable from survey item.

Important note:
- HILDA negative/special codes (for example, -1, -10) should be treated as invalid/missing in analysis.

## 7) hilda_combined_variable_coverage.csv (restricted, local only)

Purpose:
- Tracks extracted-variable availability across waves/files.

Variables:
- `file_name`, `wave`, `year`, `n_rows`, `n_selected_vars`
- `has_*` indicators for each extracted variable.

## 8) hilda_file_index.csv / hilda_file_profile.csv / hilda_variable_index.csv / hilda_variable_candidates.csv

Purpose:
- Data engineering diagnostics used to index HILDA files and identify stable variables.

Typical use:
- Validate wave coverage.
- Check which variables are available consistently.
- Support reproducible variable selection decisions.
