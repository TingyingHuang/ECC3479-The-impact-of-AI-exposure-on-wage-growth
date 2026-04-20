# Primary Econometric Analysis Summary

> Full version with detailed steps and figure explanations: [output/primary_econometric_analysis_full_notebook.ipynb](output/primary_econometric_analysis_full_notebook.ipynb)

This markdown file is a short summary to avoid duplication.

## Research question

- What is the effect of high AI occupational exposure on annual wage growth for white-collar professionals in Australia over 2020 to 2024, compared with low-AI occupations?

## Key results (concise)

- Sample: 30,526 person-year observations, 9,354 people (complete-case).
- Baseline model: `high_ai_x_post2021 = +0.0162` (`p=0.047`), positive but modest.
- Mobility main effect is positive; triple interaction (`high_ai_x_post2021_x_mobility`) is positive but not statistically significant (`p=0.171`).
- Specification check (Spec A vs Spec B): core interaction estimate remains stable.

## Figures

### Figure 1. Baseline key coefficients (95% CI)

- Included in the notebook output cell: [output/primary_econometric_analysis_full_notebook.ipynb](output/primary_econometric_analysis_full_notebook.ipynb)

### Figure 2. Specification comparison (Spec A vs Spec B, 95% CI)

- Included in the notebook output cell: [output/primary_econometric_analysis_full_notebook.ipynb](output/primary_econometric_analysis_full_notebook.ipynb)

## Output files

- output/primary_econometric_key_coefficients.csv
- output/primary_econometric_spec_check.csv
- output/primary_econometric_analysis_full_notebook.ipynb