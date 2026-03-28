"""
Mapping US AI Occupational Exposure (AIOE) to Australian ANZSCO codes

Pipeline:
  1. Load AIOE (US SOC 2010)
  2. Map SOC 2010 → ISCO 08 (with equal-weight for 1:N)
  3. Map ISCO 08 → ANZSCO (with equal-weight for 1:N)
  4. Export clean mapping tables and diagnostics

Strategy for one-to-many mappings:
  - Each SOC/ISCO that maps to N targets gets equal weight split
  - If SOC-X has AIOE=0.8 and maps to 2 ISCO codes → each ISCO gets 0.4

Author: Data Cleaning Pipeline
Date: 2026-03-28
"""

from pathlib import Path

import pandas as pd
import numpy as np


def normalize_code(code_str: str) -> str:
    """Standardize occupation codes: strip whitespace, remove .0"""
    if pd.isna(code_str):
        return None
    s = str(code_str).strip()
    s = s.replace(".0", "")
    return s


def main():
    # Paths
    raw = Path("data/raw")
    clean = Path("data/clean")
    clean.mkdir(parents=True, exist_ok=True)

    print("\n" + "=" * 70)
    print("STAGE 1: Load raw data")
    print("=" * 70)

    # Load AIOE (US SOC 2010)
    aioe = pd.read_excel(raw / "aioe_raw.xlsx", sheet_name="LM AIOE")
    aioe_cols = ["SOC Code", "Occupation Title", "Language Modeling AIOE"]
    aioe = aioe[aioe_cols].copy()
    aioe.columns = ["soc_code", "soc_title", "aioe"]
    aioe["soc_code"] = aioe["soc_code"].apply(normalize_code)
    print(f"\nAIOE loaded: {len(aioe)} rows, {aioe['soc_code'].nunique()} unique SOC codes")
    print(f"AIOE range: [{aioe['aioe'].min():.4f}, {aioe['aioe'].max():.4f}]")

    # Load SOC → ISCO crosswalk
    soc_isco_raw = pd.read_excel(
        raw / "soc10_to_isco crosswalk.xls",
        sheet_name="2010 SOC to ISCO-08",
        header=6,
    )
    soc_isco = soc_isco_raw[["2010 SOC Code", "2010 SOC Title", "ISCO-08 Code", "ISCO-08 Title EN"]].copy()
    soc_isco.columns = ["soc_code", "soc_title", "isco_code", "isco_title"]
    soc_isco = soc_isco.dropna(subset=["soc_code", "isco_code"])
    soc_isco["soc_code"] = soc_isco["soc_code"].apply(normalize_code)
    soc_isco["isco_code"] = soc_isco["isco_code"].apply(normalize_code)
    print(f"\nSOC→ISCO loaded: {len(soc_isco)} rows")
    print(f"  unique SOC: {soc_isco['soc_code'].nunique()}")
    print(f"  unique ISCO: {soc_isco['isco_code'].nunique()}")

    # Load ISCO → ANZSCO crosswalk (Table 3 is what we need)
    isco_anz_raw = pd.read_excel(
        raw / "isco_to_anzsco.xlsx.xlsx",
        sheet_name="Table 3",
        header=5,
    )
    isco_anz = isco_anz_raw.iloc[:, [0, 1, 2, 3, 4]].copy()
    isco_anz.columns = ["isco_code", "isco_title", "anzsco_code", "anzsco_title", "mapping_note"]
    # Fill down ISCO codes where Excel has blank cells (merged cell artifact)
    isco_anz["isco_code"] = isco_anz["isco_code"].ffill()
    isco_anz = isco_anz.dropna(subset=["isco_code", "anzsco_code"])
    isco_anz["isco_code"] = isco_anz["isco_code"].apply(normalize_code)
    isco_anz["anzsco_code"] = isco_anz["anzsco_code"].apply(normalize_code)
    print(f"\nISCO→ANZSCO loaded: {len(isco_anz)} rows")
    print(f"  unique ISCO: {isco_anz['isco_code'].nunique()}")
    print(f"  unique ANZSCO: {isco_anz['anzsco_code'].nunique()}")

    # ===== STAGE 2: Equal-weight aggregation =====
    print("\n" + "=" * 70)
    print("STAGE 2: Equal-weight one-to-many aggregation")
    print("=" * 70)

    # Merge AIOE with SOC→ISCO, then apply equal-weight split
    aioe_isco = aioe.merge(
        soc_isco[["soc_code", "isco_code", "isco_title"]],
        on="soc_code",
        how="left",
    )
    print(f"\nAIOE after SOC→ISCO merge: {aioe_isco.shape[0]} rows before aggregation")

    # Count how many ISCO each SOC maps to (for equal-weight)
    isco_count_per_soc = (
        soc_isco[["soc_code", "isco_code"]]
        .drop_duplicates()
        .groupby("soc_code")
        .size()
        .rename("isco_count")
    )
    aioe_isco = aioe_isco.merge(isco_count_per_soc, on="soc_code", how="left")
    aioe_isco["aioe_weighted"] = aioe_isco["aioe"] / aioe_isco["isco_count"]

    print(f"  SOC→ISCO one-to-many: {(isco_count_per_soc > 1).sum()} SOC codes map to multiple ISCO")
    print(f"  Max multiplicity: {isco_count_per_soc.max()}")

    # Now merge with ISCO→ANZSCO
    aioe_isco_anz = aioe_isco.merge(
        isco_anz[["isco_code", "anzsco_code", "anzsco_title"]],
        on="isco_code",
        how="left",
    )
    print(f"AIOE after ISCO→ANZSCO merge: {aioe_isco_anz.shape[0]} rows before final aggregation")

    # Count how many ANZSCO each ISCO maps to
    anz_count_per_isco = (
        isco_anz[["isco_code", "anzsco_code"]]
        .drop_duplicates()
        .groupby("isco_code")
        .size()
        .rename("anzsco_count")
    )
    aioe_isco_anz = aioe_isco_anz.merge(anz_count_per_isco, on="isco_code", how="left")
    aioe_isco_anz["aioe_final"] = aioe_isco_anz["aioe_weighted"] / aioe_isco_anz["anzsco_count"]

    print(f"  ISCO→ANZSCO one-to-many: {(anz_count_per_isco > 1).sum()} ISCO codes map to multiple ANZSCO")
    print(f"  Max multiplicity: {anz_count_per_isco.max()}")

    # ===== STAGE 3: Aggregate to ANZSCO level =====
    print("\n" + "=" * 70)
    print("STAGE 3: Aggregate to ANZSCO level")
    print("=" * 70)

    aioe_by_anzsco = (
        aioe_isco_anz.groupby(["anzsco_code", "anzsco_title"])
        .agg(
            aioe_mean=("aioe_final", "mean"),
            aioe_sum=("aioe_final", "sum"),
            n_paths=("aioe_final", "size"),
        )
        .reset_index()
    )
    aioe_by_anzsco = aioe_by_anzsco.sort_values("aioe_sum", ascending=False)

    print(f"\nFinal ANZSCO dataset: {len(aioe_by_anzsco)} unique ANZSCO codes")
    print(f"  AIOE (mean): [{aioe_by_anzsco['aioe_mean'].min():.4f}, {aioe_by_anzsco['aioe_mean'].max():.4f}]")
    print(f"  AIOE (sum): [{aioe_by_anzsco['aioe_sum'].min():.4f}, {aioe_by_anzsco['aioe_sum'].max():.4f}]")
    print(f"  Paths per ANZSCO (median): {aioe_by_anzsco['n_paths'].median():.1f}")

    # ===== STAGE 4: QA and export =====
    print("\n" + "=" * 70)
    print("STAGE 4: Quality assurance and export")
    print("=" * 70)

    # Check for missing values
    print(f"\nMissing values in final dataset:")
    for col in aioe_by_anzsco.columns:
        n_missing = aioe_by_anzsco[col].isna().sum()
        if n_missing > 0:
            print(f"  {col}: {n_missing}")

    # Check for duplicates
    n_dup = aioe_by_anzsco.duplicated(subset=["anzsco_code"]).sum()
    print(f"Duplicates in ANZSCO: {n_dup}")

    # Compute coverage metrics
    aioe_n_unique = aioe["soc_code"].nunique()
    aioe_with_anzsco = aioe_isco_anz[["soc_code"]].drop_duplicates()
    coverage_soc = len(aioe_with_anzsco) / aioe_n_unique
    print(f"\nCoverage metrics:")
    print(f"  AIOE SOC codes: {aioe_n_unique}")
    print(f"  SOC codes successfully mapped to ANZSCO: {len(aioe_with_anzsco)}")
    print(f"  Coverage: {coverage_soc:.2%}")

    # Export outputs
    print(f"\nExporting to {clean}/...")

    # 1. Full crosswalk history (for transparency)
    aioe_isco.to_csv(clean / "aioe_soc_to_isco_weighted.csv", index=False)
    print(f"  ✓ aioe_soc_to_isco_weighted.csv")

    # 2. Final ANZSCO-level dataset
    aioe_by_anzsco.to_csv(clean / "aioe_by_anzsco_final.csv", index=False)
    print(f"  ✓ aioe_by_anzsco_final.csv")

    # 3. Raw mapping tables for reference
    soc_isco[["soc_code", "isco_code", "isco_title"]].drop_duplicates().to_csv(
        clean / "soc_to_isco_mapping.csv", index=False
    )
    print(f"  ✓ soc_to_isco_mapping.csv")

    isco_anz[["isco_code", "anzsco_code", "anzsco_title"]].drop_duplicates().to_csv(
        clean / "isco_to_anzsco_mapping.csv", index=False
    )
    print(f"  ✓ isco_to_anzsco_mapping.csv")

    # 4. Diagnostic report
    with open(clean / "mapping_diagnostics.txt", "w") as f:
        f.write("=" * 80 + "\n")
        f.write("AIOE → ANZSCO MAPPING DIAGNOSTICS\n")
        f.write("=" * 80 + "\n\n")

        f.write("STAGE 1: Raw Data\n")
        f.write("-" * 80 + "\n")
        f.write(f"AIOE records: {len(aioe)}\n")
        f.write(f"  Unique SOC codes: {aioe['soc_code'].nunique()}\n")
        f.write(f"  AIOE range: [{aioe['aioe'].min():.6f}, {aioe['aioe'].max():.6f}]\n")
        f.write(f"  Missing AIOE: {aioe['aioe'].isna().sum()}\n\n")

        f.write(f"SOC↔ISCO crosswalk: {len(soc_isco)} rows\n")
        f.write(f"  Unique SOC: {soc_isco['soc_code'].nunique()}\n")
        f.write(f"  Unique ISCO: {soc_isco['isco_code'].nunique()}\n")
        f.write(f"  SOC codes with 1:N ISCO: {(isco_count_per_soc > 1).sum()}\n")
        f.write(f"  Max SOC→ISCO multiplicity: {isco_count_per_soc.max()}\n\n")

        f.write(f"ISCO↔ANZSCO crosswalk: {len(isco_anz)} rows\n")
        f.write(f"  Unique ISCO: {isco_anz['isco_code'].nunique()}\n")
        f.write(f"  Unique ANZSCO: {isco_anz['anzsco_code'].nunique()}\n")
        f.write(f"  ISCO codes with 1:N ANZSCO: {(anz_count_per_isco > 1).sum()}\n")
        f.write(f"  Max ISCO→ANZSCO multiplicity: {anz_count_per_isco.max()}\n\n")

        f.write("STAGE 2: After Equal-Weight Mapping\n")
        f.write("-" * 80 + "\n")
        f.write(f"AIOE records after full chain: {len(aioe_isco_anz)}\n")
        f.write(f"  (expansion due to 1:N mappings)\n\n")

        f.write("STAGE 3: ANZSCO Aggregation\n")
        f.write("-" * 80 + "\n")
        f.write(f"Final unique ANZSCO: {len(aioe_by_anzsco)}\n")
        f.write(f"  AIOE (mean) range: [{aioe_by_anzsco['aioe_mean'].min():.6f}, {aioe_by_anzsco['aioe_mean'].max():.6f}]\n")
        f.write(f"  AIOE (sum) range: [{aioe_by_anzsco['aioe_sum'].min():.6f}, {aioe_by_anzsco['aioe_sum'].max():.6f}]\n")
        f.write(f"  Paths per ANZSCO (median): {aioe_by_anzsco['n_paths'].median():.1f}\n")
        f.write(f"  Paths per ANZSCO (max): {aioe_by_anzsco['n_paths'].max()}\n\n")

        f.write("COVERAGE ANALYSIS\n")
        f.write("-" * 80 + "\n")
        f.write(f"Original AIOE SOC codes: {aioe_n_unique}\n")
        f.write(f"SOC codes successfully mapped: {len(aioe_with_anzsco)}\n")
        f.write(f"Coverage: {coverage_soc:.2%}\n\n")

        f.write("TOP 10 OCCUPATIONS BY AI EXPOSURE (mean)\n")
        f.write("-" * 80 + "\n")
        for idx, row in aioe_by_anzsco.head(10).iterrows():
            f.write(f"{row['anzsco_code']} | {row['anzsco_title']:<50} | AIOE={row['aioe_mean']:.4f} (n={row['n_paths']})\n")

    print(f"  ✓ mapping_diagnostics.txt")

    print("\n" + "=" * 70)
    print("✓ Mapping complete!")
    print("=" * 70)


if __name__ == "__main__":
    main()
