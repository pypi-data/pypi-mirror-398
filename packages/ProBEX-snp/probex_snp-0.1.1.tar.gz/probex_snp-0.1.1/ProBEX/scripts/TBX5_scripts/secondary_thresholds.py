import pandas as pd
import logging
import time
import argparse

"""
Author: [Shreya Sharma]
Date: [2024-12-12]
Description: 
    This script is designed for processing and analyzing data related to sequence counts across different samples.
    It loads data from CSV and Excel files, performs normalization to per million values, calculates total sequence counts,
    and applies thresholds to generate new columns for analysis. The script is structured around the `DataProcessor` class
    that encapsulates methods for each step of the data processing pipeline, including loading data, performing calculations,
    and extracting relevant columns for further analysis.
    
    The processing pipeline involves the following steps:
    1. Loading data from CSV and Excel files into dictionaries.
    2. Calculating total sequence counts for each sample.
    3. Normalizing the data to per million values for each base (A, T, G, C) across various samples.
    4. Adding threshold columns based on per million values to indicate whether they exceed a given threshold (5 per million).
    5. Extracting and combining relevant columns from the datasets for downstream analysis.
    
    The script uses logging to report the progress and any issues during the execution of each step, and it employs 
    exception handling to manage errors gracefully.
    Last Modified: December 26, 2024
"""

class DataProcessor:
    def __init__(self):
        self.df_dict = {}
        self.total_counts = {}
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    def load_data(self):
        logging.info("Loading data...")
        try:
            self.df_dict = {
                'df_0nM_B_R1': pd.read_csv('./output/TBX5/CarriedForward/R52_66.csv'),
                'df_0nM_B_R2': pd.read_csv('./output/TBX5/CarriedForward/R52_82.csv'),
                'df_0nM_UnB_R1': pd.read_csv('./output/TBX5/CarriedForward/R52_67.csv'),
                'df_0nM_UnB_R2': pd.read_csv('./output/TBX5/CarriedForward/R52_83.csv'),
                'df_lib1': pd.read_csv('./output/TBX5/CarriedForward/R52_81.csv'),
                'df_lib2': pd.read_csv('./output/TBX5/CarriedForward/R52_96.csv'),
                'seq_count_df': pd.read_excel('./output/TBX5_row_counts_summary.xlsx')
            }
            logging.info("Data loaded successfully.")
        except Exception as e:
            logging.error(f"Error loading data: {e}")

    def get_total_counts(self):
        logging.info("Calculating total counts...")
        try:
            self.total_counts = {
                'R1': self.df_dict['seq_count_df'].loc[self.df_dict['seq_count_df']['Sample'].str.contains('R52_67'), 'Carried Sequences'].values[0],
                'R2': self.df_dict['seq_count_df'].loc[self.df_dict['seq_count_df']['Sample'].str.contains('R52_83'), 'Carried Sequences'].values[0],
                'Lib1': self.df_dict['seq_count_df'].loc[self.df_dict['seq_count_df']['Sample'].str.contains('R52_81'), 'Carried Sequences'].values[0],
                'Lib2': self.df_dict['seq_count_df'].loc[self.df_dict['seq_count_df']['Sample'].str.contains('R52_96'), 'Carried Sequences'].values[0],
                'B_R1': self.df_dict['seq_count_df'].loc[self.df_dict['seq_count_df']['Sample'].str.contains('R52_66'), 'Carried Sequences'].values[0],
                'B_R2': self.df_dict['seq_count_df'].loc[self.df_dict['seq_count_df']['Sample'].str.contains('R52_82'), 'Carried Sequences'].values[0]
            }
            logging.info("Total counts calculated.")
        except Exception as e:
            logging.error(f"Error calculating total counts: {e}")

    def calculate_per_million(self, df, total_count, suffix):
        logging.info(f"Calculating per million for {suffix}...")
        try:
            for base in ['A', 'T', 'G', 'C']:
                df[f'{base}_{suffix} (in M)'] = (df[base] / total_count) * 1e6
            return df
        except Exception as e:
            logging.error(f"Error calculating per million: {e}")
            return df

    def process_data(self):
        logging.info("Processing data...")
        start_time = time.time()
        try:
            self.df_dict['df_0nM_UnB_R1'] = self.calculate_per_million(self.df_dict['df_0nM_UnB_R1'], self.total_counts['R1'], '0nM_UnbR1')
            self.df_dict['df_0nM_UnB_R2'] = self.calculate_per_million(self.df_dict['df_0nM_UnB_R2'], self.total_counts['R2'], '0nM_UnbR2')
            self.df_dict['df_lib1'] = self.calculate_per_million(self.df_dict['df_lib1'], self.total_counts['Lib1'], 'Lib1')
            self.df_dict['df_lib2'] = self.calculate_per_million(self.df_dict['df_lib2'], self.total_counts['Lib2'], 'Lib2')
            self.df_dict['df_0nM_B_R1'] = self.calculate_per_million(self.df_dict['df_0nM_B_R1'], self.total_counts['B_R1'], '0nM_BR1')
            self.df_dict['df_0nM_B_R2'] = self.calculate_per_million(self.df_dict['df_0nM_B_R2'], self.total_counts['B_R2'], '0nM_BR2')

            logging.info(f"Data processed in {time.time() - start_time:.2f} seconds.")
        except Exception as e:
            logging.error(f"Error processing data: {e}")

    def add_threshold_columns(self, df, column_prefix):
        logging.info(f"Adding threshold columns for {column_prefix}...")
        try:
            for base in ['A', 'T', 'G', 'C']:
                df[f'Pass LessThan5/M ({base}: {column_prefix})'] = (df[f'{base} : {column_prefix} (in M)'] > 5).astype(int)
            return df
        except Exception as e:
            logging.error(f"Error adding threshold columns: {e}")
            return df

    def extract_columns_for_combined(self):
        logging.info("Extracting columns for combined dataset...")
        try:
            df_extracted = pd.DataFrame({
                'rsID': self.df_dict['df_0nM_UnB_R1']['rsID'],
                'A : Unbound 0nM R1 (in M)': self.df_dict['df_0nM_UnB_R1']['A_0nM_UnbR1 (in M)'],
                'T : Unbound 0nM R1 (in M)': self.df_dict['df_0nM_UnB_R1']['T_0nM_UnbR1 (in M)'],
                'G : Unbound 0nM R1 (in M)': self.df_dict['df_0nM_UnB_R1']['G_0nM_UnbR1 (in M)'],
                'C : Unbound 0nM R1 (in M)': self.df_dict['df_0nM_UnB_R1']['C_0nM_UnbR1 (in M)'],
                'A : Unbound 0nM R2 (in M)': self.df_dict['df_0nM_UnB_R2']['A_0nM_UnbR2 (in M)'],
                'T : Unbound 0nM R2 (in M)': self.df_dict['df_0nM_UnB_R2']['T_0nM_UnbR2 (in M)'],
                'G : Unbound 0nM R2 (in M)': self.df_dict['df_0nM_UnB_R2']['G_0nM_UnbR2 (in M)'],
                'C : Unbound 0nM R2 (in M)': self.df_dict['df_0nM_UnB_R2']['C_0nM_UnbR2 (in M)'],
                'A : Lib1 (in M)': self.df_dict['df_lib1']['A_Lib1 (in M)'],
                'T : Lib1 (in M)': self.df_dict['df_lib1']['T_Lib1 (in M)'],
                'G : Lib1 (in M)': self.df_dict['df_lib1']['G_Lib1 (in M)'],
                'C : Lib1 (in M)': self.df_dict['df_lib1']['C_Lib1 (in M)'],
                'A : Lib2 (in M)': self.df_dict['df_lib2']['A_Lib2 (in M)'],
                'T : Lib2 (in M)': self.df_dict['df_lib2']['T_Lib2 (in M)'],
                'G : Lib2 (in M)': self.df_dict['df_lib2']['G_Lib2 (in M)'],
                'C : Lib2 (in M)': self.df_dict['df_lib2']['C_Lib2 (in M)'],
                'A : Bound 0nM R1 (in M)': self.df_dict['df_0nM_B_R1']['A_0nM_BR1 (in M)'],
                'T : Bound 0nM R1 (in M)': self.df_dict['df_0nM_B_R1']['T_0nM_BR1 (in M)'],
                'G : Bound 0nM R1 (in M)': self.df_dict['df_0nM_B_R1']['G_0nM_BR1 (in M)'],
                'C : Bound 0nM R1 (in M)': self.df_dict['df_0nM_B_R1']['C_0nM_BR1 (in M)'],
                'A : Bound 0nM R2 (in M)': self.df_dict['df_0nM_B_R2']['A_0nM_BR2 (in M)'],
                'T : Bound 0nM R2 (in M)': self.df_dict['df_0nM_B_R2']['T_0nM_BR2 (in M)'],
                'G : Bound 0nM R2 (in M)': self.df_dict['df_0nM_B_R2']['G_0nM_BR2 (in M)'],
                'C : Bound 0nM R2 (in M)': self.df_dict['df_0nM_B_R2']['C_0nM_BR2 (in M)']
            })
            logging.info("Columns extracted for combined dataset.")
            return df_extracted
        except Exception as e:
            logging.error(f"Error extracting columns: {e}")
            return pd.DataFrame()

    def add_unbound_and_library_columns(self, df):        
        def calculate_unbound(row):
            threshold_columns = [
                'Pass LessThan5/M (A: Unbound 0nM R1)', 'Pass LessThan5/M (T: Unbound 0nM R1)', 'Pass LessThan5/M (G: Unbound 0nM R1)', 'Pass LessThan5/M (C: Unbound 0nM R1)',
                'Pass LessThan5/M (A: Unbound 0nM R2)', 'Pass LessThan5/M (T: Unbound 0nM R2)', 'Pass LessThan5/M (G: Unbound 0nM R2)', 'Pass LessThan5/M (C: Unbound 0nM R1)'
            ]
            if row['rsID'].startswith('rs'):
                if row[threshold_columns].all():
                    return 1
                else:
                    return 0
            elif row['rsID'].startswith('chr') or row['rsID'].startswith('hANF'):
                for base in ['A', 'T', 'G', 'C']:
                    if (row[f'Pass LessThan5/M ({base}: Unbound 0nM R1)'] == 1 and row[f'Pass LessThan5/M ({base}: Unbound 0nM R1)'] == 1 and
                        all(row[f'Pass LessThan5/M ({other_base}: Unbound 0nM R1)'] == 0 and row[f'Pass LessThan5/M ({other_base}: Unbound 0nM R2)'] == 0
                            for other_base in ['A', 'T', 'G', 'C'] if other_base != base)):
                        return 1
                return 0
            else:
                return 0

        def calculate_bound(row):
            threshold_columns = [
                'Pass LessThan5/M (A: Bound 0nM R1)', 'Pass LessThan5/M (T: Bound 0nM R1)', 'Pass LessThan5/M (G: Bound 0nM R1)', 'Pass LessThan5/M (C: Bound 0nM R1)',
                'Pass LessThan5/M (A: Bound 0nM R2)', 'Pass LessThan5/M (T: Bound 0nM R2)', 'Pass LessThan5/M (G: Bound 0nM R2)', 'Pass LessThan5/M (C: Bound 0nM R2)'
            ]
            if row['rsID'].startswith('rs'):
                if row[threshold_columns].all():
                    return 1
                else:
                    return 0
            elif row['rsID'].startswith('chr') or row['rsID'].startswith('hANF'):
                for base in ['A', 'T', 'G', 'C']:
                    if (row[f'Pass LessThan5/M ({base}: Bound 0nM R1)'] == 1 and row[f'Pass LessThan5/M ({base}: Bound 0nM R2)'] == 1 and
                        all(row[f'Pass LessThan5/M ({base}: Bound 0nM R2)'] == 0 and row[f'Pass LessThan5/M ({base}: Bound 0nM R2)'] == 0
                            for other_base in ['A', 'T', 'G', 'C'] if other_base != base)):
                        return 1
                return 0
            else:
                return 0

        def calculate_library(row):
            threshold_columns = [
                'Pass LessThan5/M (A: Lib1)', 'Pass LessThan5/M (T: Lib1)', 'Pass LessThan5/M (G: Lib1)', 'Pass LessThan5/M (C: Lib1)',
                'Pass LessThan5/M (A: Lib2)', 'Pass LessThan5/M (T: Lib2)', 'Pass LessThan5/M (G: Lib2)', 'Pass LessThan5/M (C: Lib2)'
            ]

            if row['rsID'].startswith('rs'):
                if row[threshold_columns].all():
                    return 1
                else:
                    return 0
            elif row['rsID'].startswith('chr') or row['rsID'].startswith('hANF'):
                for base in ['A', 'T', 'G', 'C']:
                    lib1_condition = (row[f'Pass LessThan5/M ({base}: Lib1)'] == 1 and
                                      all(row[f'Pass LessThan5/M ({other_base}: Lib1)'] == 0 for other_base in ['A', 'T', 'G', 'C'] if other_base != base))

                    lib2_condition = (row[f'Pass LessThan5/M ({base}: Lib2)'] == 1 and
                                      all(row[f'Pass LessThan5/M ({other_base}: Lib2)'] == 0 for other_base in ['A', 'T', 'G', 'C'] if other_base != base))

                    if lib1_condition or lib2_condition:
                        return 1
                return 0
            else:
                return 0

        df['LT5/M Threshold \nin Unbound (0nM)\nin R1 & R2 both'] = df.apply(calculate_unbound, axis=1)
        df['LT5/M Threshold \nLibrary Status'] = df.apply(calculate_library, axis=1)
        df['LT5/M Threshold \nin Bound (0nM)\nin R1 & R2 both'] = df.apply(calculate_bound, axis=1)

        return df

    def calculate_ratios_and_labels(self, df_extracted):
        for base in ['A', 'T', 'G', 'C']:
            # Ratios for R1
            df_extracted[f'Ratio\n{base}:Unb(0nM)R1_vs_Lib1'] = (
                df_extracted[f'{base} : Unbound 0nM R1 (in M)'] / df_extracted[f'{base} : Lib1 (in M)']
            ).replace([float('inf'), -float('inf')], float('nan'))
            df_extracted[f'Label\n{base}:Unb(0nM)R1_vs_Lib1'] = df_extracted[f'Ratio\n{base}:Unb(0nM)R1_vs_Lib1'].apply(
                lambda x: 0 if x <= 0.2 or x >= 2 else 1
            )

            df_extracted[f'Ratio\n{base}:B_vs_Unb R1'] = (
                df_extracted[f'{base} : Bound 0nM R1 (in M)'] / df_extracted[f'{base} : Unbound 0nM R1 (in M)']
            ).replace([float('inf'), -float('inf')], float('nan'))
            df_extracted[f'Label\n{base}:B_vs_Unb R1'] = df_extracted[f'Ratio\n{base}:B_vs_Unb R1'].apply(
                lambda x: 0 if x <= 0.2 or x >= 5 else 1
            )

            # Ratios for R2
            df_extracted[f'Ratio\n{base}:Unb(0nM)R2_vs_Lib2'] = (
                df_extracted[f'{base} : Unbound 0nM R2 (in M)'] / df_extracted[f'{base} : Lib2 (in M)']
            ).replace([float('inf'), -float('inf')], float('nan'))
            df_extracted[f'Label\n{base}:Unb(0nM)R2_vs_Lib2'] = df_extracted[f'Ratio\n{base}:Unb(0nM)R2_vs_Lib2'].apply(
                lambda x: 0 if x <= 0.2 or x >= 2 else 1
            )

            df_extracted[f'Ratio\n{base}:B_vs_Unb R2'] = (
                df_extracted[f'{base} : Bound 0nM R2 (in M)'] / df_extracted[f'{base} : Unbound 0nM R2 (in M)']
            ).replace([float('inf'), -float('inf')], float('nan'))
            df_extracted[f'Label\n{base}:B_vs_Unb R2'] = df_extracted[f'Ratio\n{base}:B_vs_Unb R2'].apply(
                lambda x: 0 if x <= 0.2 or x >= 5 else 1
            )

        return df_extracted

    def calculate_ratio_unb_lib(self, row):
        if row['rsID'].startswith('rs'):
            if all(row[f'Label\n{base}:Unb(0nM)R1_vs_Lib1'] == 1 and row[f'Label\n{base}:Unb(0nM)R2_vs_Lib2'] == 1 for base in ['A', 'T', 'G', 'C']):
                return 1
            else:
                return 0
        elif row['rsID'].startswith('chr') or row['rsID'].startswith('hANF'):
            bases = ['A', 'T', 'G', 'C']
            matching_base = [base for base in bases if row[f'Label\n{base}:Unb(0nM)R1_vs_Lib1'] == 1 and row[f'Label\n{base}:Unb(0nM)R2_vs_Lib2'] == 1]
            if len(matching_base) == 1:
                if all(row[f'Label\n{other_base}:Unb(0nM)R1_vs_Lib1'] in [0, None] and row[f'Label\n{other_base}:Unb(0nM)R2_vs_Lib2'] in [0, None]
                       for other_base in bases if other_base != matching_base[0]):
                    return 1
            return 0
        else:
            return 0

    def calculate_ratio_b_unb(self, row):
        if row['rsID'].startswith('rs'):
            if all(row[f'Label\n{base}:B_vs_Unb R1'] == 1 and row[f'Label\n{base}:B_vs_Unb R2'] == 1 for base in ['A', 'T', 'G', 'C']):
                return 1
            else:
                return 0
        elif row['rsID'].startswith('chr') or row['rsID'].startswith('hANF'):
            bases = ['A', 'T', 'G', 'C']
            matching_base = [base for base in bases if row[f'Label\n{base}:B_vs_Unb R1'] == 1 and row[f'Label\n{base}:B_vs_Unb R2'] == 1]
            if len(matching_base) == 1:
                if all(row[f'Label\n{other_base}:B_vs_Unb R1'] in [0, None] and row[f'Label\n{other_base}:B_vs_Unb R2'] in [0, None]
                       for other_base in bases if other_base != matching_base[0]):
                    return 1
            return 0
        else:
            return 0   

    def save_to_excel(self, df_extracted, excel_file):
        try:
            df_extracted.to_excel(excel_file, index=False)
            logging.info(f"Data saved successfully to {excel_file}")
        except Exception as e:
            logging.error(f"Error saving to Excel: {e}")

def main():
    """Main function to execute the entire data processing pipeline."""
    start_time = time.time()
    parser = argparse.ArgumentParser(description="Process an Excel file for data analysis.")
    parser.add_argument('--excel_file', default='./output/TBX5/rsID_filtering.xlsx', help="Path to the input Excel file (default: 'rsID_filtering.xlsx')")
    args = parser.parse_args()
 
    try:
        data_processor = DataProcessor()
        data_processor.load_data()
    except Exception as e:
        logging.error(f"Exiting due to error: {str(e)}")
        return
 
    total_counts = data_processor.get_total_counts()
    data_processor.process_data()  
    df_dict = data_processor.df_dict
    df_extracted = data_processor.extract_columns_for_combined()
    
    for column_prefix in ['Unbound 0nM R1', 'Unbound 0nM R2', 'Lib1', 'Lib2', 'Bound 0nM R1', 'Bound 0nM R2']:
        df_extracted = data_processor.add_threshold_columns(df_extracted, column_prefix)

    df_extracted = data_processor.add_unbound_and_library_columns(df_extracted)
    df_extracted = data_processor.calculate_ratios_and_labels(df_extracted)
    df_extracted['Threshold (<=0.2 or >=2)\nUnb/Lib'] = df_extracted.apply(data_processor.calculate_ratio_unb_lib, axis=1)
    df_extracted['Threshold (<=0.2 or >=5) b/Unb'] = df_extracted.apply(data_processor.calculate_ratio_b_unb, axis=1)

    data_processor.save_to_excel(df_extracted, args.excel_file)
    end_time = time.time()
    total_time = end_time - start_time
    print(f"Total time taken: {total_time:.2f} seconds")

if __name__ == "__main__":
    main()
