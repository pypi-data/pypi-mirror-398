import os
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np
import logging
import time

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Author: [Shreya Sharma]
Date: [Dec 27, 2024]
Description:

	This Python script is designed to generate heatmaps of enrichment values for NKX25 binding data based on a series of input CSV files. The script processes the input files, computes the enrichment for different genomic patterns based on nucleotide counts (A/T/G/C), and generates a heatmap that visualizes the results for various experimental conditions (e.g., different concentrations of NKX25-bound and unbound states).

	This script is specifically tailored for the NKX25 transcription factor (TF) but can be adapted for other TFs by modifying the `desired_order` list to match the desired experimental conditions for other transcription factors. The user should provide the desired order of TF conditions in the `desired_order` parameter.

	Input: A directory containing CSV files with columns for `rsID`, `Pattern`, and nucleotide counts (A, T, G, C). The CSV files should include conditions in the format `[concentration]_Bound_[replicate].csv`.

	Output: A heatmap of enrichment values saved as a PNG file (`HeatMap_controls_NKX25.png`) for NKX25, or any transcription factor based on the `desired_order`.
"""

import os
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np
import logging
import time

class EnrichmentHeatmapGenerator:
    def __init__(self, data_dir, desired_order, output_dir='./output/NKX25/'):
        self.data_dir = data_dir
        self.desired_order = desired_order
        self.output_dir = output_dir
        self.files = [file for file in os.listdir(data_dir) if file.endswith('.csv')]
        self.final_df = pd.DataFrame()
        self.logger = self.setup_logger()

    def setup_logger(self):
        logger = logging.getLogger(__name__)
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)


class EnrichmentHeatmapGenerator:
    def __init__(self, data_dir, desired_order, output_dir='./output/NKX25/'):
        self.data_dir = data_dir
        self.desired_order = desired_order
        self.output_dir = output_dir
        self.files = [file for file in os.listdir(data_dir) if file.endswith('.csv')]
        self.final_df = pd.DataFrame()
        self.logger = self.setup_logger()

    def setup_logger(self):
        logger = logging.getLogger(__name__)
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)
        return logger

    def log_time(self, start_time):
        elapsed_time = time.time() - start_time
        self.logger.info(f"Execution Time: {elapsed_time:.2f} seconds")

    def get_enrich_base_and_value(self, row):
        counts = row[['A', 'T', 'G', 'C']]
        counts = pd.to_numeric(counts, errors='coerce').fillna(0).astype(int)
        max_base = counts.idxmax()
        enrich_value = row[f'Enrich {max_base}']
        return pd.Series([max_base, enrich_value])

    def replace_segment_with_max_base(self, row):
        pattern = row['Pattern']
        max_base = row['max_base']
        if len(pattern) > 19:
            pattern = pattern[:19] + max_base + pattern[25:]
        return pattern
       
    def process_file(self, file):
        file_path = os.path.join(self.data_dir, file)
        df = pd.read_csv(file_path)
        filtered_df = df[(df['rsID'].str.startswith('chr')) | (df['rsID'].str.startswith('hANF_control'))]
        filtered_df= filtered_df.copy()
        file_label = file.split('_Vs_')[0]
        
        filtered_df[['max_base', 'Enrich_Value']] = filtered_df.apply(self.get_enrich_base_and_value, axis=1)
        filtered_df['Pattern'] = filtered_df['Pattern'].str.replace('[ATGC]{2}', '')
        filtered_df['Pattern'] = filtered_df.apply(self.replace_segment_with_max_base, axis=1)

        result_df = filtered_df[['Pattern', 'Enrich_Value']].copy()
        result_df = result_df.rename(columns={'Enrich_Value': file_label})
        return result_df

    def merge_dataframes(self, result_df):
        if self.final_df.empty:
            self.final_df = result_df
        else:
            self.final_df = pd.merge(self.final_df, result_df, on='Pattern', how='outer')

    def generate_final_dataframe(self):
        self.final_df = self.final_df.fillna(0)
        mapping_dict = {}
        for col in self.final_df.columns:
            for name in self.desired_order:
                if col in name:
                    mapping_dict[col] = name

        self.final_df = self.final_df.rename(columns=mapping_dict)
        self.final_df = self.final_df[['Pattern'] + self.desired_order]
        self.final_df_sorted = self.final_df.sort_values(by='3000_nM_Bound_2 (R52_30)', ascending=False) #change this according to the TF

    def create_heatmap(self):
        df_for_clustering = self.final_df_sorted.set_index('Pattern')
        df_transformed = np.power(df_for_clustering, 0.5)
        plt.figure(figsize=(30, 24))
        ax = sns.heatmap(df_transformed, annot=False, cmap='coolwarm', fmt='.3f',
                    cbar_kws={'label': 'Enrichment Values'}, linewidths=0)
        ax.collections[0].colorbar.ax.set_ylabel('Enrichment Values', fontsize=18)
        ax.collections[0].colorbar.ax.tick_params(labelsize=18)
        plt.title('Heatmap of Enrichment Values for NKX25 Controls', pad=20, fontsize=18)
        plt.xlabel('Conditions')
        plt.ylabel('Patterns', fontsize=18)
        plt.xticks(fontsize=16, rotation=90, ha='right')
        plt.yticks(fontsize=8)
        plt.tight_layout()
        plt.savefig(os.path.join(self.output_dir, 'HeatMap_controls_NKX25.png'), dpi=360)

    def run(self):
        start_time = time.time()
        self.logger.info("Process Started")

        for file in self.files:
            self.logger.info(f"Processing file: {file}")
            result_df = self.process_file(file)
            self.merge_dataframes(result_df)

        self.generate_final_dataframe()
        self.create_heatmap()

        self.log_time(start_time)
        self.logger.info("Process Completed")


if __name__ == '__main__':
    start_time = time.time()
    data_dir = './output/NKX25/bound_vs_unbound/'
    desired_order = ['3000_nM_Bound_2 (R52_30)', '2000_nM_Bound_2 (R52_28)', '1500_nM_Bound_2 (R52_26)', '1000_nM_Bound_2 (R52_24)', '500_nM_Bound_2 (R52_22)', '100_nM_Bound_2 (R52_20)', '0_nM_Bound_2 (R52_18)', '0_nM_Bound (R52_01)', '100_nM_Bound (R52_03)', '500_nM_Bound (R52_05)', '1000_nM_Bound (R52_07)', '1500_nM_Bound (R52_09)', '2000_nM_Bound (R52_11)', '3000_nM_Bound (R52_13)']
    heatmap_generator = EnrichmentHeatmapGenerator(data_dir, desired_order)
    heatmap_generator.run()
    end_time = time.time()
    total_time = end_time - start_time
    print(f"Total time taken: {total_time:.2f} seconds")