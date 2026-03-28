from pathlib import Path
import re

import pandas as pd


RAW_DIR = Path("data/raw")
CLEAN_DIR = Path("data/clean")

DATASETS = {
    "Rperson": RAW_DIR / "hilda_raw_rperson",
    "Combined": RAW_DIR / "hilda_raw_combined_ak",
}

# add l-x combined folder too
EXTRA_COMBINED = RAW_DIR / "hilda_raw_combined_lx"

KEYWORD_PATTERNS = {
    "id": r"(xwaveid|personid|pid|hhid|hid|hhid)",
    "occupation": r"(anzsco|asco|occupation|occ|jobcode)",
    "wage": r"(wage|earn|income|salary|pay|hourly)",
    "hours": r"(hours|hrs|workhr|usualhr)",
    "employment": r"(employ|labour|labor|jobstat|lfstatus)",
}


def list_files(folder: Path, prefix: str):
    files = sorted(folder.glob(f"{prefix}_*240c.dta"))
    return files


def wave_from_name(name: str):
    m = re.search(r"_([a-z])240c\.dta$", name)
    return m.group(1) if m else ""


def load_columns(path: Path):
    # header-only read to keep it fast
    df = pd.read_stata(path, convert_categoricals=False, preserve_dtypes=False)
    return list(df.columns)


def classify_variable(var_name: str):
    var = var_name.lower()
    hits = []
    for tag, pat in KEYWORD_PATTERNS.items():
        if re.search(pat, var):
            hits.append(tag)
    return ",".join(hits)


def profile_dataset(dataset: str, folders):
    rows = []
    file_rows = []

    all_files = []
    for folder, prefix in folders:
        all_files.extend(list_files(folder, prefix))
    all_files = sorted(all_files)

    if not all_files:
        return pd.DataFrame(), pd.DataFrame()

    all_cols = []
    file_colsets = {}

    for fp in all_files:
        cols = load_columns(fp)
        colset = set(cols)
        file_colsets[fp.name] = colset
        all_cols.extend(cols)

        wave = wave_from_name(fp.name)
        file_rows.append(
            {
                "dataset": dataset,
                "file_name": fp.name,
                "wave": wave,
                "n_columns": len(cols),
            }
        )

    value_counts = pd.Series(all_cols).value_counts()
    n_files = len(all_files)

    for col, freq in value_counts.items():
        rows.append(
            {
                "dataset": dataset,
                "variable": col,
                "present_in_files": int(freq),
                "share_of_files": float(freq / n_files),
                "is_stable_core": bool(freq == n_files),
                "tag": classify_variable(col),
            }
        )

    var_df = pd.DataFrame(rows).sort_values(["share_of_files", "variable"], ascending=[False, True])
    file_df = pd.DataFrame(file_rows).sort_values(["wave", "file_name"])
    return var_df, file_df


def main():
    CLEAN_DIR.mkdir(parents=True, exist_ok=True)

    rperson_vars, rperson_files = profile_dataset(
        "Rperson",
        [(RAW_DIR / "hilda_raw_rperson", "Rperson")],
    )

    combined_vars, combined_files = profile_dataset(
        "Combined",
        [
            (RAW_DIR / "hilda_raw_combined_ak", "Combined"),
            (RAW_DIR / "hilda_raw_combined_lx", "Combined"),
        ],
    )

    var_index = pd.concat([rperson_vars, combined_vars], ignore_index=True)
    file_index = pd.concat([rperson_files, combined_files], ignore_index=True)

    var_index.to_csv(CLEAN_DIR / "hilda_variable_index.csv", index=False)
    file_index.to_csv(CLEAN_DIR / "hilda_file_profile.csv", index=False)

    # Short candidate list for next-step extraction
    candidates = var_index[
        (var_index["tag"] != "") & (var_index["share_of_files"] >= 0.8)
    ].copy()
    candidates = candidates.sort_values(["dataset", "tag", "share_of_files", "variable"], ascending=[True, True, False, True])
    candidates.to_csv(CLEAN_DIR / "hilda_variable_candidates.csv", index=False)

    print(f"Saved: {CLEAN_DIR / 'hilda_variable_index.csv'}")
    print(f"Saved: {CLEAN_DIR / 'hilda_file_profile.csv'}")
    print(f"Saved: {CLEAN_DIR / 'hilda_variable_candidates.csv'}")

    for ds in ["Rperson", "Combined"]:
        sub = candidates[candidates["dataset"] == ds]
        print(f"\n[{ds}] candidate variables (share>=0.8 and tagged): {len(sub)}")
        if not sub.empty:
            print(sub[["variable", "tag", "share_of_files"]].head(20).to_string(index=False))


if __name__ == "__main__":
    main()
