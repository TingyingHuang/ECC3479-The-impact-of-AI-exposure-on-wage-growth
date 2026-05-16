# ECC3479 Project: AI Exposure and Wage Growth across All Occupations in Australia

## Research Question

How is occupational AI exposure associated with wage growth across all occupations in Australia over the period 2020–2024, and how has that association changed year by year?

## Empirical Strategy

This project documents the conditional association between occupational AI exposure and individual wage growth using a **two-way fixed effects (TWFE) event-study model** with a continuous treatment variable.

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

## 1. Reading Order

Read the analysis notebooks in this order:

1. [`output/primary_analysis.ipynb`](output/primary_analysis.ipynb) — Main TWFE results:
   - §1 Setup and data loading
   - §2 Econometric specification (functional form, prep functions, model estimation, summary statistics)
   - §3 Regression table and event-study plot (Figure 1)
   - §4 Interpretation of main coefficients
   - §5 Limitations and Alternative Explanations
   - §6 Main findings summary

2. [`output/robustness_checks.ipynb`](output/robustness_checks.ipynb) — Comprehensive robustness suite (10 sections):
   - Opens with a TOC and **8.Summary Robustness Table** (all 9 specifications side by side) as a quick reference
   - §1 Pre-trend check (parallel trends, 2001–2019 cross-sectional slopes)
   - §2 Time-varying AI exposure (endogenous-switching test and sign-reversal explanation; Figure 2 comparison plot)
   - §3 Standard error choices (Classical / HC3 / Clustered)
   - §4 Alternative control sets (minimal / main / + state dummies)
   - §5 Alternative samples (trimmed wages / non-switchers / prime-age 25–55)
   - §6 Alternative functional form (log wage / IHS wage / levels)
   - §7 Placebo test and alternative base year
   - §9 Coefficient plot (forest plot of 2023 coefficient across all specs)
   - §10 Conclusions

---

## 2. Repository Structure

```text
ecc3479-project/
├── code/                                              ← data pipeline scripts (01–06)
├── data/
│   ├── raw/                                           ← raw input data files
│   └── clean/                                         ← cleaned outputs used for analysis
├── output/
│   ├── primary_analysis.ipynb         ← PRIMARY ANALYSIS — specification, regression table, event-study plot, threats (§1–§6)
│   └── robustness_checks.ipynb        ← Robustness suite: summary table at top (§8), pre-trend (§1), time-varying (§2), SE/controls/samples/form/placebo (§3–§7), forest plot (§9), conclusions (§10)
├── requirements.txt                                   ← Python packages
└── README.md                                          ← this file
```

## 3. Software Information

- Python: 3.10+
- Main packages: pandas, numpy, matplotlib, statsmodels, openpyxl, xlrd, jupyter, nbconvert

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

## 4. Raw Data Requirements (`data/raw/`)

### Public/Shareable raw files (expected in `data/raw/`)
- `01_aioe_raw.xlsx`
- `02_soc10_to_isco_crosswalk.xls`
- `03_isco_to_anzsco.xlsx.xlsx`
- `04_soc_2010_to_2018_crosswalk.xlsx` (optional robustness file)

### Restricted raw files (HILDA; not on GitHub)
HILDA is confidential and cannot be committed to this repository.

How to obtain HILDA:
1. Apply for access via the DSS/Melbourne Institute licensing process.
2. Download approved `.dta` files from DataVerse: https://dataverse.ada.edu.au/dataset.xhtml?persistentId=doi%3A10.26193%2F6M1BMR
3. Download these 4 STATA 240c zip files (all required) and extract to the folders below:

| Zip file | Extract to |
|----------|-----------|
| Zip file 1 of 4 — Combined Data Files a-k | `data/raw/hilda_raw_combined_ak/` |
| Zip file 2 of 4 — Combined Data Files l-x | `data/raw/hilda_raw_combined_lx/` |
| Zip file 3 of 4 — Rperson Data Files | `data/raw/hilda_raw_rperson/` |
| Zip file 4 of 4 — Eperson and Other Data Files | `data/raw/hilda_raw_eperson/` |

## 5. Clean Data Outputs (`data/clean/`)

Variable definitions: `data/clean/00_data_codebook.md`

| File | Description |
|------|-------------|
| `01_aioe_by_anzsco.csv` | Occupation-level AI exposure mapped to ANZSCO; fields: `anzsco_code`, `aioe_mean`, `n_paths` |
| `06_hilda_person_wave_panel.csv` | Person-wave panel from HILDA Combined files (restricted) |
| `08_wages_ai_analysis_panel.csv` | Final model-ready panel 2020–2024 (restricted); fields: `person_id`, `year`, `occ_code`, `ai_exposure`, `log_wage`, `edu`, `ai_x_yr2021`–`ai_x_yr2024` |
| `09_wages_ai_panel_qa.csv` | QA summary for sample size and coverage (restricted) |
| `02`–`05`, `07` | HILDA structure/diagnostic tables (restricted) |

## 6. How To Run The Project From Scratch

Run all commands from the repository root.

**Step 0 — Activate environment:**

macOS / Linux: `source .venv/bin/activate`  
Windows: `.venv\Scripts\Activate.ps1`

---

**Step 1 — Build clean data:**

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

---

**Step 2 — Primary analysis** (TWFE model, regression table, event-study plot, §1–§6):

```bash
jupyter nbconvert --to notebook --execute output/primary_analysis.ipynb --inplace
```

Reads: `data/clean/08_wages_ai_analysis_panel.csv`

---

**Step 3 — Robustness suite** (summary table, pre-trend, time-varying, SE/controls/samples/form/placebo, forest plot, §1–§10):

```bash
jupyter nbconvert --to notebook --execute output/robustness_checks.ipynb --inplace
```

Reads: `data/clean/08_wages_ai_analysis_panel.csv`, `data/clean/06_hilda_person_wave_panel.csv`, `data/clean/01_aioe_by_anzsco.csv`

---

### Script purposes

| Script | Purpose |
|--------|---------|
| `01_profile_raw_data.py` | Sanity-check raw mapping files |
| `02_mapping_aioe_to_anzsco.py` | Build SOC → ISCO → ANZSCO occupation exposure table |
| `03_index_hilda_files.py` | Index HILDA files and wave coverage |
| `04_profile_hilda_variables.py` | Profile variable availability across HILDA files |
| `05_build_hilda_minipanel.py` | Extract person-wave panel for analysis variables |
| `06_build_hilda_ai_analysis_panel.py` | Harmonise wages, build log wage, merge AI exposure, compute interaction terms |

**Manual steps (required before running):**
1. Obtain and place HILDA files in `data/raw/`.
2. Confirm file names/folders match this README.
3. Keep restricted HILDA files private (already gitignored).

### Occupation matching note

HILDA occupation uses ANZSCO 2-digit code (`jbmo62`). AIOE is first mapped to ANZSCO 6-digit through SOC → ISCO → ANZSCO crosswalks, then aggregated to 2-digit for merge. Coverage is approximately 99.6% in valid occupation observations; unmatched observations (~0.4%) are kept as missing exposure in the main analysis.
