import os
import pandas as pd
from collections import defaultdict
import time, logging
"""
Author: [Shreya Sharma]
Date: [April 08, 2025]
Description:
	This Python script processes nucleotide count data from sequencing libraries and bound/unbound experiments
	to compute enrichment metrics and combined results. Only rows included here if matched rsID in GATA4_accepted_rsIDs.csv. 
	This output file will be used for fitting.

"""

# =========================== CONFIGURATION ===========================
DATA_DIR_LIB = "./output/GATA4/CarriedForward"
DATA_DIR_UNB = "./output/GATA4/CarriedForward"
DATA_DIR_BOUND = "./output/GATA4/bound_vs_unbound_without_pseudocounts"

LIB_FILES = {
    "R52_49.csv": "Library_1",
    "R52_65.csv": "Library_2"
}

TOTAL_COUNT_L1 = 24744496
TOTAL_COUNT_L2 = 24756936

FILES_REPS = [
    ("0", "R52_34_Vs_R52_35.csv"), ("100", "R52_36_Vs_R52_37.csv"), ("500", "R52_38_Vs_R52_39.csv"), ("1000", "R52_40_Vs_R52_41.csv"),
    ("1500", "R52_42_Vs_R52_43.csv"), ("2000", "R52_44_Vs_R52_45.csv"), ("3000", "R52_46_Vs_R52_47.csv"), ("0", "R52_50_Vs_R52_51.csv"),
    ("100", "R52_52_Vs_R52_53.csv"), ("500", "R52_54_Vs_R52_55.csv"), ("1000", "R52_56_Vs_R52_57.csv"),
    ("1500", "R52_58_Vs_R52_59.csv"), ("2000", "R52_60_Vs_R52_61.csv"), ("3000", "R52_62_Vs_R52_63.csv")
]

NUCLEOTIDES = ["A", "T", "G", "C"]
CONCENTRATIONS = [0, 100, 500, 1000, 1500, 2000, 3000]
REPLICATES = ["R1", "R2"]

# =========================== FUNCTIONS ===========================
def load_library_counts():
    counts = defaultdict(lambda: {"Library_1": 0, "Library_2": 0})
    for filename, lib in LIB_FILES.items():
        df = pd.read_csv(os.path.join(DATA_DIR_LIB, filename))
        if not {"rsID", *NUCLEOTIDES}.issubset(df.columns):
            raise ValueError(f"Missing required columns in {filename}")
        for _, row in df.iterrows():
            rsid = row["rsID"]
            if isinstance(rsid, str) and rsid.startswith("rs"):
                for nt in NUCLEOTIDES:
                    counts[f"{rsid}_{nt}"][lib] = row[nt]
    return counts

def load_counts(data_dir, file_mapping, suffix_func, filename_func):
    counts = defaultdict(lambda: defaultdict(int))
    for conc, file in file_mapping:
        suffix = suffix_func(file)
        file_to_read = filename_func(file)
        path = os.path.join(data_dir, file_to_read)
        if not os.path.exists(path):
            raise FileNotFoundError(f"Expected file not found: {path}")
        df = pd.read_csv(path)
        for _, row in df.iterrows():
            rsid = row["rsID"]
            if isinstance(rsid, str) and rsid.startswith("rs"):
                for nt in NUCLEOTIDES:
                    key = f"{rsid}_{nt}"
                    col = f"{conc}_count_{suffix}"
                    counts[key][col] = row[nt]
    return counts

def suffix_unbound(file):
    unb_num = int(file.split("_Vs_")[1].split("_")[1].replace(".csv", ""))
    return f"R1_unb" if unb_num < 49 else f"R2_unb"

def suffix_bound(file):
    bnd_num = int(file.split("_Vs_")[1].split("_")[1].replace(".csv", ""))
    return f"R1_b" if bnd_num < 49 else f"R2_b"

def filename_unbound(file):
    return file.split("_Vs_")[1]

def filename_bound(file):
    return file

def construct_combined_dataframe(lib_counts, unb_counts, bnd_counts):
    all_keys = set(lib_counts.keys()) | set(unb_counts.keys()) | set(bnd_counts.keys())
    rows = []
    for key in all_keys:
        row = [key, lib_counts.get(key, {}).get("Library_1", 0), lib_counts.get(key, {}).get("Library_2", 0)]
        for conc in CONCENTRATIONS:
            for rep in REPLICATES:
                row.append(unb_counts.get(key, {}).get(f"{conc}_count_{rep}_unb", 0))
        for conc in CONCENTRATIONS:
            for rep in REPLICATES:
                row.append(bnd_counts.get(key, {}).get(f"{conc}_count_{rep}_b", 0))
        rows.append(row)
    
    columns = ["rsID", "Library_1", "Library_2"]
    columns += [f"{c}_count_{r}_unb" for c in CONCENTRATIONS for r in REPLICATES]
    columns += [f"{c}_count_{r}_b" for c in CONCENTRATIONS for r in REPLICATES]
    
    df = pd.DataFrame(rows, columns=columns)
    return df

def calculate_enrichment_unbound(df):
    for conc in CONCENTRATIONS:
        for rep in REPLICATES:
            b_col = f"{conc}_count_{rep}_b"
            u_col = f"{conc}_count_{rep}_unb"
            e_col = f"Enrich_{conc}_{rep}_b_unb"

            total_b = df[b_col].sum()
            total_u = df[u_col].sum()
            
            print(f"Total bound for {conc} {rep}: {total_b}")
            print(f"Total unbound for {conc} {rep}: {total_u}")

            # Pseudocounts based on total reads
            pseudo_u = (2.5 * total_u) / 1e6

            df[e_col] = ((df[b_col]) / total_b) / ((df[u_col] + pseudo_u) /(total_u  + pseudo_u))
    return df

def calculate_enrichment_library(df):
    for conc in CONCENTRATIONS:
        for rep in REPLICATES:
            b_col = f"{conc}_count_{rep}_b"
            if rep == "R1":
                lib_col = "Library_1"
                lib_total = TOTAL_COUNT_L1
            else:
                lib_col = "Library_2"
                lib_total = TOTAL_COUNT_L2

            total_b = df[b_col].sum()

            # Pseudocounts based on total reads
            pseudo_lib = (2.5 * lib_total) / 1e6

            e_col = f"Enrich_{conc}_{rep}_b_lib"

            df[e_col] = ((df[b_col]) / total_b) / ((df[lib_col] + pseudo_lib) / (lib_total + pseudo_lib))
    return df

# =========================== MAIN EXECUTION ===========================
if __name__ == "__main__":
    start_time = time.time()
    lib_counts = load_library_counts()
    unb_counts = load_counts(DATA_DIR_UNB, FILES_REPS, suffix_unbound, filename_unbound)
    bnd_counts = load_counts(DATA_DIR_BOUND, FILES_REPS, suffix_bound, filename_bound)
    print(f"Total bound entries: {len(bnd_counts)}")
    print(f"Total unbound entries: {len(unb_counts)}")

    combined_df = construct_combined_dataframe(lib_counts, unb_counts, bnd_counts)
    
    # ====== Filtering based on accepted rsIDs ======
    accepted_rsids = pd.read_csv("./output/GATA4_accepted_rsIDs.csv")['rsID'].dropna().astype(str)
    print(f"Accepted rsIDs loaded: {accepted_rsids.shape}")
    combined_df["base_rsid"] = combined_df["rsID"].str.split("_").str[0]
    combined_df = combined_df[combined_df["base_rsid"].isin(accepted_rsids)]
    combined_df.drop(columns=["base_rsid"], inplace=True)
    print(f"Filtered combined_df: {combined_df.shape[0]} rows retained")

    # Now run enrichment only on filtered data
    combined_df = calculate_enrichment_unbound(combined_df)
    combined_df = calculate_enrichment_library(combined_df)

    combined_df.to_csv("./output/GATA4/merged_df_GATA4_with_zeronM_pseudocounts_2point5.csv", index=False)
    print("File saved: merged_df_GATA4_with_zeronM_pseudocounts_2point5.csv")
    end_time = time.time()
    total_time = end_time - start_time
    print(f"Total time taken: {total_time:.2f} seconds")
