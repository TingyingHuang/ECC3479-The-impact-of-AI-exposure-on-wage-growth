# ECC3479 Project: AI Exposure and Wage Growth across All Occupations in Australia

This repository builds a reproducible pipeline to map US AI occupational exposure (AIOE) into Australian occupation codes and prepare HILDA panel data for econometric analysis.

## Research Question

How does occupational AI exposure affect wages across all occupations in Australia over the period 2020–2024, and how has that effect changed year by year?

## Empirical Strategy

This project estimates the causal effect of occupational AI exposure on individual wage growth using a **two-way fixed effects (TWFE) event-study model** with a continuous treatment intensity.

**Primary specification:**

```
log_wage_{it} = β_2021·(AI_i × 1{t=2021})
              + β_2022·(AI_i × 1{t=2022})
              + β_2023·(AI_i × 1{t=2023})
              + β_2024·(AI_i × 1{t=2024})
              + γ·X_{it} + μ_i + λ_t + ε_{it}
```

where `AI_i` is each individual's **2020 baseline occupation AI exposure score** (held fixed regardless of subsequent job changes), `μ_i` are individual fixed effects, and `λ_t` are year fixed effects. Standard errors are clustered at the individual level.

**Key design choices:**
- **Continuous treatment, not binary.** Uses the full AIOE score rather than a high/low split, preserving variation across the full occupation distribution.
- **Baseline-fixed AI exposure.** ~37.5% of individuals change occupation during 2020–2024. Fixing exposure to the 2020 value removes the endogeneity from workers selectively switching into higher-paying AI roles.
- **Individual FE.** Absorbs all time-invariant personal characteristics; identification comes from within-person wage changes differentiated by AI exposure level.
- **Base year 2020.** Coefficients β_t measure wage growth divergence relative to 2020.

**Main finding:** After fixing baseline AI exposure and controlling for individual FE, workers in high-AI-exposure occupations in 2020 experienced significantly *lower* wage growth in 2021–2024 (β ranging from −0.090 to −0.205), consistent with post-COVID mean reversion of an elevated pandemic-era tech wage premium. A robustness check using time-varying AI exposure (see `output/robustness_timevarying.ipynb`) finds a positive 2021 effect (+0.083), attributable to endogenous occupational switching into high-AI roles.

## 1. Repository Structure

```text
ecc3479-project/
├── code/                                              ← data pipeline scripts (01–06)
├── data/
│   ├── raw/                                           ← raw input data files
│   └── clean/                                         ← cleaned outputs used for analysis
├── output/
│   ├── primary_analysis.ipynb        ← PRIMARY ANALYSIS (run this first)
│   └── robustness_timevarying.ipynb  ← robustness check: time-varying AI exposure
├── requirements.txt                                   ← Python packages
└── README.md                                          ← this file
```

## 2. Software Information

- Python: 3.10+
- Main packages: pandas, openpyxl, xlrd, statsmodels

### Install from scratch

**macOS / Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

**Windows:**
```bash
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r requirements.txt
```

## 3. Raw Data Requirements (`data/raw/`)

### Public/Shareable raw files (expected in `data/raw/`)
- `01_aioe_raw.xlsx`
- `02_soc10_to_isco_crosswalk.xls`
- `03_isco_to_anzsco.xlsx.xlsx`
- `04_soc_2010_to_2018_crosswalk.xlsx` (optional robustness file)

### Restricted raw files (HILDA; not on GitHub)
HILDA is confidential and cannot be committed to this repository.

How to obtain HILDA:
1. Apply for access via DSS/Melbourne Institute licensing process.
2. Download approved `.dta` files.
3. Place files in the exact folder names above.

Source page (DataVerse):
- https://dataverse.ada.edu.au/dataset.xhtml?persistentId=doi%3A10.26193%2F6M1BMR

Download these 4 STATA 240c zip files (all required):
1. `2. STATA 240c (Zip file 1 of 4 - Combined Data Files a-k).zip`
2. `2. STATA 240c (Zip file 2 of 4 - Combined Data Files l-x).zip`
3. `2. STATA 240c (Zip file 3 of 4 - Rperson Data Files).zip`
4. `2. STATA 240c (Zip file 4 of 4 - Eperson and Other Data Files).zip`

In this project, these are extracted/renamed to:
- zip 1 -> `data/raw/hilda_raw_combined_ak/`
- zip 2 -> `data/raw/hilda_raw_combined_lx/`
- zip 3 -> `data/raw/hilda_raw_rperson/`
- zip 4 -> `data/raw/hilda_raw_eperson/`

## 4. How To Run The Project From Scratch

### Full pipeline: raw data → clean data → analysis → results

Run from repository root in this order:

**Step 0 — Activate environment:**

**macOS / Linux:**
```bash
source .venv/bin/activate
```

**Windows:**
```bash
.venv\Scripts\Activate.ps1
```

**Step 1 — Build clean data** (optional one-command pipeline):

```bash
bash code/run_pipeline.sh
```

Or step-by-step:

```bash
python code/01_profile_raw_data.py
python code/02_mapping_aioe_to_anzsco.py
python code/03_index_hilda_files.py
python code/04_profile_hilda_variables.py
python code/05_build_hilda_minipanel.py
python code/06_build_hilda_ai_analysis_panel.py
```

**Step 2 — Run primary analysis** (produces all results, tables, figures):

```bash
jupyter nbconvert --to notebook --execute output/primary_analysis.ipynb --output output/primary_analysis.ipynb
```

Or open `output/primary_analysis.ipynb` in Jupyter and run all cells.

The notebook reads these clean data files:
- `data/clean/08_wages_ai_analysis_panel.csv` — main 2020–2024 analysis panel (TWFE models + pooled OLS)
- `data/clean/06_hilda_person_wave_panel.csv` — full HILDA panel 2001–2024 (pre-trend check, §5)
- `data/clean/01_aioe_by_anzsco.csv` — occupation-level AI exposure (pre-trend check, §5)

All results (tables and figures) are rendered inline within the notebook.

**Step 3 — Optional robustness notebook:**

```bash
jupyter nbconvert --to notebook --execute output/robustness_timevarying.ipynb --inplace
```

This runs the time-varying AI exposure specification (reads `data/clean/08_wages_ai_analysis_panel.csv`) and explains why it diverges from the primary result.

**Expected outputs in `data/clean/` after Step 1:**
- `01_aioe_by_anzsco.csv`
- `02_hilda_file_inventory.csv`
- `03_hilda_file_schema.csv`
- `04_hilda_variable_frequency.csv`
- `05_hilda_variable_candidates.csv`
- `06_hilda_person_wave_panel.csv` (restricted/local)
- `07_hilda_variable_coverage_by_wave.csv` (restricted/local)
- `08_wages_ai_analysis_panel.csv` (restricted/local)
- `09_wages_ai_panel_qa.csv` (restricted/local)

### Occupation matching note (for empirical transparency)
- HILDA occupation in this project uses ANZSCO 2-digit code (`jbmo62`).
- AIOE is first mapped to ANZSCO 6-digit through SOC -> ISCO -> ANZSCO links, then aggregated to ANZSCO 2-digit for merge.
- In valid occupation observations (`jbmo62 > 0`), the merge coverage is about 99.6%.
- Unmatched observations are a small residual share (about 0.4%), mostly broad/special occupation groups.
- Main analysis keeps these as missing exposure; a robustness check can re-estimate after excluding unmatched occupations.

### Script run order and purpose
1. `code/01_profile_raw_data.py`
	- sanity-check raw mapping files before transformation
2. `code/02_mapping_aioe_to_anzsco.py`
	- build final SOC -> ISCO -> ANZSCO mapped occupation exposure table
3. `code/03_index_hilda_files.py`
	- index all HILDA files and wave coverage
4. `code/04_profile_hilda_variables.py`
	- profile variable availability across HILDA files
5. `code/05_build_hilda_minipanel.py`
	- extract person-wave mini panel for analysis variables
6. `code/06_build_hilda_ai_analysis_panel.py`
	- harmonise wages (`wscmg` annual gross wages, `wscmga` imputed fallback), build log wage, construct white/blue collar markers, merge 2-digit AIOE exposure, and pre-compute year dummies and `ai_exposure × yr_t` interaction terms for the time-varying coefficient model (2020–2024, all occupations)

Manual steps outside code (must do):
1. Obtain and place HILDA files in `data/raw/` (restricted data step).
2. Confirm file names/folders match this README before running scripts.
3. Keep restricted HILDA raw and derived files private (already gitignored).

## 5. Clean Data Outputs (`data/clean/`)

### Variable definitions are documented in:
- `data/clean/00_data_codebook.md`

### Core analysis tables
- `01_aioe_by_anzsco.csv`
  - Occupation-level AI exposure after mapping to ANZSCO
  - Main fields: `anzsco_code`, `aioe_mean`, `n_paths`
- `06_hilda_person_wave_panel.csv` (restricted; local only)
  - Person-wave panel extracted from HILDA Combined files
  - Main fields: `xwaveid`, `year`, `jbmo62`, `jbmspay`, `jbmpays`, `crpay`, `hgsex`, `hgage`, `hhstate`, `edhigh1`
- `08_wages_ai_analysis_panel.csv` (restricted; local only)
	- Final model-ready panel for the time-varying coefficient model
	- Main fields: `person_id`, `year`, `occ_code`, `occ_major_group`, `white_collar`, `blue_collar`, `ai_exposure`, `annual_wage`, `log_wage`, `sex`, `age`, `state`, `edu`, `yr_2021`-`yr_2024`, `ai_x_yr2021`-`ai_x_yr2024`
- `09_wages_ai_panel_qa.csv` (restricted; local only)
	- QA summary for final analysis sample size and coverage

### Mapping transparency and QA tables
- Mapping intermediates are generated in memory and collapsed to the final occupation exposure table `01_aioe_by_anzsco.csv`.

### HILDA structure/diagnostic tables (restricted; local only)
- `02_hilda_file_inventory.csv`: file inventory by dataset and wave
- `03_hilda_file_schema.csv`: number of columns by file
- `04_hilda_variable_frequency.csv`: variable presence frequency across files
- `05_hilda_variable_candidates.csv`: high-coverage candidate variables
- `07_hilda_variable_coverage_by_wave.csv`: extracted-variable availability by wave

