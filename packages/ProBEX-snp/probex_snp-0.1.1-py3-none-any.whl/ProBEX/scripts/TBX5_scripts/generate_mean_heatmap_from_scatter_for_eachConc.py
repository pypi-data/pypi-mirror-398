import os
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import logging, time


"""
Author: [Shreya Sharma]
Date:[2024-12-23]
Description:
	This Python script processes allele-specific enrichment data across various concentrations, computes mean enrichments for SNPs, and visualizes them using heatmaps. It compares increased and decreased binding events by SNP across treatment conditions.

"""

concentration_map = {
        "R52_78_Vs_R52_79": "3000 nM",
        "R52_76_Vs_R52_77": "2000 nM",
        "R52_74_Vs_R52_75": "1500 nM",
        "R52_72_Vs_R52_73": "1000 nM",
        "R52_70_Vs_R52_71": "500 nM", 
        "R52_68_Vs_R52_69": "100 nM",
        "R52_66_Vs_R52_67": "0 nM",   
        "R52_82_Vs_R52_83": "0 nM",
        "R52_84_Vs_R52_85": "100 nM", 
        "R52_86_Vs_R52_87": "500 nM", 
        "R52_88_Vs_R52_89": "1000 nM",
        "R52_90_Vs_R52_91": "1500 nM",
        "R52_92_Vs_R52_93": "2000 nM", 
        "R52_94_Vs_R52_95": "3000 nM"
    }
def get_keys_from_concentration(concentration_value):
    matching_keys = [key for key, value in concentration_map.items() if value == concentration_value]
    return matching_keys if matching_keys else ["Concentration not found"]

def get_other_alleles(ref_allele, alt_allele):
    all_alleles = ["A", "T", "G", "C"]
    all_alleles.remove(ref_allele)
    all_alleles.remove(alt_allele)
    return all_alleles

def calculate_mean_enrichment(rsid, file1, file2):
    df1 = pd.read_csv(file1)
    df2 = pd.read_csv(file2)
    
    if rsid in df1['rsID'].values and rsid in df2['rsID'].values:
        df1_filtered = df1[df1["rsID"] == rsid]
        df2_filtered = df2[df2["rsID"] == rsid]
        ref_allele = df1.loc[df1["rsID"] == rsid, "RefAllele"].iloc[0] if (df1.loc[df1["rsID"] == rsid, "RefAllele"].values == df2.loc[df2["rsID"] == rsid, "RefAllele"].values).all() else None
        alt_allele = df1.loc[df1["rsID"] == rsid, "AltAllele"].iloc[0] if (df1.loc[df1["rsID"] == rsid, "AltAllele"].values == df2.loc[df2["rsID"] == rsid, "AltAllele"].values).all() else None

        alt2_allele, alt3_allele = get_other_alleles(ref_allele, alt_allele)
        if df1_filtered.empty or df2_filtered.empty:
            return None, None, None, None
        
        try:
            enrich_ref_allele_1 = df1_filtered[f'Enrich {ref_allele}']
            enrich_ref_allele_2 = df2_filtered[f'Enrich {ref_allele}']
            enrich_alt_allele_1 = df1_filtered[f'Enrich {alt_allele}']
            enrich_alt_allele_2 = df2_filtered[f'Enrich {alt_allele}']
            enrich_alt2_allele_1 = df1_filtered[f'Enrich {alt2_allele}']
            enrich_alt2_allele_2 = df2_filtered[f'Enrich {alt2_allele}']
            enrich_alt3_allele_1 = df1_filtered[f'Enrich {alt3_allele}']
            enrich_alt3_allele_2 = df2_filtered[f'Enrich {alt3_allele}']
        except IndexError:
            return None, None, None, None
        
        mean_ref = np.mean([enrich_ref_allele_1, enrich_ref_allele_2])
        mean_alt = np.mean([enrich_alt_allele_1, enrich_alt_allele_2])
        mean_alt2 = np.mean([enrich_alt2_allele_1, enrich_alt2_allele_2])
        mean_alt3 = np.mean([enrich_alt3_allele_1, enrich_alt3_allele_2])
        
        return ref_allele, alt_allele, alt2_allele, alt3_allele, mean_ref, mean_alt, mean_alt2, mean_alt3
    else:
        return None, None, None, None

def setup_logging():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def main(base_path, bound_vs_unbound_path, output_dir):
    setup_logging()
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        logging.info(f"Output directory {output_dir} created.")

    for folder in os.listdir(base_path):
        folder_path = os.path.join(base_path, folder)
        
        if os.path.isdir(folder_path):
            folder_parts = folder.split("_")
            concentration_value = f"{folder_parts[0]} {folder_parts[1]}"
            logging.info(f"Processing folder: {folder}, concentration: {concentration_value}")
            files = get_keys_from_concentration(concentration_value)

            if len(files) == 2:
                fileone, filetwo = files
                logging.info(f"File one: {fileone}, File two: {filetwo}")
                file1 = os.path.join(bound_vs_unbound_path, f'{fileone}.csv')
                file2 = os.path.join(bound_vs_unbound_path, f'{filetwo}.csv')
                
                decreased_rsids_path = os.path.join(folder_path, 'common_decreased_rsIDs.txt')
                increased_rsids_path = os.path.join(folder_path, 'common_increased_rsIDs.txt')
            
                if (not os.path.exists(decreased_rsids_path) or os.path.getsize(decreased_rsids_path) == 0) and \
                   (not os.path.exists(increased_rsids_path) or os.path.getsize(increased_rsids_path) == 0):
                    logging.warning(f"Both files: {decreased_rsids_path} and {increased_rsids_path} are empty or do not exist. Skipping folder: {folder}.")
                    continue
                
                decreased_data = []
                increased_data = []

                if os.path.exists(increased_rsids_path) and os.path.getsize(increased_rsids_path) > 0:
                    increased_rsids = pd.read_csv(increased_rsids_path, header=None)
                    for rsid in increased_rsids[0]:
                        ref_allele, alt_allele, alt2_allele, alt3_allele, mean_ref, mean_alt, mean_alt2, mean_alt3 = calculate_mean_enrichment(rsid, file1, file2)
                        increased_data.append([rsid, mean_ref, mean_alt, mean_alt2, mean_alt3])

                if os.path.exists(decreased_rsids_path) and os.path.getsize(decreased_rsids_path) > 0:
                    decreased_rsids = pd.read_csv(decreased_rsids_path, header=None)
                    for rsid in decreased_rsids[0]:
                        ref_allele, alt_allele, alt2_allele, alt3_allele, mean_ref, mean_alt, mean_alt2, mean_alt3 = calculate_mean_enrichment(rsid, file1, file2)
                        decreased_data.append([rsid, mean_ref, mean_alt, mean_alt2, mean_alt3])

                increased_df = pd.DataFrame(increased_data, columns=['rsID', 'Ref Allele', 'Alt Allele', 'Alt2', 'Alt3'])
                decreased_df = pd.DataFrame(decreased_data, columns=['rsID', 'Ref Allele', 'Alt Allele', 'Alt2', 'Alt3'])

                increased_df.set_index('rsID', inplace=True)
                decreased_df.set_index('rsID', inplace=True)
                
                increased_df.sort_values(by='Ref Allele', ascending=False, inplace=True)
                decreased_df.sort_values(by='Ref Allele', ascending=False, inplace=True)

                # Single plot if only one file exists, otherwise two subplots
                if increased_data and not decreased_data:
                    fig, ax = plt.subplots(figsize=(10, 6))
                    sns.heatmap(increased_df, annot=False, cmap='coolwarm', cbar=True, linewidths=0, ax=ax)
                    ax.set_title(f'Increased Alleles\nConcentration: {concentration_value}')
                    ax.set_xlabel('Alleles')
                    ax.set_ylabel('rsID')
                elif decreased_data and not increased_data:
                    fig, ax = plt.subplots(figsize=(10, 6))
                    sns.heatmap(decreased_df, annot=False, cmap='coolwarm', cbar=True, linewidths=0, ax=ax)
                    ax.set_title(f'Decreased Alleles\nConcentration: {concentration_value}')
                    ax.set_xlabel('Alleles')
                    ax.set_ylabel('rsID')
                else:
                    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
                    sns.heatmap(increased_df, annot=False, cmap='coolwarm', cbar=True, linewidths=0, ax=axes[0])
                    axes[0].set_title(f'Increased Alleles\nConcentration: {concentration_value}')
                    axes[0].set_xlabel('Alleles')
                    axes[0].set_ylabel('rsID')

                    sns.heatmap(decreased_df, annot=False, cmap='coolwarm', cbar=True, linewidths=0, ax=axes[1])
                    axes[1].set_title(f'Decreased Alleles\nConcentration: {concentration_value}')
                    axes[1].set_xlabel('Alleles')
                    axes[1].set_ylabel('rsID')

                plt.tight_layout()
                output_file = os.path.join(output_dir, f'{folder}_heatmap.png')
                plt.savefig(output_file)
                logging.info(f"Saved heatmap to {output_file}")
                plt.close()

if __name__ == "__main__":
    start_time = time.time()
    base_path = './output/TBX5/intersected_rsids_based_scatterPlot'
    bound_vs_unbound_path = './output/TBX5/bound_vs_unbound'
    output_dir = './output/TBX5/mean_heatmaps_from_scatter'
    main(base_path, bound_vs_unbound_path, output_dir)
    end_time = time.time()
    total_time = end_time - start_time
    print(f"Total time taken: {total_time:.2f} seconds")