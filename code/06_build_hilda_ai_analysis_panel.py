from pathlib import Path
import numpy as np
import pandas as pd


CLEAN_DIR = Path("data/clean")


def normalize_occ_code(value, width: int):
    """Normalize occupation codes to fixed-width strings for safe joins."""
    if pd.isna(value):
        return pd.NA
    s = str(value).strip().replace(".0", "")
    if s == "":
        return pd.NA
    if s.startswith("-"):
        return pd.NA
    # Keep only digit strings for code merges.
    if not s.isdigit():
        return pd.NA
    return s.zfill(width)


def build_aioe_2digit(aioe_path: Path) -> pd.DataFrame:
    aioe = pd.read_csv(aioe_path)
    aioe["anzsco_code"] = aioe["anzsco_code"].map(lambda x: normalize_occ_code(x, 6))
    aioe = aioe.dropna(subset=["anzsco_code", "aioe_mean"]).copy()

    aioe["anzsco2"] = aioe["anzsco_code"].str[:2]
    out = (
        aioe.groupby("anzsco2", as_index=False)
        .agg(
            aioe2_mean=("aioe_mean", "mean"),
            aioe2_sum=("aioe_sum", "sum"),
            n_anzsco6=("anzsco_code", "nunique"),
        )
        .sort_values("anzsco2")
    )
    return out


def main() -> None:
    hilda_path = CLEAN_DIR / "06_hilda_combined_minipanel.csv"
    aioe_path = CLEAN_DIR / "01_aioe_by_anzsco.csv"

    if not hilda_path.exists():
        raise FileNotFoundError(f"Missing input: {hilda_path}")
    if not aioe_path.exists():
        raise FileNotFoundError(f"Missing input: {aioe_path}")

    hilda = pd.read_csv(hilda_path)

    # Normalize key identifiers and occupation code for merge.
    hilda["xwaveid"] = hilda["xwaveid"].astype(str).str.strip()
    hilda["anzsco2"] = hilda["jbmo62"].map(lambda x: normalize_occ_code(x, 2))

    # Convert core numeric fields and treat HILDA negative codes as missing.
    for col in ["crpay", "hgage", "hgsex", "hhstate", "jbocct", "jbcmocc"]:
        if col in hilda.columns:
            hilda[col] = pd.to_numeric(hilda[col], errors="coerce")
            hilda.loc[hilda[col] < 0, col] = pd.NA

    hilda["year"] = pd.to_numeric(hilda["year"], errors="coerce")

    # Keep valid pay rows for main outcome construction.
    hilda = hilda.loc[hilda["crpay"].notna() & (hilda["crpay"] > 0)].copy()

    # Build 1-year log wage growth where observations are consecutive years.
    hilda = hilda.sort_values(["xwaveid", "year"])
    hilda["ln_crpay"] = hilda["crpay"].map(lambda x: pd.NA if pd.isna(x) or x <= 0 else float(np.log(x)))
    hilda["lag_year"] = hilda.groupby("xwaveid")["year"].shift(1)
    hilda["lag_ln_crpay"] = hilda.groupby("xwaveid")["ln_crpay"].shift(1)

    hilda["is_consecutive_year"] = (hilda["year"] - hilda["lag_year"] == 1).astype(int)
    hilda["wage_growth_log_1y"] = hilda["ln_crpay"] - hilda["lag_ln_crpay"]
    hilda.loc[hilda["is_consecutive_year"] != 1, "wage_growth_log_1y"] = pd.NA

    aioe2 = build_aioe_2digit(aioe_path)
    merged = hilda.merge(aioe2, on="anzsco2", how="left")

    # Keep a compact analysis column set.
    keep_cols = [
        "xwaveid",
        "wave",
        "year",
        "anzsco2",
        "aioe2_mean",
        "crpay",
        "ln_crpay",
        "wage_growth_log_1y",
        "hgsex",
        "hgage",
        "hhstate",
        "jbocct",
        "jbcmocc",
    ]
    keep_cols = [c for c in keep_cols if c in merged.columns]
    merged = merged[keep_cols]

    out_panel = CLEAN_DIR / "08_hilda_ai_analysis_panel.csv"
    out_qa = CLEAN_DIR / "09_hilda_ai_analysis_qa.csv"

    merged.to_csv(out_panel, index=False)

    qa = pd.DataFrame(
        [
            {"metric": "rows", "value": len(merged)},
            {"metric": "unique_people", "value": merged["xwaveid"].nunique()},
            {"metric": "year_min", "value": merged["year"].min()},
            {"metric": "year_max", "value": merged["year"].max()},
            {"metric": "rows_with_aioe", "value": int(merged["aioe2_mean"].notna().sum())},
            {
                "metric": "rows_with_wage_growth",
                "value": int(merged["wage_growth_log_1y"].notna().sum()),
            },
        ]
    )
    qa.to_csv(out_qa, index=False)

    print(f"Saved: {out_panel}")
    print(f"Saved: {out_qa}")
    print("QA summary:")
    print(qa.to_string(index=False))


if __name__ == "__main__":
    main()
