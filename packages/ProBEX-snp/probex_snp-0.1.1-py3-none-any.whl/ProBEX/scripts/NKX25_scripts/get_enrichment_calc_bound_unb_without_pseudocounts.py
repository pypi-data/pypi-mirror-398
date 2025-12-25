import os
import pandas as pd
import time, logging
import argparse
from matplotlib.backend_bases import CloseEvent

"""
Author: [Shreya Sharma]
Date: [2024-12-27]
Description: This script processes enrichment and normalized enrichment for a set of files. 
	It reads data from specified CSV files, computes enrichment values for bases A, T, G, and C, 
	and normalizes those enrichment values. The calculations are performed for multiple files within 
	a given range and unbound, and the results are saved to new CSV files.

	- No need to manually specify file paths in the script; only the unbound number and file range 
	  need to be provided via command-line arguments.
	- This script is intended to handle the normalization of multiple files against one specified file 
	  (unbound file), though this may not be strictly necessary in all cases.
	- The user must ensure that the specified range of files is valid for their dataset.

	Note: The script uses logging to track the process and errors, and allows flexibility in input via 
	      command-line arguments.
"""
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def parse_ranges(range_list):
    all_bounds = []
    for r in range_list:
        start, end = map(int, r.split('-'))
        all_bounds.extend(range(start, end + 1, 2))
    return all_bounds

def process_files(df_excel, bound_range, output_folder):
    for bound_file_number in bound_range:
        unbound_file_number = bound_file_number + 1  
        bound_file_path = f'./output/NKX25/CarriedForward/R52_{bound_file_number:02}.csv'
        unbound_file_path = f'./output/NKX25/CarriedForward/R52_{unbound_file_number:02}.csv'

        if os.path.exists(bound_file_path) and os.path.exists(unbound_file_path):
            bound_df = pd.read_csv(bound_file_path)
            unbound_df = pd.read_csv(unbound_file_path)
            logger.info(f"Processing: R52_{bound_file_number:02} vs R52_{unbound_file_number:02}")
            df_excel['Sample'] = df_excel['Sample'].str.replace('.csv', '', regex=False)

            get_bound_rawCount = df_excel.loc[df_excel['Sample'] == f'R52_{bound_file_number:02}', 'Carried Sequences'].iloc[0]
            get_unbound_rawCount = df_excel.loc[df_excel['Sample'] == f'R52_{unbound_file_number:02}', 'Carried Sequences'].iloc[0]

            for index, row in bound_df.iterrows():
                pattern = row['Pattern']
                matching_rows = unbound_df[unbound_df['Pattern'] == pattern]
                if not matching_rows.empty:
                    matching_row = matching_rows.iloc[0]
                    for base in ['A', 'T', 'G', 'C']:
                        numerator = row[base] #+ ((2.5 * get_bound_rawCount) / 1e6)
                        denominator = matching_row[base] #+ ((2.5 * get_unbound_rawCount) / 1e6)
                        enrich_value = (numerator / get_bound_rawCount) / (denominator / get_unbound_rawCount)
                        bound_df.at[index, f'Enrich {base}'] = enrich_value
                else:
                    logger.warning(f"No matching row found for pattern: {pattern}")

            bound_df['Enrich Sum'] = bound_df[['Enrich A', 'Enrich T', 'Enrich G', 'Enrich C']].sum(axis=1)

            for base in ['A', 'T', 'G', 'C']:
                norm_enrich_col = f'Norm Enrich {base}'
                
                bound_df[norm_enrich_col] = bound_df[f'Enrich {base}'] / bound_df['Enrich Sum']

            output_file_path = os.path.join(output_folder, f'R52_{bound_file_number:02}_Vs_R52_{unbound_file_number:02}.csv')
            bound_df.to_csv(output_file_path, index=False)
            logger.info(f"Output saved to: {output_file_path}")
        else:
            if not os.path.exists(bound_file_path):
                logger.error(f"File {bound_file_path} does not exist.")
            if not os.path.exists(unbound_file_path):
                logger.error(f"File {unbound_file_path} does not exist.")

def main():
    start_time = time.time()
    parser = argparse.ArgumentParser(description="Process enrichment and normalized enrichment files")
    parser.add_argument('--file_ranges', nargs='+', required=False, default=['1-14', '18-31'], help="List of file ranges, e.g., 1-14 18-31")
    parser.add_argument('--excel_file', type=str, default="./output/NKX25_row_counts_summary.xlsx", help="Path to the Excel file containing summary data")
    parser.add_argument('--output_folder', type=str, default='./output/NKX25/bound_vs_unbound_without_pseudocounts', help="Output folder (default: '../bound_vs_unbound')")
    
    args = parser.parse_args()
    if not os.path.exists(args.output_folder):
        os.makedirs(args.output_folder)
        logger.info(f"Created output folder: {args.output_folder}")
    
    df_excel = pd.read_excel(args.excel_file)   
    bound_range = parse_ranges(args.file_ranges)
    process_files(df_excel, bound_range, args.output_folder)
    end_time = time.time()
    total_time = end_time - start_time
    print(f"Total time taken: {total_time:.2f} seconds")

if __name__ == "__main__":
    main()
