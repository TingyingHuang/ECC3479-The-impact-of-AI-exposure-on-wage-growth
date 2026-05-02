from pathlib import Path

import pandas as pd
import statsmodels.api as sm


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = PROJECT_ROOT / "data" / "clean" / "08_wages_ai_analysis_panel.csv"
OUT_COEF = PROJECT_ROOT / "output" / "panel_twfe_trial_coefficients.csv"
OUT_SUMMARY = PROJECT_ROOT / "output" / "panel_twfe_trial_summary.txt"


def within_transform(df: pd.DataFrame, cols: list[str], entity_col: str) -> pd.DataFrame:
    means = df.groupby(entity_col)[cols].transform("mean")
    return df[cols] - means


def build_sample() -> pd.DataFrame:
    if not DATA_PATH.exists():
        raise FileNotFoundError(f"Missing input data: {DATA_PATH}")

    df = pd.read_csv(DATA_PATH)

    numeric_cols = ["year", "log_wage", "ai_exposure", "state", "edu"]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    required_cols = ["person_id", "year", "log_wage", "ai_exposure", "state", "edu"]
    df = df.dropna(subset=required_cols).copy()
    df = df.loc[df["year"].between(2020, 2024)].copy()

    # FE needs at least 2 time periods per person.
    df = df.groupby("person_id").filter(lambda g: g["year"].nunique() >= 2).copy()

    return df


def estimate_twfe(df: pd.DataFrame):
    for yr in [2021, 2022, 2023, 2024]:
        df[f"ai_x_yr{yr}"] = df["ai_exposure"] * (df["year"] == yr).astype(int)

    # Age is excluded in TWFE because age = individual baseline age + common year trend,
    # which is collinear with individual and year fixed effects.
    x_cols = [
        "ai_x_yr2021",
        "ai_x_yr2022",
        "ai_x_yr2023",
        "ai_x_yr2024",
        "state",
        "edu",
    ]

    y_within = within_transform(df, ["log_wage"], "person_id")["log_wage"]
    x_within = within_transform(df, x_cols, "person_id")

    year_fe = pd.get_dummies(df["year"].astype(int), prefix="yr", drop_first=True).astype(float)
    year_fe_within = year_fe - year_fe.groupby(df["person_id"]).transform("mean")

    x = pd.concat([x_within, year_fe_within], axis=1).astype(float)

    model = sm.OLS(y_within, x).fit(
        cov_type="cluster",
        cov_kwds={"groups": df["person_id"]},
    )
    return model


def save_outputs(model, df: pd.DataFrame) -> None:
    coef_rows = ["ai_x_yr2021", "ai_x_yr2022", "ai_x_yr2023", "ai_x_yr2024"]
    coef_table = pd.DataFrame(
        {
            "coef": model.params[coef_rows],
            "std_err": model.bse[coef_rows],
            "p_value": model.pvalues[coef_rows],
            "ci_low": model.conf_int().loc[coef_rows, 0],
            "ci_high": model.conf_int().loc[coef_rows, 1],
        }
    ).round(6)

    coef_table.to_csv(OUT_COEF)

    with OUT_SUMMARY.open("w", encoding="utf-8") as f:
        f.write("Two-way FE trial model (entity FE via within transform + year FE)\n")
        f.write(f"Observations: {len(df):,}\n")
        f.write(f"Individuals: {df['person_id'].nunique():,}\n\n")
        f.write("Key AI exposure x year coefficients:\n")
        f.write(coef_table.to_string())
        f.write("\n\nFull model summary:\n")
        f.write(str(model.summary()))


if __name__ == "__main__":
    sample = build_sample()
    twfe_model = estimate_twfe(sample)
    save_outputs(twfe_model, sample)

    print("Saved:", OUT_COEF)
    print("Saved:", OUT_SUMMARY)
    print(f"Obs={len(sample):,}, Persons={sample['person_id'].nunique():,}")
