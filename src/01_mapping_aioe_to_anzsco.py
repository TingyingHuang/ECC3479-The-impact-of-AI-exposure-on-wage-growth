"""
Mapping US AI occupational exposure (AIOE) to Australian occupations (ANZSCO).

Process:
1. Load AIOE data with US SOC codes and AI exposure metrics
2. Map SOC 2010 -> ISCO-08 using crosswalk (handle many-to-many via equal weight)
3. Map ISCO-08 -> ANZSCO 2022 using crosswalk (handle many-to-many via equal weight)
4. Export clean mappings and diagnostics to data/clean/

For many-to-many relationships, we use equal-weight splitting:
- If SOC A maps to ISCO codes [1, 2, 3], the exposure is divided equally
- Same for ISCO -> ANZSCO
"""

from pathlib import Path

import pandas as pd


def load_raw_data():
    """Load all raw crosswalk and AIOE files."""
    raw = Path("data/raw")

    # AIOE: Language Model AI Occupational Exposure (US SOC 2010)
    aioe = pd.read_excel(raw / "aioe_raw.xlsx", sheet_name="LM AIOE")
    aioe.columns = ["soc_code", "occupation_title", "aioe", "soc_code_clean"]
    aioe["soc_code_clean"] = aioe["soc_code"].astype(str).str.strip()

    # SOC 2010 -> ISCO-08
    soc_isco = pd.read_excel(
        raw / "soc10_to_isco crosswalk.xls",
        sheet_name="2010 SOC to ISCO-08",
        header=6,
    )
    soc_isco = soc_isco[["2010 SOC Code", "ISCO-08 Code"]].dropna()
    soc_isco.columns = ["soc_code", "isco_code"]
    soc_isco["soc_code"] = soc_isco["soc_code"].astype(str).str.strip()
    soc_isco["isco_code"] = (
        soc_isco["isco_code"]
        .astype(str)
        .str.replace(".0", "", regex=False)
        .str.strip()
    )

    # ISCO-08 -> ANZSCO 2022 (Table 3 is the key mapping)
    isco_anz = pd.read_excel(
        raw / "isco_to_anzsco.xlsx.xlsx",
        sheet_name="Table 3",
        header=5,
    )
    isco_anz = isco_anz.iloc[:, [0, 2]].copy()
    isco_anz.columns = ["isco_code", "anzsco_code"]
    # Forward-fill ISCO codes for merged cells
    isco_anz["isco_code"] = isco_anz["isco_code"].ffill()
    isco_anz = isco_anz.dropna(subset=["isco_code", "anzsco_code"])
    isco_anz["isco_code"] = (
        isco_anz["isco_code"]
        .astype(str)
        .str.replace(".0", "", regex=False)
        .str.strip()
    )
    isco_anz["anzsco_code"] = (
        isco_anz["anzsco_code"]
        .astype(str)
        .str.replace(".0", "", regex=False)
        .str.strip()
    )

    return aioe, soc_isco, isco_anz


def apply_equal_weight_mapping(exposure_df, map_df, from_col, to_col, value_col):
    """
    Apply many-to-many equal weight expansion.

    For each source code with multiple targets, divide the exposure value equally.

    Args:
        exposure_df: DataFrame with source code and value to be mapped
        map_df: Crosswalk DataFrame with from_col -> to_col
        from_col: column name in map_df for source code
        to_col: column name in map_df for target code
        value_col: column name in exposure_df containing the value to split

    Returns:
        Expanded DataFrame with target code and weighted values
    """
    # Remove duplicates from mapping to count unique targets per source
    unique_map = map_df[[from_col, to_col]].drop_duplicates()

    # Count how many targets each source code has
    target_counts = (
        unique_map.groupby(from_col)[to_col].nunique().rename("n_targets")
    )

    # Merge with exposure data, then with unique targets
    result = exposure_df.merge(
        unique_map,
        left_on=exposure_df.columns[0],
        right_on=from_col,
        how="left",
    )

    # Add target count
    result = result.merge(
        target_counts.to_frame(),
        left_on=from_col,
        right_index=True,
        how="left",
    )

    # For unmatched rows, set n_targets to NaN so they don't contribute
    # For matched rows, divide the value equally
    result[value_col + "_weighted"] = result[value_col] / result["n_targets"]

    return result


def main():
    """Execute the mapping pipeline."""
    print("=" * 70)
    print("MAPPING AIOE TO ANZSCO")
    print("=" * 70)

    # Output directories
    clean_dir = Path("data/clean")
    clean_dir.mkdir(parents=True, exist_ok=True)

    # Load data
    print("\n[1/5] Loading raw data...")
    aioe, soc_isco, isco_anz = load_raw_data()
    print(f"  AIOE: {len(aioe)} occupations, {aioe['soc_code_clean'].nunique()} unique SOC")
    print(
        f"  SOC->ISCO: {len(soc_isco)} rows, {soc_isco['soc_code'].nunique()} unique SOC"
    )
    print(
        f"  ISCO->ANZSCO: {len(isco_anz)} rows, {isco_anz['isco_code'].nunique()} unique ISCO"
    )

    # Stage 1: Map SOC -> ISCO with equal weight
    print("\n[2/5] Mapping SOC 2010 -> ISCO-08 (equal-weight expand)...")
    soc_isco_clean = soc_isco.drop_duplicates().copy()
    
    # Count how many ISCO targets each SOC code has
    isco_target_count = (
        soc_isco_clean.groupby("soc_code")["isco_code"]
        .nunique()
        .rename("isco_count")
    )
    
    # Build SOC -> ISCO mapping with weights
    aioe_isco = aioe[["soc_code_clean", "aioe"]].copy()
    aioe_isco.columns = ["soc_code", "aioe"]
    
    # Many SOC codes may have duplicates due to multiple ISCO targets
    # For each SOC, we'll keep all ISCO mappings and weight the exposure
    aioe_isco = aioe_isco.merge(
        soc_isco_clean, on="soc_code", how="left"
    )
    aioe_isco = aioe_isco.merge(
        isco_target_count.to_frame().reset_index(),
        left_on="soc_code",
        right_on="soc_code",
        how="left",
    )
    # Equal weight: divide AIOE by number of ISCO targets
    aioe_isco.loc[aioe_isco["isco_code"].notna(), "aioe_weighted"] = (
        aioe_isco.loc[aioe_isco["isco_code"].notna(), "aioe"] /
        aioe_isco.loc[aioe_isco["isco_code"].notna(), "isco_count"]
    )
    
    soc_isco_multimap = (soc_isco_clean.groupby("soc_code")["isco_code"].nunique()
                         .sort_values(ascending=False))
    print(
        f"  {(soc_isco_multimap > 1).sum()} SOC codes map to >1 ISCO (max: {soc_isco_multimap.max()})"
    )
    print(f"  Result: {len(aioe_isco[aioe_isco['isco_code'].notna()])} expanded rows (with ISCO match)")

    # Stage 2: Map ISCO -> ANZSCO with equal weight
    print("\n[3/5] Mapping ISCO-08 -> ANZSCO (equal-weight expand)...")
    isco_anz_clean = isco_anz.drop_duplicates().copy()
    
    anzsco_target_count = (
        isco_anz_clean.groupby("isco_code")["anzsco_code"]
        .nunique()
        .rename("anzsco_count")
    )
    
    aioe_anzsco = aioe_isco[['soc_code', 'isco_code', 'aioe', 'aioe_weighted']].dropna(subset=['isco_code']).copy()
    aioe_anzsco = aioe_anzsco.merge(
        isco_anz_clean, on="isco_code", how="left"
    )
    aioe_anzsco = aioe_anzsco.merge(
        anzsco_target_count.to_frame().reset_index(),
        left_on="isco_code",
        right_on="isco_code",
        how="left",
    )
    # Equal weight within ISCO->ANZSCO as well
    aioe_anzsco.loc[aioe_anzsco["anzsco_code"].notna(), "aioe_weighted"] = (
        aioe_anzsco.loc[aioe_anzsco["anzsco_code"].notna(), "aioe_weighted"] /
        aioe_anzsco.loc[aioe_anzsco["anzsco_code"].notna(), "anzsco_count"]
    )
    
    isco_anz_multimap = (isco_anz_clean.groupby("isco_code")["anzsco_code"].nunique()
                         .sort_values(ascending=False))
    print(
        f"  {(isco_anz_multimap > 1).sum()} ISCO codes map to >1 ANZSCO (max: {isco_anz_multimap.max()})"
    )
    print(f"  Result: {len(aioe_anzsco[aioe_anzsco['anzsco_code'].notna()])} rows (with ANZSCO match)")

    # Aggregate by ANZSCO
    print("\n[4/5] Aggregating by ANZSCO...")
    aioe_by_anzsco = (
        aioe_anzsco.groupby("anzsco_code")
        .agg({"aioe_weighted": "sum"})
        .reset_index()
        .rename(columns={"aioe_weighted": "aioe_exposure"})
    )
    print(f"  Final ANZSCO occupations with exposure: {len(aioe_by_anzsco)}")

    # Export clean tables
    print("\n[5/5] Exporting to data/clean/...")
    
    # 1. Clean SOC -> ISCO mapping
    soc_isco_out = (
        soc_isco_clean[["soc_code", "isco_code"]]
        .drop_duplicates()
        .sort_values("soc_code")
        .reset_index(drop=True)
    )
    soc_isco_path = clean_dir / "soc_to_isco_mapping.csv"
    soc_isco_out.to_csv(soc_isco_path, index=False)
    print(f"  ✓ {soc_isco_path.name} ({len(soc_isco_out)} rows)")

    # 2. Clean ISCO -> ANZSCO mapping
    isco_anz_out = (
        isco_anz_clean[["isco_code", "anzsco_code"]]
        .drop_duplicates()
        .sort_values("isco_code")
        .reset_index(drop=True)
    )
    isco_anz_path = clean_dir / "isco_to_anzsco_mapping.csv"
    isco_anz_out.to_csv(isco_anz_path, index=False)
    print(f"  ✓ {isco_anz_path.name} ({len(isco_anz_out)} rows)")

    # 3. AIOE with ANZSCO exposure
    aioe_out = aioe_by_anzsco.copy()
    aioe_path = clean_dir / "aioe_by_anzsco.csv"
    aioe_out.to_csv(aioe_path, index=False)
    print(f"  ✓ {aioe_path.name} ({len(aioe_out)} rows)")

    # Diagnostics report
    print("\n" + "=" * 70)
    print("DIAGNOSTICS")
    print("=" * 70)
    
    # Coverage checks
    aioe_soc_unique = aioe["soc_code_clean"].nunique()
    aioe_covered_isco = aioe_isco.dropna(subset=['isco_code'])['soc_code'].nunique()
    aioe_covered_anzsco = aioe_anzsco.dropna(subset=['anzsco_code'])['soc_code'].nunique()
    
    print(f"\nCoverage (SOC-level):")
    print(f"  AIOE unique SOC codes: {aioe_soc_unique}")
    print(f"  Covered by SOC->ISCO: {aioe_covered_isco} ({aioe_covered_isco/aioe_soc_unique:.1%})")
    print(f"  Covered to ANZSCO: {aioe_covered_anzsco} ({aioe_covered_anzsco/aioe_soc_unique:.1%})")
    
    uncovered = aioe[~aioe['soc_code_clean'].isin(aioe_anzsco['soc_code'].dropna().unique())]['soc_code_clean'].unique()
    if len(uncovered) > 0:
        print(f"\n  Uncovered SOC codes ({len(uncovered)}):")
        for code in sorted(uncovered)[:10]:
            print(f"    - {code}")
    
    print(f"\nMany-to-many complexity:")
    print(f"  SOC codes with >1 ISCO target (top 10):")
    for soc, cnt in soc_isco_multimap.head(10).items():
        print(f"    {soc}: {cnt} ISCO codes")
    
    print(f"\n  ISCO codes with >1 ANZSCO target (top 10):")
    for isco, cnt in isco_anz_multimap.head(10).items():
        print(f"    {isco}: {cnt} ANZSCO codes")
    
    print(f"\nExposure distribution (equal-weighted aggregates):")
    print(aioe_by_anzsco['aioe_exposure'].describe().to_string())
    
    print("\n" + "=" * 70)
    print("COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()
