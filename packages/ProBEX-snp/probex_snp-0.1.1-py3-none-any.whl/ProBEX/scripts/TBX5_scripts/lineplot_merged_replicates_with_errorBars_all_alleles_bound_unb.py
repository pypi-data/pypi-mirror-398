import os
import time
import logging
import pandas as pd
import re
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from matplotlib import MatplotlibDeprecationWarning
import warnings
import traceback

warnings.filterwarnings("ignore", category=MatplotlibDeprecationWarning)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler()
    ]
)

"""
Author: [Shreya Sharma]
Date: [Dec 22, 2024]

Description:
-------------
	This script defines the `EnrichmentPlotter` class, which processes SNP (rsID-based) enrichment data across various concentrations.
	It performs the following tasks:

	1. Loads a list of accepted rsIDs from a CSV file.
	2. Iterates through a predefined list of enrichment CSV files, each associated with a specific concentration.
	3. Filters and extracts enrichment values for the reference allele, the primary alternate allele (from the CSV), and two additional computed alternate alleles.
	4. Stores the enrichment data in a nested dictionary for later use.
	5. Generates error bar plots showing mean enrichment values and standard deviations across concentration levels for each rsID.
	6. Saves the plots as PNG files in the specified output folder.

"""

class EnrichmentPlotter:
    def __init__(self, folder_path, output_folder, csv_files_order, concentration_map, accepted_rsids_file):
        self.folder_path = folder_path
        self.output_folder = output_folder
        self.csv_files_order = csv_files_order
        self.concentration_map = concentration_map
        self.rsid_pattern = re.compile(r'^rs')
        self.enrich_dict = {}
        self.accepted_rsids = self._load_accepted_rsids(accepted_rsids_file)
        os.makedirs(output_folder, exist_ok=True)

    def _load_accepted_rsids(self, file_path):
        df = pd.read_csv(file_path)
        return set(df['rsID'].dropna().astype(str))

    @staticmethod
    def generate_alt_alleles(ref, alt):
        possible_alleles = ['A', 'T', 'G', 'C']
        if ref in possible_alleles:
            possible_alleles.remove(ref)
        if alt in possible_alleles:
            possible_alleles.remove(alt)

        return possible_alleles[:2] if len(possible_alleles) >= 2 else (possible_alleles[0], None)

    def process_files(self):
        for csv_file in self.csv_files_order:
            file_path = os.path.join(self.folder_path, csv_file)
            logging.info(f"Processing file: {file_path}")
            df = pd.read_csv(file_path)
            df_filtered = df[df['rsID'].apply(lambda x: isinstance(x, str) and self.rsid_pattern.match(x) is not None)]

            for _, row in df_filtered.iterrows():
                rsID = row['rsID']
                if rsID not in self.accepted_rsids:
                    continue

                ref = row['RefAllele']
                alt = row['AltAllele']
                alt1, alt2 = self.generate_alt_alleles(ref, alt)

                enrich_ref = row.get(f'Enrich {ref}', np.nan)
                enrich_alt = row.get(f'Enrich {alt}', np.nan)
                enrich_alt1 = row.get(f'Enrich {alt1}', np.nan) if alt1 else np.nan
                enrich_alt2 = row.get(f'Enrich {alt2}', np.nan) if alt2 else np.nan

                if rsID not in self.enrich_dict:
                    self.enrich_dict[rsID] = {}

                conc = self.concentration_map[csv_file]
                if conc not in self.enrich_dict[rsID]:
                    self.enrich_dict[rsID][conc] = {'Ref': [], 'Alt1': [], 'Alt2': [], 'Alt3': [], 'Alleles': []}

                self.enrich_dict[rsID][conc]['Ref'].append(enrich_ref)
                self.enrich_dict[rsID][conc]['Alt1'].append(enrich_alt)
                self.enrich_dict[rsID][conc]['Alt2'].append(enrich_alt1)
                self.enrich_dict[rsID][conc]['Alt3'].append(enrich_alt2)
                self.enrich_dict[rsID][conc]['Alleles'].append({'Ref': ref, 'Alt1': alt, 'Alt2': alt1, 'Alt3': alt2})

    def plot_enrichment(self):
        for rsID, concentrations in self.enrich_dict.items():
            logging.info(f"Plotting enrichment values for rsID: {rsID}")

            target_labels = ["0 nM", "100 nM", "500 nM", "1000 nM", "1500 nM", "2000 nM", "3000 nM"]
            x_vals = [int(label.replace(" nM", "")) for label in target_labels]

            ref_means, alt_means, alt1_means, alt2_means = [], [], [], []
            ref_stds, alt_stds, alt1_stds, alt2_stds = [], [], [], []
            allele_labels = []

            for conc in target_labels:
                ref_values = concentrations.get(conc, {'Ref': [np.nan], 'Alt1': [np.nan], 'Alt2': [np.nan], 'Alt3': [np.nan]})['Ref']
                alt_values = concentrations.get(conc, {'Ref': [np.nan], 'Alt1': [np.nan], 'Alt2': [np.nan], 'Alt3': [np.nan]})['Alt1']
                alt1_values = concentrations.get(conc, {'Ref': [np.nan], 'Alt1': [np.nan], 'Alt2': [np.nan], 'Alt3': [np.nan]})['Alt2']
                alt2_values = concentrations.get(conc, {'Ref': [np.nan], 'Alt1': [np.nan], 'Alt2': [np.nan], 'Alt3': [np.nan]})['Alt3']

                ref_means.append(np.nanmean(ref_values) if np.any(np.isfinite(ref_values)) else np.nan)
                ref_stds.append(np.nanstd(ref_values) if np.any(np.isfinite(ref_values)) else 0)

                alt_means.append(np.nanmean(alt_values) if np.any(np.isfinite(alt_values)) else np.nan)
                alt_stds.append(np.nanstd(alt_values) if np.any(np.isfinite(alt_values)) else 0)

                alt1_means.append(np.nanmean(alt1_values) if np.any(np.isfinite(alt1_values)) else np.nan)
                alt1_stds.append(np.nanstd(alt1_values) if np.any(np.isfinite(alt1_values)) else 0)

                alt2_means.append(np.nanmean(alt2_values) if np.any(np.isfinite(alt2_values)) else np.nan)
                alt2_stds.append(np.nanstd(alt2_values) if np.any(np.isfinite(alt2_values)) else 0)

                allele_labels.append(concentrations.get(conc, {'Alleles': [{'Ref': np.nan, 'Alt1': np.nan, 'Alt2': np.nan, 'Alt3': np.nan}]})['Alleles'][0])

            plt.figure(figsize=(12, 7))
            ref_allele = allele_labels[0]['Ref']
            alt1_allele = allele_labels[0]['Alt1']
            alt2_allele = allele_labels[0]['Alt2']
            alt3_allele = allele_labels[0]['Alt3']

            plt.errorbar(x_vals, ref_means, yerr=ref_stds, label=f"Ref Allele ({ref_allele})", fmt='--o', color='#254B96', capsize=5)
            plt.errorbar(x_vals, alt_means, yerr=alt_stds, label=f"Alt1 Allele ({alt1_allele})", fmt='--o', color='#BF212F', capsize=5)
            plt.errorbar(x_vals, alt1_means, yerr=alt1_stds, label=f"Alt2 Allele ({alt2_allele})", fmt='--o', color='#1D6F3D', capsize=5)
            plt.errorbar(x_vals, alt2_means, yerr=alt2_stds, label=f"Alt3 Allele ({alt3_allele})", fmt='--o', color='#800080', capsize=5)

            plt.title(f"Enrichment Values for rsID: {rsID}")
            plt.xlabel("Concentration")
            plt.ylabel("Enrichment Value")
            plt.xticks(ticks=x_vals, labels=target_labels, rotation=45)
            plt.legend()

            ax = plt.gca()
            ax.tick_params(which='both', direction='in', top=True, right=True)

            plt.tight_layout()
            output_path = os.path.join(self.output_folder, f"{rsID}_errorbars_with_alleles.png")
            plt.savefig(output_path, dpi=350)
            plt.close()


    def run(self):
        start_time = time.time()
        self.process_files()
        self.plot_enrichment()
        end_time = time.time()
        logging.info(f"Completed processing and plotting in {end_time - start_time:.2f} seconds")

if __name__ == "__main__":
    start_time = time.time()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    folder_path = "./output/TBX5/bound_vs_unbound"
    output_folder = "./output/TBX5/rsID_plots_bound_unb"
    accepted_rsids_file = "./output/TBX5_accepted_rsIDs.csv"

    csv_files_order = [
    "R52_78_Vs_R52_79.csv", "R52_76_Vs_R52_77.csv", "R52_74_Vs_R52_75.csv",
    "R52_72_Vs_R52_73.csv", "R52_70_Vs_R52_71.csv", "R52_68_Vs_R52_69.csv",
    "R52_66_Vs_R52_67.csv",    
    "R52_82_Vs_R52_83.csv",
    "R52_84_Vs_R52_85.csv", "R52_86_Vs_R52_87.csv", "R52_88_Vs_R52_89.csv",
    "R52_90_Vs_R52_91.csv", "R52_92_Vs_R52_93.csv", "R52_94_Vs_R52_95.csv"
     ]

    concentration_map = {
        "R52_78_Vs_R52_79.csv": "3000 nM",
        "R52_76_Vs_R52_77.csv": "2000 nM",
        "R52_74_Vs_R52_75.csv": "1500 nM",
        "R52_72_Vs_R52_73.csv": "1000 nM",
        "R52_70_Vs_R52_71.csv": "500 nM", 
        "R52_68_Vs_R52_69.csv": "100 nM",
        "R52_66_Vs_R52_67.csv": "0 nM",   
        "R52_82_Vs_R52_83.csv": "0 nM",
        "R52_84_Vs_R52_85.csv": "100 nM", 
        "R52_86_Vs_R52_87.csv": "500 nM", 
        "R52_88_Vs_R52_89.csv": "1000 nM",
        "R52_90_Vs_R52_91.csv": "1500 nM",
        "R52_92_Vs_R52_93.csv": "2000 nM", 
        "R52_94_Vs_R52_95.csv": "3000 nM"
    }

    logging.info("Initializing EnrichmentPlotter")
    try:
        plotter = EnrichmentPlotter(
            folder_path=folder_path,
            output_folder=output_folder,
            csv_files_order=csv_files_order,
            concentration_map=concentration_map,
            accepted_rsids_file=accepted_rsids_file
        )

        logging.info("Starting the enrichment plotting process")
        plotter.run()
        logging.info("All plots successfully generated")

    except Exception as e:
        logging.error(f"An error occurred during processing: {e}")
        logging.error("Traceback: %s", traceback.format_exc())
    end_time = time.time()
    total_time = end_time - start_time
    print(f"Total time taken: {total_time:.2f} seconds")
