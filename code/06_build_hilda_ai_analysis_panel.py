from pathlib import Path
import numpy as np
import pandas as pd


CLEAN_DIR = Path("data/clean")
PAY_CANDIDATES = ["wscmg", "wscmga"]
YEAR_MIN = 2020
YEAR_MAX = 2024
WHITE_COLLAR_MAJOR_GROUPS = {"1", "2", "3", "4"}


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


def build_harmonized_pay(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for col in PAY_CANDIDATES:
        if col in out.columns:
            out[col] = pd.to_numeric(out[col], errors="coerce")
            out.loc[out[col] < 0, col] = pd.NA
    out["pay"] = pd.NA
    for col in PAY_CANDIDATES:
        if col not in out.columns:
            continue
        fill_mask = out["pay"].isna() & out[col].notna() & (out[col] > 0)
        out.loc[fill_mask, "pay"] = out.loc[fill_mask, col]
    return out


def main() -> None:
    hilda_path = CLEAN_DIR / "06_hilda_person_wave_panel.csv"
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
    for col in ["hgage", "hgsex", "hhstate", "edhigh1"]:
        if col in hilda.columns:
            hilda[col] = pd.to_numeric(hilda[col], errors="coerce")
            hilda.loc[hilda[col] < 0, col] = pd.NA

    hilda["year"] = pd.to_numeric(hilda["year"], errors="coerce")

    hilda = build_harmonized_pay(hilda)

    # Keep valid pay rows.
    hilda = hilda.loc[hilda["pay"].notna() & (hilda["pay"] > 0)].copy()

    # Build log wage.
    hilda["ln_pay"] = hilda["pay"].map(lambda x: pd.NA if pd.isna(x) or x <= 0 else float(np.log(x)))

    # Build white-collar (ANZSCO 1-4) and blue-collar (ANZSCO 5-8) markers.
    hilda["anzsco_major"] = hilda["anzsco2"].astype("string").str.slice(0, 1)
    hilda["is_white_collar"] = hilda["anzsco_major"].isin(WHITE_COLLAR_MAJOR_GROUPS).astype(int)
    hilda["is_blue_collar"] = (
        hilda["anzsco_major"].notna() & ~hilda["anzsco_major"].isin(WHITE_COLLAR_MAJOR_GROUPS)
    ).astype(int)

    aioe2 = build_aioe_2digit(aioe_path)
    merged = hilda.merge(aioe2, on="anzsco2", how="left")

    # Restrict to policy window.
    merged = merged.loc[
        merged["year"].between(YEAR_MIN, YEAR_MAX, inclusive="both")
    ].copy()

    # Year dummies (base = YEAR_MIN) and AI exposure × year interactions.
    # Each ai_x_yr{t} = ai_exposure * I(year == t); NA where ai_exposure is missing.
    yr_cols = []
    for yr in range(YEAR_MIN + 1, YEAR_MAX + 1):
        d_col = f"yr_{yr}"
        ix_col = f"ai_x_yr{yr}"
        merged[d_col] = (merged["year"] == yr).astype(int)
        merged[ix_col] = pd.NA
        has_ai = merged["aioe2_mean"].notna()
        merged.loc[has_ai, ix_col] = merged.loc[has_ai, "aioe2_mean"] * merged.loc[has_ai, d_col]
        yr_cols.extend([d_col, ix_col])

    # Keep a compact analysis column set.
    keep_cols = (
        ["xwaveid", "year", "anzsco2", "anzsco_major", "is_white_collar", "is_blue_collar",
         "aioe2_mean", "pay", "ln_pay", "hgsex", "hgage", "hhstate", "edhigh1"]
        + yr_cols
    )
    keep_cols = [c for c in keep_cols if c in merged.columns]
    merged = merged[keep_cols]

    rename_map = {
        "xwaveid": "person_id",
        "anzsco2": "occ_code",
        "anzsco_major": "occ_major_group",
        "is_white_collar": "white_collar",
        "is_blue_collar": "blue_collar",
        "aioe2_mean": "ai_exposure",
        "pay": "annual_wage",
        "ln_pay": "log_wage",
        "hgsex": "sex",
        "hgage": "age",
        "hhstate": "state",
        "edhigh1": "edu",
    }
    merged = merged.rename(columns={k: v for k, v in rename_map.items() if k in merged.columns})

    out_panel = CLEAN_DIR / "08_wages_ai_analysis_panel.csv"
    out_qa = CLEAN_DIR / "09_wages_ai_panel_qa.csv"

    merged.to_csv(out_panel, index=False)

    actual_yrs = sorted(merged["year"].dropna().unique())
    qa = pd.DataFrame(
        [
            {"metric": "rows", "value": len(merged)},
            {"metric": "unique_people", "value": merged["person_id"].nunique()},
            {"metric": "year_min", "value": merged["year"].min()},
            {"metric": "year_max", "value": merged["year"].max()},
            {"metric": "rows_with_ai_exposure", "value": int(merged["ai_exposure"].notna().sum())},
            {"metric": "rows_missing_ai_exposure", "value": int(merged["ai_exposure"].isna().sum())},
            {"metric": "rows_white_collar", "value": int((merged["white_collar"] == 1).sum())},
            {"metric": "rows_blue_collar", "value": int((merged["blue_collar"] == 1).sum())},
            {"metric": "rows_with_edu", "value": int(merged["edu"].notna().sum()) if "edu" in merged.columns else 0},
            {
                "metric": "years_with_rows",
                "value": ",".join(str(int(y)) for y in actual_yrs),
            },
        ]
        + [
            {"metric": f"rows_yr_{int(yr)}", "value": int((merged["year"] == yr).sum())}
            for yr in actual_yrs
        ]
    )
    qa.to_csv(out_qa, index=False)

    print(f"Saved: {out_panel}")
    print(f"Saved: {out_qa}")
    print("QA summary:")
    print(qa.to_string(index=False))


if __name__ == "__main__":
    main()
