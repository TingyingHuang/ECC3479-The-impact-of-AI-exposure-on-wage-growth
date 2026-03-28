# ECC3479-The-impact-of-AI-exposure-on-wage-growth

Empirical analysis of AI occupational exposure on wage growth in Australia (2020-2024) using a Difference-in-Differences (DID) design. Built for ECC3479.

## Project Overview
This project maps US AI exposure indicators to Australian occupational classifications and evaluates links with wage growth outcomes.

## Data Sources
- SOC 2010 to ISCO crosswalk
- ISCO to ANZSCO crosswalk
- AIOE (AI occupational exposure) data
- HILDA data (restricted)

## Data Availability Statement (HILDA)
The raw data from the Household, Income and Labour Dynamics in Australia (HILDA) Survey is highly restricted due to privacy and confidentiality agreements. Therefore, it is not included in this public repository.

How to obtain the data: Researchers can apply for access through the Department of Social Services (DSS) and the Melbourne Institute. Once access is granted, place the provided files in the data/raw directory according to the project scripts.

## Repository Structure
- data/raw: original data files (restricted files are ignored)
- data/clean: processed datasets
- src: cleaning and analysis scripts
- docs: documentation and reports
- outputs: results and visualizations

## Workflow
1. Data cleaning: standardize occupation codes and handle mappings
2. Linking: join US AI exposure to AU occupations
3. Analysis: assess exposure distribution across Australian workforce

## Status
In progress - data cleaning phase
