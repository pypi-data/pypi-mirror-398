import os
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import time

"""
Author: [Shreya Sharma]
Date: [2024-12-27]
Description:
	This script processes CSV files containing enrichment data for different bound vs unbound conditions
	across various transcription factor (TF) samples. It performs the following steps:
	1. Data Loading: Loads the accepted rsIDs from a CSV file (`NKX25_accepted_rsIDs.csv`). Loads and filters the enrichment data from multiple CSV files within a specified directory.

	2. Data Filtering: Filters the data to only include rows where the `rsID` is present in the accepted rsIDs list, and the `rsID` does not start with 'chr' or 'hANF_control'. Identifies common patterns across all files for use in downstream analysis.

	3. Enrichment Data Aggregation: Builds an aggregated DataFrame that contains enrichment values for each common pattern and each file (representing different bound/unbound conditions). For each pattern, it extracts enrichment values for the four nucleotides (A, T, G, C) and populates them accordingly.

	4. Correlation Calculation: Computes the Pearson correlation matrix for enrichment values across different conditions (both replicate 1 and replicate 2 samples). The correlation is calculated based on the enrichment values for each pattern, which are stored in the aggregated DataFrame.

	5. Heatmap Visualization: The heatmap is used to visualize the relationships between different bound/unbound conditions based on their enrichment patterns.

"""
class DataProcessor:
    def __init__(self, data_dir, accepted_rsids_file, desired_order, output_csv='./output/NKX25_original_control.csv'):
        self.data_dir = data_dir
        self.accepted_rsids_file = accepted_rsids_file
        self.desired_order = desired_order
        self.output_csv = output_csv
        self.files = [file for file in os.listdir(data_dir) if file.endswith('.csv')]
        self.accepted_rsids = pd.read_csv(accepted_rsids_file)['rsID'].tolist()
        self.common_patterns = set()
        self.dfs = []
    
    def log_time(self, message):
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {message}")
    
    def filter_data(self, df, file_name):
        #if you want to also include controls then you can avoid the conditioin where the rsID cannot start with the "chr" and "hANF_control"
        self.log_time(f"Filtering data for file {file_name}")
        filtered_df = df[df['rsID'].isin(self.accepted_rsids) & 
                         ~(df['rsID'].str.startswith('chr') | df['rsID'].str.startswith('hANF_control'))] 
                         
        self.common_patterns.update(filtered_df['Pattern'].unique())
        self.dfs.append(filtered_df)

    def build_enrichment_df(self):
        self.log_time("Building the enrichment dataframe")
        common_patterns_list = list(self.common_patterns) * 4
        ext_df = pd.DataFrame({'Pattern': common_patterns_list})
        for file in self.files:
            file_name = os.path.basename(file).split('_Vs_')[0]
            for name in self.desired_order:
                col_name = name.split(' (')[1][:-1]
                if file_name == col_name:
                    ext_df[file_name] = None
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
        for name in self.desired_order:
            col_name = name.split(' (')[1][:-1]
            if col_name in ext_df.columns:
                ext_df.rename(columns={col_name: name}, inplace=True)
        
        self.ext_df = ext_df
    
    def save_enrichment_df(self):
        self.log_time(f"Saving the enrichment dataframe to {self.output_csv}")
        self.ext_df.to_csv(self.output_csv, index=False)
    
    def calculate_correlation(self):
        self.log_time("Calculating correlation matrix")
        columns_to_correlate = [col for col in self.ext_df.columns if col != 'Pattern']
        subset_df = self.ext_df[columns_to_correlate]
        subset_df = subset_df.reindex(columns=self.desired_order)
        corr_matrix = subset_df.corr()
        return corr_matrix

    def plot_heatmap(self, corr_matrix):
        self.log_time("Plotting correlation heatmap")
        plt.figure(figsize=(10, 8))
        sns.heatmap(corr_matrix, annot=False, cmap='coolwarm', fmt='.2f', vmin=-1, vmax=1)
        plt.title('Pearson correlation between bound replicate 1 and replicate 2 samples,\nwhen enrichment calculated against Unbound')
        plt.xticks(rotation=90)
        plt.yticks(rotation=0)
        plt.tight_layout()
        plt.savefig("./output/NKX25/corr_heatmap_rep1_2_with_accepted_rsIDs.png")
        #plt.show()

    def process(self):
        self.log_time("Starting data processing")
        for file in self.files:
            file_name = os.path.basename(file).split('_Vs_')[0]
            file_path = os.path.join(self.data_dir, file)
            df = pd.read_csv(file_path)
            self.filter_data(df, file_name)
        
        self.build_enrichment_df()
        self.save_enrichment_df()
        corr_matrix = self.calculate_correlation()
        self.plot_heatmap(corr_matrix)
        self.log_time("Data processing complete")

if __name__ == "__main__":
    start_time = time.time()
    data_dir = './output/NKX25/bound_vs_unbound/'
    accepted_rsids_file = './output/NKX25_accepted_rsIDs.csv'
    desired_order = ['3000_nM_Bound (R52_13)', '2000_nM_Bound (R52_11)', '1500_nM_Bound (R52_09)', '1000_nM_Bound (R52_07)', 
                 '500_nM_Bound (R52_05)', '100_nM_Bound (R52_03)', '0_nM_Bound (R52_01)',
                 '0_nM_Bound_2 (R52_18)', '100_nM_Bound_2 (R52_20)', '500_nM_Bound_2 (R52_22)', '1000_nM_Bound_2 (R52_24)',
                 '1500_nM_Bound_2 (R52_26)', '2000_nM_Bound_2 (R52_28)', '3000_nM_Bound_2 (R52_30)']
    processor = DataProcessor(data_dir, accepted_rsids_file, desired_order)
    processor.process()
    end_time = time.time()
    total_time = end_time - start_time
    print(f"Total time taken: {total_time:.2f} seconds")
