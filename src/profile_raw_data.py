from pathlib import Path

import pandas as pd


def print_section(title: str) -> None:
    print(f"\n{'=' * 12} {title} {'=' * 12}")


def main() -> None:
    raw = Path("data/raw")

    print_section("Raw Folder Inventory")
    for p in sorted(raw.iterdir()):
        tag = "DIR" if p.is_dir() else "FILE"
        print(f"[{tag}] {p.name}")

    # AIOE
    print_section("AIOE: LM AIOE")
    aioe = pd.read_excel(raw / "aioe_raw.xlsx", sheet_name="LM AIOE")
    aioe["soc10"] = aioe["SOC Code"].astype(str).str.strip()
    print("shape:", aioe.shape)
    print("columns:", list(aioe.columns))
    print("missing:", aioe.isna().sum().to_dict())
    print("duplicate SOC Code:", int(aioe.duplicated(subset=["SOC Code"]).sum()))
    print(aioe.head(5).to_string(index=False))

    # SOC to ISCO
    print_section("SOC2010 -> ISCO08")
    soc_isco = pd.read_excel(
        raw / "soc10_to_isco crosswalk.xls",
        sheet_name="2010 SOC to ISCO-08",
        header=6,
    )
    soc_isco = soc_isco[["2010 SOC Code", "2010 SOC Title", "part", "ISCO-08 Code", "ISCO-08 Title EN"]].copy()
    soc_isco = soc_isco.dropna(subset=["2010 SOC Code", "ISCO-08 Code"])
    soc_isco["soc10"] = soc_isco["2010 SOC Code"].astype(str).str.strip()
    soc_isco["isco08"] = soc_isco["ISCO-08 Code"].astype(str).str.replace(".0", "", regex=False).str.strip()
    print("shape:", soc_isco.shape)
    print("unique SOC:", soc_isco["soc10"].nunique())
    print("unique ISCO:", soc_isco["isco08"].nunique())
    print("duplicate SOC-ISCO pairs:", int(soc_isco.duplicated(subset=["soc10", "isco08"]).sum()))
    soc_multi = soc_isco.groupby("soc10")["isco08"].nunique().sort_values(ascending=False)
    print("SOC mapping to >1 ISCO:", int((soc_multi > 1).sum()))
    print("top SOC multiplicity:", soc_multi.head(10).to_dict())
    print(soc_isco.head(5).to_string(index=False))

    # ISCO to ANZSCO
    print_section("ISCO08 -> ANZSCO (Table 3)")
    isco_anz = pd.read_excel(
        raw / "isco_to_anzsco.xlsx.xlsx",
        sheet_name="Table 3",
        header=5,
    )
    isco_anz = isco_anz.iloc[:, [0, 1, 2, 4]].copy()
    isco_anz.columns = ["isco08", "isco08_title", "anzsco", "anzsco_title"]
    isco_anz["isco08"] = isco_anz["isco08"].ffill()
    isco_anz = isco_anz.dropna(subset=["isco08", "anzsco"])
    isco_anz["isco08"] = isco_anz["isco08"].astype(str).str.replace(".0", "", regex=False).str.strip()
    isco_anz["anzsco"] = isco_anz["anzsco"].astype(str).str.replace(".0", "", regex=False).str.strip()
    print("shape:", isco_anz.shape)
    print("unique ISCO:", isco_anz["isco08"].nunique())
    print("unique ANZSCO:", isco_anz["anzsco"].nunique())
    print("duplicate ISCO-ANZSCO pairs:", int(isco_anz.duplicated(subset=["isco08", "anzsco"]).sum()))
    isco_multi = isco_anz.groupby("isco08")["anzsco"].nunique().sort_values(ascending=False)
    print("ISCO mapping to >1 ANZSCO:", int((isco_multi > 1).sum()))
    print("top ISCO multiplicity:", isco_multi.head(10).to_dict())
    print(isco_anz.head(5).to_string(index=False))

    # SOC version crosswalk
    print_section("SOC2010 -> SOC2018")
    soc_shift = pd.read_excel(
        raw / "soc_2010_to_2018_crosswalk (1).xlsx",
        sheet_name="Sorted by 2010",
        header=8,
    )
    soc_shift = soc_shift[["2010 SOC Code", "2018 SOC Code"]].dropna().copy()
    soc_shift["soc2010"] = soc_shift["2010 SOC Code"].astype(str).str.strip()
    soc_shift["soc2018"] = soc_shift["2018 SOC Code"].astype(str).str.strip()
    print("shape:", soc_shift.shape)
    print("unique SOC2010:", soc_shift["soc2010"].nunique())
    print("unique SOC2018:", soc_shift["soc2018"].nunique())
    print("duplicate 2010-2018 pairs:", int(soc_shift.duplicated(subset=["soc2010", "soc2018"]).sum()))
    print(soc_shift.head(5).to_string(index=False))

    # Coverage chain for your use case
    print_section("Coverage: AIOE SOC -> ISCO -> ANZSCO")
    m1 = aioe[["soc10"]].drop_duplicates().merge(
        soc_isco[["soc10", "isco08"]].drop_duplicates(),
        on="soc10",
        how="left",
    )
    m2 = m1.merge(
        isco_anz[["isco08", "anzsco"]].drop_duplicates(),
        on="isco08",
        how="left",
    )

    soc_cov = m1["isco08"].notna().mean()
    anz_cov = m2["anzsco"].notna().mean()
    print(f"AIOE SOC covered by SOC->ISCO: {soc_cov:.3%}")
    print(f"AIOE SOC covered through ANZSCO: {anz_cov:.3%}")


if __name__ == "__main__":
    main()
