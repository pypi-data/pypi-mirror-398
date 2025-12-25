import os
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from adjustText import adjust_text
import time, logging
"""
Description: Plots Ref vs Alt allele correlation, highlights significant deviations,
              and calculates log2 fold change for accepted SNPs.
Author: [Shreya Sharma]
Date: [March 23, 2025]
"""
start_time = time.time()
df = pd.read_excel("./output/NKX25/fitting/updated_CORREL_with_bi.xlsx")
df[['base_rsID', 'allele']] = df['rsID'].str.rsplit('_', n=1, expand=True)
df['allele'] = df['allele'].str.strip().str.upper()
df['RefAllele'] = df['RefAllele'].str.strip().str.upper()
df['AltAllele'] = df['AltAllele'].str.strip().str.upper()
df['Fitted_K_iter10'] = df['Fitted_K_iter10'].round(5)
df = df.drop_duplicates(subset=['base_rsID', 'allele'])

accepted_rsIDs = pd.read_csv("./output/NKX25_accepted_rsIDs.csv")
accepted_list = accepted_rsIDs['rsID'].tolist()

# Filter your base_rsID to only include accepted ones
df = df[df['base_rsID'].isin(accepted_list)]

ref_df = df[df['allele'] == df['RefAllele']][['base_rsID', 'Fitted_K_iter10']]
ref_df = ref_df.rename(columns={'Fitted_K_iter10': 'Ref_value'})
alt_df = df[df['allele'] == df['AltAllele']][['base_rsID', 'Fitted_K_iter10']]
alt_df = alt_df.rename(columns={'Fitted_K_iter10': 'Alt_value'})

merged = pd.merge(ref_df, alt_df, on='base_rsID')

if merged.empty:
    print("No valid data points to plot.")
else:
    print(f"Number of points to plot: {len(merged)}")

    plt.figure(figsize=(12, 10))
    all_vals = pd.concat([merged['Ref_value'], merged['Alt_value']])
    
    axis_min = min(all_vals.min() - 0.0005, 0)
    axis_max = all_vals.max() + 0.0001
    plt.xlim(axis_min, axis_max)
    plt.ylim(axis_min, axis_max)

    plt.plot([axis_min, axis_max], [axis_min, axis_max],
             color='gray', linestyle='-', linewidth=1.5, label='y = x')
    offset = 0.05 * (axis_max)
    plt.plot([axis_min, axis_max],[axis_min + offset, axis_max + offset],
             linestyle='-', color='black', linewidth=1, label='parallel +offset')
    plt.plot([axis_min, axis_max], 
             [axis_min - offset, axis_max - offset], 
             linestyle='-', color='black', linewidth=1, label='parallel -offset')
    
    # Plot angled lines
    offset_angle = 15
    slope_above_upper = np.tan(np.deg2rad(45 + offset_angle))
    slope_below_lower = np.tan(np.deg2rad(45 - offset_angle))
    
    plt.plot([0, (1 / slope_above_upper) * (axis_max - axis_min)], [offset, offset + (axis_max - axis_min)],
             linestyle='--', color='black', linewidth=1, label='+15° offset')
    
    plt.plot([offset, offset + (axis_max - axis_min)], [0, slope_below_lower * (axis_max - axis_min)],
             linestyle='--', color='black', linewidth=1, label='-15° offset')

    def is_above_angled_line(x, y):
        y_on_line = offset + slope_above_upper * (x)
        return y > y_on_line

    def is_below_angled_line(x, y):
        y_on_line = slope_below_lower * (x - offset)
        return y < y_on_line

    merged['color'] = merged.apply(
        lambda row: '#254B96' if is_above_angled_line(row['Ref_value'], row['Alt_value']) 
                   else ('#BF212F' if is_below_angled_line(row['Ref_value'], row['Alt_value']) 
                   else 'gray'), axis=1)
    
    x_fill = np.linspace(axis_min, axis_max, 500)
    y_upper = offset + slope_above_upper * x_fill
    y_lower = slope_below_lower * (x_fill - offset)
    plt.fill_between(x_fill, y_lower, y_upper, where=(y_upper >= y_lower),
                 color='lightgray', alpha=0.3, label='Neutral zone')

    plt.scatter(merged['Ref_value'], merged['Alt_value'], color=merged['color'], alpha=0.6)
    texts = []
    for _, row in merged[merged['color'] != 'gray'].iterrows():
        x, y = row['Ref_value'], row['Alt_value']
        label = row['base_rsID']
        
        angle = np.degrees(np.arctan2(y - axis_min, x - axis_min))
        if -45 <= angle <= 45:   # Right quadrant → label left
            texts.append(plt.text(x, y, label, ha='right', va='center', fontsize=9))
        elif 45 < angle <= 135:   # Top quadrant → label bottom
            texts.append(plt.text(x, y, label, ha='center', va='bottom', fontsize=9))
        elif -135 <= angle < -45: # Bottom quadrant → label top
            texts.append(plt.text(x, y, label, ha='center', va='top', fontsize=9))
        else:                     
            texts.append(plt.text(x, y, label, ha='left', va='center', fontsize=9))

    adjust_text(
        texts,
        expand_points=(1.2, 1.2),
        expand_text=(1.1, 1.1),
        arrowprops=dict(
            arrowstyle="->",
            color='black',
            lw=0.7,
            alpha=0.7,
            relpos=(0.5, 0.5)
        ),
        force_text=(0.5, 0.5),
        lim=1000
    )

    plt.xlabel("Ref allele fitted K value", fontsize=12)
    plt.ylabel("Alt allele fitted K value", fontsize=12)
    plt.title("Ref vs Alt allele correlation", fontsize=14)
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.grid(False)
    plt.tight_layout()
    plt.savefig("./output/NKX25/fitting/ref_vs_alt_correlation_plot.png")
    plt.close()
    s = 0.05 * axis_max
    S = ((1 + np.sqrt(3)) / 2) * s

    merged['FC_log2'] = np.log2((merged['Alt_value'] + S) / (merged['Ref_value'] + S))
    allele_info = df[['base_rsID', 'RefAllele', 'AltAllele']].drop_duplicates()
    merged = pd.merge(merged, allele_info, on='base_rsID', how='left')

    increased_df = merged[merged['color'] == '#254B96'][['base_rsID', 'RefAllele', 'AltAllele', 'Ref_value', 'Alt_value', 'FC_log2']]
    decreased_df = merged[merged['color'] == '#BF212F'][['base_rsID', 'RefAllele', 'AltAllele', 'Ref_value', 'Alt_value', 'FC_log2']]

    increased_df = increased_df[['base_rsID', 'RefAllele', 'AltAllele', 'Ref_value', 'Alt_value', 'FC_log2']]
    decreased_df = decreased_df[['base_rsID', 'RefAllele', 'AltAllele', 'Ref_value', 'Alt_value', 'FC_log2']]
    
    with pd.ExcelWriter("./output/NKX25/fitting/FC_table_with_bi.xlsx", engine="openpyxl") as writer:
        merged.to_excel(writer, sheet_name="All_SNPs", index=False)
        increased_df.to_excel(writer, sheet_name="Increased", index=False)
        decreased_df.to_excel(writer, sheet_name="Decrease", index=False)

file_path = "./output/NKX25/fitting/FC_table_with_bi.xlsx"
output_dir = "./output/NKX25/motif_affect_NKX25"
os.makedirs(output_dir, exist_ok=True)

sheet2 = pd.read_excel(file_path, sheet_name=1)
sheet3 = pd.read_excel(file_path, sheet_name=2)
sheet2.iloc[:, 0].dropna().to_csv(os.path.join(output_dir, "NKX25increased_rsIDs.txt"), index=False, header=False)
sheet3.iloc[:, 0].dropna().to_csv(os.path.join(output_dir, "NKX25decreased_rsIDs.txt"), index=False, header=False)
end_time = time.time()
total_time = end_time - start_time
print(f"Total time taken: {total_time:.2f} seconds")