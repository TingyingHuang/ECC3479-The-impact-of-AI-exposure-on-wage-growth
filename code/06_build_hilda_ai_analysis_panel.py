from pathlib import Path
import numpy as np
import pandas as pd


CLEAN_DIR = Path("data/clean")
PAY_CANDIDATES = ["jbmspay", "crpay", "jbmpays"]
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
    """Build a pay field with source fallback while preserving source provenance."""
    out = df.copy()

    for col in PAY_CANDIDATES:
        if col in out.columns:
            out[col] = pd.to_numeric(out[col], errors="coerce")
            out.loc[out[col] < 0, col] = pd.NA

    out["pay"] = pd.NA
    out["pay_source"] = pd.NA

    for col in PAY_CANDIDATES:
        if col not in out.columns:
            continue
        fill_mask = out["pay"].isna() & out[col].notna() & (out[col] > 0)
        out.loc[fill_mask, "pay"] = out.loc[fill_mask, col]
        out.loc[fill_mask, "pay_source"] = col

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
    for col in ["hgage", "hgsex", "hhstate", "jbocct", "jbcmocc"]:
        if col in hilda.columns:
            hilda[col] = pd.to_numeric(hilda[col], errors="coerce")
            hilda.loc[hilda[col] < 0, col] = pd.NA

    hilda["year"] = pd.to_numeric(hilda["year"], errors="coerce")

    hilda = build_harmonized_pay(hilda)

    # Keep valid pay rows for main outcome construction.
    hilda = hilda.loc[hilda["pay"].notna() & (hilda["pay"] > 0)].copy()

    # Build 1-year log wage growth where observations are consecutive years
    # and drawn from the same pay source to avoid definition shifts.
    hilda = hilda.sort_values(["xwaveid", "year"])
    hilda["ln_pay"] = hilda["pay"].map(lambda x: pd.NA if pd.isna(x) or x <= 0 else float(np.log(x)))
    hilda["lag_year"] = hilda.groupby("xwaveid")["year"].shift(1)
    hilda["lag_ln_pay"] = hilda.groupby("xwaveid")["ln_pay"].shift(1)
    hilda["lag_pay_source"] = hilda.groupby("xwaveid")["pay_source"].shift(1)

    hilda["is_consecutive_year"] = (hilda["year"] - hilda["lag_year"] == 1).astype(int)
    hilda["same_pay_source_as_lag"] = (hilda["pay_source"] == hilda["lag_pay_source"]).astype(int)
    hilda["wage_growth_log_1y"] = hilda["ln_pay"] - hilda["lag_ln_pay"]
    hilda.loc[
        (hilda["is_consecutive_year"] != 1) | (hilda["same_pay_source_as_lag"] != 1),
        "wage_growth_log_1y",
    ] = pd.NA

    # Build occupation-mobility indicators from occupation-code changes.
    hilda["lag_anzsco2"] = hilda.groupby("xwaveid")["anzsco2"].shift(1)
    hilda["occ_changed_anzsco2_1y"] = pd.NA
    valid_occ_change = (
        hilda["is_consecutive_year"].eq(1)
        & hilda["anzsco2"].notna()
        & hilda["lag_anzsco2"].notna()
    )
    hilda.loc[valid_occ_change, "occ_changed_anzsco2_1y"] = (
        hilda.loc[valid_occ_change, "anzsco2"] != hilda.loc[valid_occ_change, "lag_anzsco2"]
    ).astype(int)

    # Build a white-collar marker from ANZSCO major groups (1-4).
    hilda["anzsco_major"] = hilda["anzsco2"].astype("string").str.slice(0, 1)
    hilda["is_white_collar"] = hilda["anzsco_major"].isin(WHITE_COLLAR_MAJOR_GROUPS).astype(int)

    aioe2 = build_aioe_2digit(aioe_path)
    merged = hilda.merge(aioe2, on="anzsco2", how="left")

    # Restrict to policy window and white-collar analysis sample.
    merged = merged.loc[
        merged["year"].between(YEAR_MIN, YEAR_MAX, inclusive="both")
        & merged["is_white_collar"].eq(1)
    ].copy()

    # Policy/exposure indicators for the new research question.
    merged["post_2021"] = (merged["year"] >= 2021).astype(int)
    aioe_cutoff = merged["aioe2_mean"].median(skipna=True)
    merged["high_ai_exposure"] = pd.NA
    merged.loc[merged["aioe2_mean"].notna(), "high_ai_exposure"] = (
        merged.loc[merged["aioe2_mean"].notna(), "aioe2_mean"] >= aioe_cutoff
    ).astype(int)
    merged["high_ai_x_post2021"] = pd.NA
    valid_interaction = merged["high_ai_exposure"].notna()
    merged.loc[valid_interaction, "high_ai_x_post2021"] = (
        merged.loc[valid_interaction, "high_ai_exposure"].astype(int) * merged.loc[valid_interaction, "post_2021"]
    )

    merged["high_ai_x_post2021_x_mobility"] = pd.NA
    valid_triple = valid_interaction & merged["occ_changed_anzsco2_1y"].notna()
    merged.loc[valid_triple, "high_ai_x_post2021_x_mobility"] = (
        merged.loc[valid_triple, "high_ai_exposure"].astype(int)
        * merged.loc[valid_triple, "post_2021"]
        * merged.loc[valid_triple, "occ_changed_anzsco2_1y"].astype(int)
    )

    # Keep a compact analysis column set.
    keep_cols = [
        "xwaveid",
        "wave",
        "year",
        "anzsco2",
        "anzsco_major",
        "is_white_collar",
        "aioe2_mean",
        "high_ai_exposure",
        "post_2021",
        "high_ai_x_post2021",
        "pay",
        "pay_source",
        "ln_pay",
        "wage_growth_log_1y",
        "occ_changed_anzsco2_1y",
        "high_ai_x_post2021_x_mobility",
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
            {
                "metric": "pay_source_jbmspay_rows",
                "value": int((merged["pay_source"] == "jbmspay").sum()),
            },
            {
                "metric": "pay_source_crpay_rows",
                "value": int((merged["pay_source"] == "crpay").sum()),
            },
            {
                "metric": "pay_source_jbmpays_rows",
                "value": int((merged["pay_source"] == "jbmpays").sum()),
            },
            {"metric": "aioe2_mean_median_cutoff", "value": float(aioe_cutoff) if pd.notna(aioe_cutoff) else pd.NA},
            {"metric": "rows_with_aioe", "value": int(merged["aioe2_mean"].notna().sum())},
            {
                "metric": "rows_high_ai_exposure",
                "value": int((merged["high_ai_exposure"] == 1).sum()),
            },
            {
                "metric": "rows_low_ai_exposure",
                "value": int((merged["high_ai_exposure"] == 0).sum()),
            },
            {
                "metric": "rows_post_2021",
                "value": int((merged["post_2021"] == 1).sum()),
            },
            {
                "metric": "rows_pre_2021",
                "value": int((merged["post_2021"] == 0).sum()),
            },
            {
                "metric": "rows_with_wage_growth",
                "value": int(merged["wage_growth_log_1y"].notna().sum()),
            },
            {
                "metric": "rows_with_occ_mobility_indicator",
                "value": int(merged["occ_changed_anzsco2_1y"].notna().sum()),
            },
            {
                "metric": "rows_occ_changed_anzsco2_1y",
                "value": int((merged["occ_changed_anzsco2_1y"] == 1).sum()),
            },
            {
                "metric": "years_with_rows",
                "value": ",".join(str(int(y)) for y in sorted(merged["year"].dropna().unique())),
            },
            {
                "metric": "years_with_wage_growth",
                "value": ",".join(
                    str(int(y))
                    for y in sorted(
                        merged.loc[merged["wage_growth_log_1y"].notna(), "year"].dropna().unique()
                    )
                ),
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
