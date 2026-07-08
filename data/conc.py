import pandas as pd
import numpy as np

SEX_MAP = {
    "male": 1, "m": 1, "1": 1, 1: 1,
    "female": 0, "f": 0, "0": 0, 0: 0,
}

def normalize_sex(s):
    x = s.astype(str).str.strip().str.lower()
    out = x.map(SEX_MAP)
    if out.isna().any():
        bad = sorted(s[out.isna()].astype(str).unique())
        raise ValueError(f"Unknown sex values: {bad}")
    return out.astype("int8")

def load_ilpd(path):
    df = pd.read_csv(path)
    df = df.rename(columns={
        "Age": "age",
        "Gender": "sex",
        "Total_Bilirubin": "bilirubin",
        "Albumin": "albumin",
        "Alamine_Aminotransferase": "alt",
        "Aspartate_Aminotransferase": "ast",
        "Dataset": "raw_target",
    })

    df["sex"] = normalize_sex(df["sex"])

    # ILPD commonly uses 1 = liver patient, 2 = non-liver patient
    vals = set(pd.Series(df["raw_target"]).dropna().unique().tolist())
    if vals <= {1, 2}:
        df["significant_disease"] = (df["raw_target"] == 1).astype("int8")
    elif vals <= {0, 1}:
        df["significant_disease"] = df["raw_target"].astype("int8")
    else:
        raise ValueError(f"Unexpected ILPD target values: {sorted(vals)}")

    cols = ["ast", "alt", "bilirubin", "albumin", "age", "sex", "significant_disease"]
    return df[cols].copy()

def load_hcv(path):
    df = pd.read_csv(path)
    df = df.rename(columns={
        "Age": "age",
        "Sex": "sex",
        "ALB": "albumin",
        "ALT": "alt",
        "AST": "ast",
        "BIL": "bilirubin",
        "Category": "category",
    })

    df["sex"] = normalize_sex(df["sex"])
    cat = df["category"].astype(str).str.strip()

    keep = {
        "0=Blood Donor": 0,
        "2=Fibrosis": 1,
        "3=Cirrhosis": 1,
    }

    df = df[cat.isin(keep)].copy()
    df["significant_disease"] = df["category"].map(keep).astype("int8")

    cols = ["ast", "alt", "bilirubin", "albumin", "age", "sex", "significant_disease"]
    return df[cols].copy()

def combine(ilpd_path, hcv_path, out_path="combined_liver.csv"):
    ilpd = load_ilpd(ilpd_path)
    hcv = load_hcv(hcv_path)
    df = pd.concat([ilpd, hcv], ignore_index=True)

    for c in ["ast", "alt", "bilirubin", "albumin", "age"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")

    df.to_csv(out_path, index=False)
    return df

if __name__ == "__main__":
    df = combine("ilpd.csv", "hcv.csv")
    print(df.head())
    print(df["significant_disease"].value_counts(dropna=False))
