from pathlib import Path
import re

import pandas as pd


RAW_DIR = Path("data/raw")
CLEAN_DIR = Path("data/clean")

HILDA_DIRS = [
    "hilda_raw_combined_ak",
    "hilda_raw_combined_lx",
    "hilda_raw_rperson",
    "hilda_raw_eperson",
]

PATTERN = re.compile(r"^(?P<dataset>[A-Za-z]+)_(?P<wave>[a-z])240c\.dta$", re.IGNORECASE)


def main():
    rows = []

    for folder in HILDA_DIRS:
        base = RAW_DIR / folder
        if not base.exists():
            continue

        for fp in sorted(base.glob("*.dta")):
            m = PATTERN.match(fp.name)
            dataset = m.group("dataset") if m else "unknown"
            wave = m.group("wave") if m else ""

            rows.append(
                {
                    "folder": folder,
                    "file_name": fp.name,
                    "dataset": dataset,
                    "wave": wave,
                    "wave_year_approx": 2001 + (ord(wave) - ord("a")) if wave else pd.NA,
                    "file_path": str(fp),
                }
            )

    out = pd.DataFrame(rows)
    out = out.sort_values(["dataset", "wave", "file_name"]).reset_index(drop=True)

    CLEAN_DIR.mkdir(parents=True, exist_ok=True)
    out_path = CLEAN_DIR / "02_hilda_file_index.csv"
    out.to_csv(out_path, index=False)

    print(f"Indexed files: {len(out)}")
    if not out.empty:
        print("By dataset:")
        print(out.groupby("dataset").size().sort_values(ascending=False).to_string())
        print("\nWave coverage:")
        print(f"min={out['wave'].min()}, max={out['wave'].max()}, unique={out['wave'].nunique()}")
    print(f"Saved: {out_path}")


if __name__ == "__main__":
    main()
