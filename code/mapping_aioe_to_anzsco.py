from pathlib import Path

import pandas as pd


RAW_DIR = Path("data/raw")
CLEAN_DIR = Path("data/clean")


def normalize_code(value):
    if pd.isna(value):
        return pd.NA
    return str(value).strip().replace(".0", "")


def load_aioe(path):
    df = pd.read_excel(path, sheet_name="LM AIOE")
    df = df[["SOC Code", "Occupation Title", "Language Modeling AIOE"]].copy()
    df.columns = ["soc_code", "soc_title", "aioe"]
    df["soc_code"] = df["soc_code"].map(normalize_code)
    return df.dropna(subset=["soc_code", "aioe"]).drop_duplicates(subset=["soc_code"])


def load_soc_to_isco(path):
    df = pd.read_excel(path, sheet_name="2010 SOC to ISCO-08", header=6)
    df = df[["2010 SOC Code", "ISCO-08 Code", "ISCO-08 Title EN"]].copy()
    df.columns = ["soc_code", "isco_code", "isco_title"]
    df = df.dropna(subset=["soc_code", "isco_code"])
    df["soc_code"] = df["soc_code"].map(normalize_code)
    df["isco_code"] = df["isco_code"].map(normalize_code)
    return df.drop_duplicates(subset=["soc_code", "isco_code"])


def load_isco_to_anzsco(path):
    df = pd.read_excel(path, sheet_name="Table 3", header=5)
    df = df.iloc[:, [0, 2, 4]].copy()
    df.columns = ["isco_code", "anzsco_code", "anzsco_title"]
    df["isco_code"] = df["isco_code"].ffill()
    df = df.dropna(subset=["isco_code", "anzsco_code"])
    df["isco_code"] = df["isco_code"].map(normalize_code)
    df["anzsco_code"] = df["anzsco_code"].map(normalize_code)
    return df.drop_duplicates(subset=["isco_code", "anzsco_code"])


def build_mapping(aioe, soc_isco, isco_anz):
    soc_counts = soc_isco.groupby("soc_code", as_index=False).size().rename(columns={"size": "n_isco"})
    isco_counts = isco_anz.groupby("isco_code", as_index=False).size().rename(columns={"size": "n_anzsco"})

    mapped = aioe.merge(soc_isco, on="soc_code", how="left")
    mapped = mapped.merge(soc_counts, on="soc_code", how="left")
    mapped["aioe_soc_split"] = mapped["aioe"] / mapped["n_isco"]

    mapped = mapped.merge(isco_anz, on="isco_code", how="left")
    mapped = mapped.merge(isco_counts, on="isco_code", how="left")
    mapped["aioe_path"] = mapped["aioe_soc_split"] / mapped["n_anzsco"]

    out = (
        mapped.dropna(subset=["anzsco_code", "aioe_path"])
        .groupby(["anzsco_code", "anzsco_title"], as_index=False)
        .agg(aioe_mean=("aioe_path", "mean"), aioe_sum=("aioe_path", "sum"), n_paths=("aioe_path", "size"))
        .sort_values("aioe_sum", ascending=False)
    )
    return mapped, out, soc_counts, isco_counts


def build_qa(aioe, soc_isco, isco_anz, mapped):
    soc_total = aioe["soc_code"].nunique()
    soc_with_isco = mapped.loc[mapped["isco_code"].notna(), "soc_code"].nunique()
    soc_with_anz = mapped.loc[mapped["anzsco_code"].notna(), "soc_code"].nunique()

    qa = pd.DataFrame(
        [
            {"metric": "aioe_rows", "value": len(aioe)},
            {"metric": "aioe_unique_soc", "value": soc_total},
            {"metric": "aioe_missing_aioe", "value": int(aioe["aioe"].isna().sum())},
            {"metric": "soc_isco_rows", "value": len(soc_isco)},
            {"metric": "soc_isco_soc_multi_map", "value": int((soc_isco.groupby("soc_code").size() > 1).sum())},
            {"metric": "isco_anz_rows", "value": len(isco_anz)},
            {"metric": "isco_anz_isco_multi_map", "value": int((isco_anz.groupby("isco_code").size() > 1).sum())},
            {"metric": "coverage_soc_to_isco", "value": soc_with_isco / soc_total if soc_total else 0},
            {"metric": "coverage_soc_to_anzsco", "value": soc_with_anz / soc_total if soc_total else 0},
            {"metric": "aioe_describe_mean", "value": float(aioe["aioe"].describe()["mean"])},
            {"metric": "aioe_describe_std", "value": float(aioe["aioe"].describe()["std"])},
            {"metric": "aioe_describe_min", "value": float(aioe["aioe"].describe()["min"])},
            {"metric": "aioe_describe_max", "value": float(aioe["aioe"].describe()["max"])},
        ]
    )
    return qa


def main():
    CLEAN_DIR.mkdir(parents=True, exist_ok=True)

    aioe = load_aioe(RAW_DIR / "aioe_raw.xlsx")
    soc_isco = load_soc_to_isco(RAW_DIR / "soc10_to_isco crosswalk.xls")
    isco_anz = load_isco_to_anzsco(RAW_DIR / "isco_to_anzsco.xlsx.xlsx")

    mapped_paths, aioe_by_anzsco, _, _ = build_mapping(aioe, soc_isco, isco_anz)
    qa = build_qa(aioe, soc_isco, isco_anz, mapped_paths)

    mapped_paths.to_csv(CLEAN_DIR / "aioe_mapping_paths.csv", index=False)
    aioe_by_anzsco.to_csv(CLEAN_DIR / "aioe_by_anzsco.csv", index=False)
    soc_isco.to_csv(CLEAN_DIR / "soc_to_isco_mapping.csv", index=False)
    isco_anz.to_csv(CLEAN_DIR / "isco_to_anzsco_mapping.csv", index=False)
    qa.to_csv(CLEAN_DIR / "cleaning_qa_summary.csv", index=False)

    print("Cleaning complete")
    print(f"- aioe_by_anzsco rows: {len(aioe_by_anzsco)}")
    print(f"- coverage_soc_to_anzsco: {qa.loc[qa['metric'] == 'coverage_soc_to_anzsco', 'value'].iloc[0]:.3%}")


if __name__ == "__main__":
    main()
