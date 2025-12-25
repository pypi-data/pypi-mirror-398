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

                enrich_ref = row.get(f'Enrich {ref}', np.nan)
                enrich_alt = row.get(f'Enrich {alt}', np.nan)

                if rsID not in self.enrich_dict:
                    self.enrich_dict[rsID] = {}

                conc = self.concentration_map[csv_file]
                if conc not in self.enrich_dict[rsID]:
                    self.enrich_dict[rsID][conc] = {'Ref': [], 'Alt1': [], 'Alleles': []}

                self.enrich_dict[rsID][conc]['Ref'].append(enrich_ref)
                self.enrich_dict[rsID][conc]['Alt1'].append(enrich_alt)
                self.enrich_dict[rsID][conc]['Alleles'].append({'Ref': ref, 'Alt1': alt})

    def plot_enrichment(self):
        for rsID, concentrations in self.enrich_dict.items():
            logging.info(f"Plotting enrichment values for rsID: {rsID}")
            labels = list(self.concentration_map.values())[-7:]

            ref_means, alt_means = [], []
            ref_stds, alt_stds,= [], []
            allele_labels = []

            for conc in labels:
                ref_values = concentrations.get(conc, {'Ref': [np.nan], 'Alt1': [np.nan]})['Ref']
                alt_values = concentrations.get(conc, {'Ref': [np.nan], 'Alt1': [np.nan]})['Alt1']

                ref_means.append(np.nanmean(ref_values) if np.any(np.isfinite(ref_values)) else np.nan)
                ref_stds.append(np.nanstd(ref_values) if np.any(np.isfinite(ref_values)) else 0)

                alt_means.append(np.nanmean(alt_values) if np.any(np.isfinite(alt_values)) else np.nan)
                alt_stds.append(np.nanstd(alt_values) if np.any(np.isfinite(alt_values)) else 0)

                allele_labels.append(concentrations.get(conc, {'Alleles': [{'Ref': np.nan, 'Alt1': np.nan}]})['Alleles'][0])

            plt.figure(figsize=(12, 7))
            ref_allele = allele_labels[0]['Ref']
            alt1_allele = allele_labels[0]['Alt1']

            plt.errorbar(labels, ref_means, yerr=ref_stds, label=f"Ref Allele ({ref_allele})", fmt='--o', color='#254B96', capsize=5)
            plt.errorbar(labels, alt_means, yerr=alt_stds, label=f"Alt1 Allele ({alt1_allele})", fmt='--o', color='#BF212F', capsize=5)

            plt.title(f"Enrichment Values for rsID: {rsID}")
            plt.xlabel("Concentration")
            plt.ylabel("Enrichment Value")
            plt.xticks(rotation=45)
            plt.legend()
            #plt.grid(which='both', linestyle='--', linewidth=0.5, alpha=0.7)
            ax = plt.gca()
            ax.xaxis.set_minor_locator(ticker.AutoMinorLocator(2))
            ax.yaxis.set_minor_locator(ticker.AutoMinorLocator(2))
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
    folder_path = "./output/GATA4/bound_vs_unbound"
    output_folder = "./output/GATA4/rsID_plots_ref_alt_bound_unb"
    accepted_rsids_file = "./output/GATA4_accepted_rsIDs.csv"

    csv_files_order = [
        "R52_46_Vs_R52_47.csv", "R52_44_Vs_R52_45.csv", "R52_42_Vs_R52_43.csv",
        "R52_40_Vs_R52_41.csv", "R52_38_Vs_R52_39.csv", "R52_36_Vs_R52_37.csv",
        "R52_34_Vs_R52_35.csv", "R52_50_Vs_R52_51.csv", "R52_52_Vs_R52_53.csv",
        "R52_54_Vs_R52_55.csv", "R52_56_Vs_R52_57.csv", "R52_58_Vs_R52_59.csv",
        "R52_60_Vs_R52_61.csv", "R52_62_Vs_R52_63.csv"
    ]

    concentration_map = {
        "R52_46_Vs_R52_47.csv": "3000 nM",
        "R52_44_Vs_R52_45.csv": "2000 nM",
        "R52_42_Vs_R52_43.csv": "1500 nM",
        "R52_40_Vs_R52_41.csv": "1000 nM",
        "R52_38_Vs_R52_39.csv": "500 nM",
        "R52_36_Vs_R52_37.csv": "100 nM",
        "R52_34_Vs_R52_35.csv": "0 nM",
        "R52_50_Vs_R52_51.csv": "0 nM",
        "R52_52_Vs_R52_53.csv": "100 nM",
        "R52_54_Vs_R52_55.csv": "500 nM",
        "R52_56_Vs_R52_57.csv": "1000 nM",
        "R52_58_Vs_R52_59.csv": "1500 nM",
        "R52_60_Vs_R52_61.csv": "2000 nM",
        "R52_62_Vs_R52_63.csv": "3000 nM"
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
