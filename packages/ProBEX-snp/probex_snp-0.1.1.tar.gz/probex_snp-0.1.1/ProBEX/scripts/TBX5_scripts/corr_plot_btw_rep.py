import os
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import time

"""
Author: [Shreya Sharma]
Date: 2024-12-27
Description:
    This Python script processes CSV files containing enrichment data for different conditions (e.g., bound and unbound states).
    The script performs the following key operations:
    
    1. Reads and filters data from CSV files located in the specified directory.
    2. Extracts common genetic patterns from the data and creates a unified DataFrame.
    3. Populates the DataFrame with enrichment values for the common genetic patterns across all files.
    4. Renames columns based on a predefined order and saves the enriched data to a CSV file.
    5. Computes the Pearson correlation matrix for the enrichment values and visualizes it using a heatmap.
    6. Saves the heatmap to a file (`corr_heatmap_rep1_2.png`) and displays it.

    The code is organized into a class-based abstraction (`DataProcessor`), which encapsulates all functionality, 
    making it easier to maintain, reuse, and extend. A decorator is used to log the time taken for each major step 
    in the processing pipeline.
"""

class DataProcessor:
    def __init__(self, data_dir, desired_order, output_filename='./output/TBX5_original_control.csv'):
        self.data_dir = data_dir
        self.desired_order = desired_order
        self.output_filename = output_filename
        self.files = [file for file in os.listdir(data_dir) if file.endswith('.csv')]
        self.common_patterns = set()
        self.dfs = []

    def log_time(func):
        def wrapper(self, *args, **kwargs):
            start_time = time.time()
            result = func(self, *args, **kwargs)
            end_time = time.time()
            print(f"Time taken for {func.__name__}: {end_time - start_time:.4f} seconds")
            return result
        return wrapper

    @log_time
    def read_and_filter_data(self):
        for file in self.files:
            file_name = os.path.basename(file).split('_Vs_')[0]
            for name in self.desired_order:
                col_name = name.split(' (')[1][:-1]
                if file_name == col_name:
                    file_path = os.path.join(self.data_dir, file)
                    df = pd.read_csv(file_path)
                    filtered_df = df[~(df['rsID'].str.startswith('chr') | df['rsID'].str.startswith('hANF_control'))]
                    self.common_patterns.update(filtered_df['Pattern'].unique())
                    self.dfs.append(filtered_df)

    @log_time
    def create_common_patterns_dataframe(self):
        common_patterns_list = list(self.common_patterns) * 4
        ext_df = pd.DataFrame({'Pattern': common_patterns_list})
        for file in self.files:
            file_name = os.path.basename(file).split('_Vs_')[0]
            for name in self.desired_order:
                col_name = name.split(' (')[1][:-1]
                if file_name == col_name:
                    ext_df[file_name] = None
        return ext_df

    @log_time
    def populate_enrichment_values(self, ext_df):
        for file, df in zip(self.files, self.dfs):
            file_name = os.path.basename(file).split('_Vs_')[0]
            for pattern in self.common_patterns:
                pattern_row = df[df['Pattern'] == pattern]
                if not pattern_row.empty:
                    enrich_values = pattern_row[['Enrich A', 'Enrich T', 'Enrich G', 'Enrich C']].values.flatten()
                    ext_df_rows = ext_df[ext_df['Pattern'] == pattern]
                    if len(ext_df_rows) == 4:
                        for i, (index, row) in enumerate(ext_df_rows.iterrows()):
                            if i < len(enrich_values):
                                ext_df.at[index, file_name] = enrich_values[i]

    @log_time
    def rename_columns(self, ext_df):
        for name in self.desired_order:
            col_name = name.split(' (')[1][:-1]
            if col_name in ext_df.columns:
                ext_df.rename(columns={col_name: name}, inplace=True)

    @log_time
    def calculate_and_plot_correlation(self, ext_df):
        columns_to_correlate = [col for col in ext_df.columns if col != 'Pattern']
        subset_df = ext_df[columns_to_correlate]
        subset_df = subset_df.reindex(columns=self.desired_order)
        corr_matrix = subset_df.corr()
        plt.figure(figsize=(10, 8))
        sns.heatmap(corr_matrix, annot=False, cmap='coolwarm', fmt='.2f', vmin=-1, vmax=1)
        plt.title('Pearson correlation between bound replicate 1 and replicate 2 samples,\nwhen enrichment calculated against Unbound')
        plt.xticks(rotation=90)
        plt.yticks(rotation=0)
        plt.tight_layout()
        plt.savefig('./output/TBX5/corr_heatmap_rep1_2.png')
        #plt.show()

    @log_time
    def process_data(self):
        self.read_and_filter_data()
        ext_df = self.create_common_patterns_dataframe()
        self.populate_enrichment_values(ext_df)
        self.rename_columns(ext_df)
        ext_df.to_csv(self.output_filename, index=False)
        self.calculate_and_plot_correlation(ext_df)

if __name__ == "__main__":
    start_time = time.time() 
    desired_order = ['3000_nM_Bound (R52_78)', '2000_nM_Bound (R52_76)', '1500_nM_Bound (R52_74)', '1000_nM_Bound (R52_72)', 
                 '500_nM_Bound (R52_70)', '100_nM_Bound (R52_68)', '0_nM_Bound (R52_66)',
                 '0_nM_Bound_2 (R52_82)', '100_nM_Bound_2 (R52_84)', '500_nM_Bound_2 (R52_86)', '1000_nM_Bound_2 (R52_88)',
                 '1500_nM_Bound_2 (R52_90)', '2000_nM_Bound_2 (R52_92)', '3000_nM_Bound_2 (R52_94)']
    data_dir = './output/TBX5/bound_vs_unbound/'
    processor = DataProcessor(data_dir, desired_order)
    processor.process_data()
    end_time = time.time()
    total_time = end_time - start_time
    print(f"Total time taken: {total_time:.2f} seconds")
