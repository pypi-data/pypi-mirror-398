import os
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import logging
import numpy as np
import time, logging
"""
Author: [Shreya Sharma]
Date: [MAy 14, 2025]
Description: 
	This Python script analyzes SNPs (rsIDs) that alter transcription factor binding by extracting fitted K-values for reference and alternative alleles. It constructs and visualizes heatmaps of these allele-specific K-values for rsIDs with increased or decreased motif activity, based on provided input files. The script handles missing data, logs key steps, and saves individual and combined heatmaps to the specified output directory.
"""

def setup_logging():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def load_rsids(file_path):
    if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
        return pd.read_csv(file_path, header=None)[0].str.split('_').str[0].tolist()
    else:
        logging.warning(f"File {file_path} is missing or empty.")
        return []

def build_allele_cvalue_matrix(rsid_list, c_values_df, allele_info_df):
    data = {}
    for rsid in rsid_list:
        if rsid in allele_info_df.index:
            ref = allele_info_df.loc[rsid, 'RefAllele']
            alt = allele_info_df.loc[rsid, 'AltAllele']
            all_bases = ['A', 'T', 'G', 'C']
            other_alts = [b for b in all_bases if b not in [ref, alt]]
            labels = ['Ref Allele', 'Alt Allele 1', 'Alt Allele 2', 'Alt Allele 3']
            alleles = [ref, alt] + other_alts
            cvals = []
            for allele in alleles:
                full_id = f"{rsid}_{allele}"
                if full_id in c_values_df['full_rsID'].values:
                    val = c_values_df.loc[c_values_df['full_rsID'] == full_id, 'Fitted_K_iter10'].values[0]
                    val = round(val, 5)
                else:
                    val = np.nan
                cvals.append(val)
            data[rsid] = dict(zip(labels, cvals))
    return pd.DataFrame.from_dict(data, orient='index')

def main():
    setup_logging()
    start_time = time.time()
    fitted_k_file = "./output/GATA4/fitting/iteration_results_withunb_with_bi/fitted_K_results_iteration_10.csv"
    increased_rsids_path = "./output/GATA4/motif_affect_GATA4/GATA4increased_rsIDs.txt"
    decreased_rsids_path = "./output/GATA4/motif_affect_GATA4/GATA4decreased_rsIDs.txt"
    allele_info_file = "./output/GATA4/bound_vs_unbound/R52_38_Vs_R52_39.csv"
    output_dir = "./output/GATA4/fitting/K_value_heatmaps"

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        logging.info(f"Output directory {output_dir} created.")

    c_values_df = pd.read_csv(fitted_k_file)
    c_values_df.rename(columns={c_values_df.columns[0]: 'rsID'}, inplace=True)
    c_values_df['full_rsID'] = c_values_df['rsID']
    c_values_df['base_rsID'] = c_values_df['rsID'].str.split('_').str[0]

    allele_info_df = pd.read_csv(allele_info_file)
    allele_info_df.set_index('rsID', inplace=True)

    increased_rsids = load_rsids(increased_rsids_path)
    decreased_rsids = load_rsids(decreased_rsids_path)

    matched_increased = list(set(c_values_df['base_rsID']).intersection(increased_rsids))
    matched_decreased = list(set(c_values_df['base_rsID']).intersection(decreased_rsids))

    logging.info(f"Matched {len(matched_increased)} increased rsIDs.")
    logging.info(f"Matched {len(matched_decreased)} decreased rsIDs.")

    increased_matrix = build_allele_cvalue_matrix(matched_increased, c_values_df, allele_info_df) if matched_increased else pd.DataFrame()
    decreased_matrix = build_allele_cvalue_matrix(matched_decreased, c_values_df, allele_info_df) if matched_decreased else pd.DataFrame()

    if not increased_matrix.empty:
        increased_matrix_sorted = increased_matrix.sort_values(by=increased_matrix.columns[0], ascending=False)
        increased_matrix_sorted.to_excel('increased_matrix_sorted_scatter_ref_alts_GATA4.xlsx', index=False)
        plt.figure(figsize=(1.5, 0.1 * len(increased_matrix_sorted)))
        ax = sns.heatmap(increased_matrix_sorted, cmap='coolwarm', cbar=True, annot=False, fmt=".5f")
        plt.title('K-values Heatmap: Increased rsIDs', fontsize=2.5, fontweight='bold')
        plt.xlabel('Nucleotide', fontsize=2.5, fontweight='bold')
        plt.ylabel('rsID', fontsize=2.5, fontweight='bold')
        plt.xticks(fontsize=2)
        plt.yticks(fontsize=2)
        
        cbar = ax.collections[0].colorbar
        cbar.set_label("K-value", fontsize=2.5, fontweight='bold')
        cbar.ax.tick_params(labelsize=2)
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, 'increased_K_values_heatmap_alleles.png'), dpi=400)
        plt.close()

    # Decreased matrix sorted and plotted
    if not decreased_matrix.empty:
        decreased_matrix_sorted = decreased_matrix.sort_values(by=decreased_matrix.columns[0], ascending=False)
        decreased_matrix_sorted.to_excel('decreased_matrix_sorted_scatter_ref_alts_GATA4.xlsx', index=False)
        plt.figure(figsize=(1.5, 0.1 * len(decreased_matrix_sorted)))
        ax = sns.heatmap(decreased_matrix_sorted, cmap='coolwarm', cbar=True, annot=False, fmt=".5f")
        plt.title('K-values Heatmap: Decreased rsIDs', fontsize=2.5, fontweight='bold')
        plt.xlabel('Nucleotide', fontsize=2.5, fontweight='bold')
        plt.ylabel('rsID', fontsize=2.5, fontweight='bold')
        plt.xticks(fontsize=2)
        plt.yticks(fontsize=2)
        
        cbar = ax.collections[0].colorbar
        cbar.set_label("K-value", fontsize=2.5, fontweight='bold')
        cbar.ax.tick_params(labelsize=2)
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, 'decreased_K_values_heatmap_alleles.png'), dpi=400)
        plt.close()

    # Combined sorted heatmaps
    if not increased_matrix.empty and not decreased_matrix.empty:
        increased_matrix_sorted = increased_matrix.sort_values(by=increased_matrix.columns[0], ascending=False)
        decreased_matrix_sorted = decreased_matrix.sort_values(by=decreased_matrix.columns[0], ascending=False)

        fig, axes = plt.subplots(1, 2, figsize=(6, max(0.2 * len(increased_matrix_sorted), 0.2 * len(decreased_matrix_sorted))))
        sns.heatmap(increased_matrix_sorted, cmap='coolwarm', cbar=True, annot=False, ax=axes[0])
        axes[0].set_title('Increased rsIDs', fontsize=8, fontweight='bold')
        axes[0].set_xlabel('Nucleotide', fontsize=8, fontweight='bold')
        axes[0].set_ylabel('rsID', fontsize=8, fontweight='bold')

        sns.heatmap(decreased_matrix_sorted, cmap='coolwarm', cbar=True, annot=False, ax=axes[1])
        axes[1].set_title('Decreased rsIDs', fontsize=8, fontweight='bold')
        axes[1].set_xlabel('Nucleotide', fontsize=8, fontweight='bold')
        axes[1].set_ylabel('rsID', fontsize=8, fontweight='bold')

        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, 'combined_K_values_heatmap_alleles.png'), dpi=400)
        plt.close()

    if increased_matrix.empty and decreased_matrix.empty:
        logging.warning("No matching increased or decreased rsIDs found in the C-value file. No heatmap created.")
        
    end_time = time.time()
    total_time = end_time - start_time
    print(f"Total time taken: {total_time:.2f} seconds")

if __name__ == "__main__":
    main()
