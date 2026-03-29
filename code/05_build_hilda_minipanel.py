from pathlib import Path
import re

import pandas as pd


RAW_DIR = Path("data/raw")
CLEAN_DIR = Path("data/clean")

COMBINED_FOLDERS = [
    RAW_DIR / "hilda_raw_combined_ak",
    RAW_DIR / "hilda_raw_combined_lx",
]

# Keep this list short and model-oriented.
VAR_STEMS = [
    "jbmo62",    # current main job occupation: 2-digit ANZSCO 2006
    "jbmo61",    # current main job occupation: 1-digit ANZSCO 2006
    "jbcmocc",   # occupation changed since last interview (not occupation code)
    "jbocct",    # tenure in current occupation (years)
    "hehearn",   # earnings-related
    "jbmspay",   # pay-related
    "jbmpays",   # pay-related
    "crpay",     # pay-related
    "hgsex",     # sex
    "hgage",     # age
    "hhstate",   # state
]


def wave_from_filename(name: str) -> str:
    m = re.search(r"_([a-z])240c\.dta$", name)
    return m.group(1) if m else ""


def year_from_wave(wave: str):
    if not wave:
        return pd.NA
    return 2001 + (ord(wave) - ord("a"))


def list_combined_files():
    files = []
    for folder in COMBINED_FOLDERS:
        files.extend(sorted(folder.glob("Combined_*240c.dta")))
    return sorted(files)


def get_columns(path: Path):
    df = pd.read_stata(path, convert_categoricals=False)
    return list(df.columns)


def extract_one_wave(path: Path):
    wave = wave_from_filename(path.name)
    if not wave:
        return None, None

    cols = get_columns(path)

    selected = ["xwaveid"]
    stem_map = {}
    for stem in VAR_STEMS:
        candidate = f"{wave}{stem}"
        if candidate in cols:
            selected.append(candidate)
            stem_map[candidate] = stem

    df = pd.read_stata(path, columns=selected, convert_categoricals=False)
    df = df.rename(columns=stem_map)
    df["wave"] = wave
    df["year"] = year_from_wave(wave)

    coverage = {
        "file_name": path.name,
        "wave": wave,
        "year": year_from_wave(wave),
        "n_rows": len(df),
        "n_selected_vars": len(selected) - 1,
    }
    for stem in VAR_STEMS:
        coverage[f"has_{stem}"] = int(stem in df.columns)

    return df, coverage


def main():
    CLEAN_DIR.mkdir(parents=True, exist_ok=True)

    files = list_combined_files()
    if not files:
        raise FileNotFoundError("No Combined_*.dta files found under HILDA raw folders.")

    panels = []
    coverages = []

    for fp in files:
        df, cov = extract_one_wave(fp)
        if df is None:
            continue
        panels.append(df)
        coverages.append(cov)

    panel = pd.concat(panels, ignore_index=True, sort=False)
    coverage = pd.DataFrame(coverages).sort_values("wave")

    # Keep id as string for safe merges.
    panel["xwaveid"] = panel["xwaveid"].astype(str).str.strip()

    panel_out = CLEAN_DIR / "10_hilda_combined_minipanel.csv"
    cov_out = CLEAN_DIR / "11_hilda_combined_variable_coverage.csv"

    panel.to_csv(panel_out, index=False)
    coverage.to_csv(cov_out, index=False)

    print(f"Saved: {panel_out}")
    print(f"Saved: {cov_out}")
    print(f"Rows: {len(panel):,}")
    print(f"Waves: {panel['wave'].nunique()} ({panel['wave'].min()} to {panel['wave'].max()})")
    print("Variable availability by wave:")
    print(coverage[["wave", "n_selected_vars"]].to_string(index=False))


if __name__ == "__main__":
    main()
