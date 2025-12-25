import pandas as pd
from pathlib import Path
import time
"""
Author:[Shreya Sharma]
Date:[May 12, 2025]
Description: 
	Sorts an Excel file by the "Fitted_K_iter10" column in descending order and saves the top 500 and all rows to separate files, creating directories if needed.
"""
start_time = time.time()
input_path = Path("./output/TBX5/fitting/iteration_results_withunb_with_bi/fitted_K_results_iteration_10.xlsx")
df = pd.read_excel(input_path)

df["base_rsid"] = df["rsID"].str.split("_").str[0]

df_sorted = df.sort_values("Fitted_K_iter10", ascending=False)
df_unique = df_sorted.drop_duplicates(subset="base_rsid", keep="first")

output_meme = Path("./output/TBX5/motif_affect_TBX5/MEME/200_sequences_for_meme.xlsx")
output_lsgkm = Path("./output/TBX5/LSGKM/all_sequences_for_lsgkm.xlsx")

output_meme.parent.mkdir(parents=True, exist_ok=True)
output_lsgkm.parent.mkdir(parents=True, exist_ok=True)

df_unique.head(200).to_excel(output_meme, index=False)
df_unique.to_excel(output_lsgkm, index=False)
end_time = time.time()
total_time = end_time - start_time
print(f"Total time taken: {total_time:.2f} seconds")
