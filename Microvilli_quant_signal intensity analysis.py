import numpy as np
import pandas as pd
import glob
import os
import ast
from scipy.interpolate import interp1d

# =========================
# CONFIG
# =========================

config = {
    "pBTK": r"E:\HU postdoc\Science\Data\B-cell activation\Pharmacology\Imaging\Pooled DMSO files\pBTK",
    "IgM": r"E:\HU postdoc\Science\Data\B-cell activation\Pharmacology\Imaging\Pooled DMSO files\IgM",
}

SPACING = 0.15  # micrometers per step
OUTPUT_DIR = r"E:\HU postdoc\Science\Data\B-cell activation\Pharmacology\Imaging\Pooled DMSO files"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# =========================
# SAFE CSV READER
# =========================

def safe_read_csv(file_path):
    encodings = ["utf-8", "cp1252", "latin1"]

    for enc in encodings:
        try:
            return pd.read_csv(file_path, encoding=enc, skiprows=2)
        except Exception:
            continue

    print(f"Skip file: {file_path}")
    return None

# =========================
# PARSER
# =========================

def parse_profile(cell):
    try:
        if pd.isna(cell):
            return np.array([])
        return np.array(ast.literal_eval(cell), dtype=float)
    except:
        return np.array([])

# =========================
# VALIDATION
# =========================

def is_valid_profile(arr):
    return isinstance(arr, np.ndarray) and arr.size > 1 and np.isfinite(arr).any()

# =========================
# NORMALIZATION
# =========================

def normalize(arr):
    arr = np.asarray(arr, dtype=float)
    denom = np.nanmax(arr) - np.nanmin(arr)
    if denom == 0:
        return np.zeros_like(arr)
    return (arr - np.nanmin(arr)) / denom

# =========================
# MAIN FUNCTION
# =========================

def build_table(folder_path, protein_name):

    all_rows = []
    csv_files = glob.glob(os.path.join(folder_path, "*.csv"))

    for file_path in csv_files:

        print("Processing:", os.path.basename(file_path))

        df = safe_read_csv(file_path)
        if df is None:
            continue

        df.columns = df.columns.str.strip()

        actin_col = "Profile Channel 1"
        protein_col = "Profile Channel 2"

        if actin_col not in df.columns or protein_col not in df.columns:
            print("Missing expected columns:", file_path)
            continue

        if "Blob" not in df.columns:
            print("Missing Blob column:", file_path)
            continue

        df[actin_col] = df[actin_col].apply(parse_profile)
        df[protein_col] = df[protein_col].apply(parse_profile)

        cols = df.columns.tolist()

        actin_idx = cols.index(actin_col)
        protein_idx = cols.index(protein_col)
        blob_idx = cols.index("Blob")

        for row in df.itertuples(index=False, name=None):

            actin = row[actin_idx]
            protein = row[protein_idx]
            blob_id = row[blob_idx]

            if not (is_valid_profile(actin) and is_valid_profile(protein)):
                continue

            # -------------------------
            # Physical coordinate system
            # -------------------------
            actin_x = np.arange(len(actin)) * SPACING
            protein_x = np.arange(len(protein)) * SPACING

            x_common = np.arange(
                0,
                min(actin_x.max(), protein_x.max()) + SPACING,
                SPACING
            )

            # -------------------------
            # Interpolation
            # -------------------------
            actin_i = interp1d(
                actin_x, actin,
                kind="linear",
                bounds_error=False,
                fill_value="extrapolate"
            )(x_common)

            protein_i = interp1d(
                protein_x, protein,
                kind="linear",
                bounds_error=False,
                fill_value="extrapolate"
            )(x_common)

            # -------------------------
            # NORMALIZE INTENSITY ONLY
            # -------------------------
            actin_i = normalize(actin_i)
            protein_i = normalize(protein_i)

            # -------------------------
            # STORE
            # -------------------------
            for x, a, p in zip(x_common, actin_i, protein_i):
                all_rows.append([
                    blob_id,
                    float(x),
                    a,
                    p,
                    os.path.basename(file_path)
                ])

    # =========================
    # OUTPUT TABLES
    # =========================

    df_long = pd.DataFrame(
        all_rows,
        columns=["Blob", "Distance", "Channel1", "Channel2", "File"]
    )

    # stabilize float grouping
    df_long["Distance"] = np.round(df_long["Distance"], 6)

    df_plot = df_long.groupby("Distance", as_index=False).agg(
        Channel1_mean=("Channel1", "mean"),
        Channel1_SD=("Channel1", "std"),
        Channel2_mean=("Channel2", "mean"),
        Channel2_SD=("Channel2", "std"),
    ).sort_values("Distance")

    # =========================
    # SAVE
    # =========================

    df_long.to_csv(
        os.path.join(OUTPUT_DIR, f"{protein_name}_LONG.csv"),
        index=False
    )

    df_plot.to_csv(
        os.path.join(OUTPUT_DIR, f"{protein_name}_PLOT.csv"),
        index=False
    )

    print("\nDONE")
    print("LONG shape:", df_long.shape)
    print("PLOT shape:", df_plot.shape)

    return df_long, df_plot

# =========================
# RUN
# =========================

pBTK_long, pBTK_plot = build_table(config["pBTK"], "pBTK")
IgM_long, IgM_plot = build_table(config["IgM"], "IgM")