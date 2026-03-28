# ecc3479-project

## Project Overview
Mapping US AI exposure indicators to Australian occupational classifications.

## Data Sources
- SOC 2010 to ISCO crosswalk
- ISCO to ANZSCO crosswalk  
- HILDA data (restricted - not included in repository)
- AIOE (AI occupational exposure) data

**Note:** Raw data files are excluded from this repository for confidentiality reasons. Users requiring access should contact the instructor for data distribution instructions.

## Repository Structure
```
.
├── data/
│   ├── raw/          (original data files - not tracked)
│   └── clean/        (processed data)
├── src/              (cleaning and analysis scripts)
├── docs/             (documentation and reports)
├── outputs/          (results and visualizations)
└── README.md
```

## Workflow
1. Data cleaning: standardize occupation codes and handle mappings
2. Linking: join US AI exposure to AU occupations
3. Analysis: assess exposure distribution across Australian workforce

## Status
🚧 In progress - data cleaning phase