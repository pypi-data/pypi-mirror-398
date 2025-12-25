import os
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import time

"""
Author: Shreya Sharma
Date: 2024-12-27
Description:
    This script processes CSV files containing enrichment data for different bound vs unbound conditions
    across various transcription factor (TF) samples. It performs the following steps:
    1. Data Loading
    2. Data Filtering
    3. Enrichment Data Aggregation
    4. Correlation Calculation
    5. Heatmap Visualization
    6. Scatter Plot of 3000 nM replicate samples
"""

class DataProcessor:
    def __init__(self, data_dir, accepted_rsids_file, desired_order, output_csv='/home/dell/Desktop/snpoiss_bind_n_seq/output/GATA4_enrich_data.csv'):
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
        plt.savefig("/home/dell/Desktop/snpoiss_bind_n_seq/output/GATA4/corr_heatmap_rep1_2_with_accepted_rsIDs.png")
        # plt.show()

    def plot_scatter_3000nM(self):
        import scipy.stats as stats

        self.log_time("Plotting scatter plot for 3000 nM (R1 vs R2)")
        col_r1 = '3000_nM_Bound (R52_46)'
        col_r2 = '3000_nM_Bound_2 (R52_62)'
        
        if col_r1 in self.ext_df.columns and col_r2 in self.ext_df.columns:
            x = self.ext_df[col_r1].astype(float)
            y = self.ext_df[col_r2].astype(float)

            # Drop NaNs
            valid = x.notna() & y.notna()
            x = x[valid]
            y = y[valid]

            # Pearson correlation
            r, p_value = stats.pearsonr(x, y)

            # Scatter + regression line
            plt.figure(figsize=(8, 6))
            sns.regplot(
                x=x,
                y=y,
                scatter_kws={'color': '#BF212F', 'edgecolor': 'black', 's': 60},
                line_kws={"lw": 2, "alpha": 0.8, "color": "black"}
            )

            # Annotate with r and p-value
            plt.text(
                0.05, 0.95,
                f'Pearson r = {r:.3f}\np = {p_value:.2e}',
                transform=plt.gca().transAxes,
                fontsize=14,
                weight='bold',
                verticalalignment='top',
                bbox=dict(boxstyle="round", facecolor='white', alpha=0.6)
            )

            plt.xlabel('3000 nM Bound (R52_46) - Replicate 1', fontsize=12)
            plt.ylabel('3000 nM Bound_2 (R52_62) - Replicate 2', fontsize=12)
            plt.title('Scatter Plot of 3000 nM Enrichment Values (R1 vs R2)', fontsize=14, weight='bold')
            plt.grid(True)
            plt.tight_layout()
            plt.savefig("/home/dell/Desktop/snpoiss_bind_n_seq/output/GATA4/scatter_3000nM_R1_vs_R2.png")
            # plt.show()

            self.log_time(f"Pearson correlation (r): {r:.3f}, p-value: {p_value:.2e}")
        
        else:
            print("3000 nM replicate columns not found in the DataFrame.")

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
        self.plot_scatter_3000nM()
        self.log_time("Data processing complete")


if __name__ == "__main__":
    start_time = time.time()
    data_dir = '/home/dell/Desktop/snpoiss_bind_n_seq/output/GATA4/bound_vs_unbound/'
    accepted_rsids_file = '/home/dell/Desktop/snpoiss_bind_n_seq/output/GATA4_accepted_rsIDs.csv'
    desired_order = [
        '3000_nM_Bound (R52_46)', '2000_nM_Bound (R52_44)', '1500_nM_Bound (R52_42)', 
        '1000_nM_Bound (R52_40)', '500_nM_Bound (R52_38)', '100_nM_Bound (R52_36)', '0_nM_Bound (R52_34)',
        '0_nM_Bound_2 (R52_50)', '100_nM_Bound_2 (R52_52)', '500_nM_Bound_2 (R52_54)', '1000_nM_Bound_2 (R52_56)',
        '1500_nM_Bound_2 (R52_58)', '2000_nM_Bound_2 (R52_60)', '3000_nM_Bound_2 (R52_62)'
    ]

    processor = DataProcessor(data_dir, accepted_rsids_file, desired_order)
    processor.process()
    end_time = time.time()
    total_time = end_time - start_time
    print(f"Total time taken: {total_time:.2f} seconds")
