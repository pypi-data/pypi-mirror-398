import pandas as pd
import argparse
import logging
import time

"""
Author: [Shreya Sharma]
Date: [2024-12-27]
Description: Script for processing rsID filtering data and applying specific filters based on threshold values. 

	Functionality:
	1. Reads an input Excel file containing rsID filtering data and another Excel file with GATA4 labels.
	2. Extracts specified columns for processing.
	3. Applies two filters:
	   a. Filter(B,E): Checks if specific conditions in columns B and E are met.
	   b. Filter(B,C,E,F): Checks if specific conditions in columns B, C, E, and F are met.
	4. Merges the filtered data with the GATA4 labels to include the '5/MPass' column.
	5. Applies another filter:
	   a. Filter(H,I): Adds a column where rows satisfying both Filter(B,C,E,F) and '5/MPass' are marked.
	6. Outputs the processed data with additional filter columns to a new Excel file.

	Key Features:
	- Uses pandas for data manipulation.
	- Supports command-line arguments for specifying input and output file paths, ensuring flexibility and reusability.
	- Modular design with functions for readability and maintainability.

	Command-line Arguments:
	- `--file_path`: Path to the rsID filtering Excel file.
	- `--GATA4_file_path`: Path to the GATA4 labels Excel file.
	- `--output_file`: (Optional) Path to save the output Excel file (default: 'parameters.xlsx').

	Example Usage:
	python script_name.py --file_path rsID_filtering.xlsx --GATA4_file_path GATA4_labels.xlsx --output_file extracted_rsIDs.xlsx
"""

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
pd.set_option('future.no_silent_downcasting', True)

def check_filter(row, columns):
    """
    Check if all values in the specified columns are equal to 1.
    
    Parameters:
    row (pd.Series): A row of the DataFrame.
    columns (list): List of column names to check.

    Returns:
    int: 1 if all values are 1, otherwise 0.
    """
    values = row[columns].fillna(0)
    return 1 if all(values == 1) else 0

def main(file_path, gata4_file_path, output_file):
    """
    Process the input Excel file to apply filters and save the result.

    Parameters:
    file_path (str): Path to the rsID filtering Excel file.
    gata4_file_path (str): Path to the GATA4 labels Excel file.
    output_file (str): Path to save the resulting Excel file.
    """
    start_time = time.time()
    logging.info("Reading input files...")

    df = pd.read_excel(file_path)
    gata4_df = pd.read_excel(gata4_file_path)

    logging.info("Extracting relevant columns...")
    columns_to_extract = [
        'rsID', 
        'LT5/M Threshold \nin Unbound (0nM)\nin R1 & R2 both', 
        'LT5/M Threshold \nLibrary Status', 
        'LT5/M Threshold \nin Bound (0nM)\nin R1 & R2 both', 
        'Threshold (<=0.2 or >=2)\nUnb/Lib', 
        'Threshold (<=0.2 or >=5) b/Unb'
    ]
    extracted_df = df[columns_to_extract].copy()

    logging.info("Applying filters...")
    columns_to_check_BE = [
        'LT5/M Threshold \nin Unbound (0nM)\nin R1 & R2 both', 
        'Threshold (<=0.2 or >=2)\nUnb/Lib'
    ]
    columns_to_check_BCEF = [
        'LT5/M Threshold \nin Unbound (0nM)\nin R1 & R2 both', 
        'LT5/M Threshold \nLibrary Status', 
        'Threshold (<=0.2 or >=2)\nUnb/Lib', 
        'Threshold (<=0.2 or >=5) b/Unb'
    ]

    extracted_df['Filter(B,E)'] = extracted_df.apply(lambda row: check_filter(row, columns_to_check_BE), axis=1)
    extracted_df['Filter(B,C,E,F)'] = extracted_df.apply(lambda row: check_filter(row, columns_to_check_BCEF), axis=1)

    logging.info("Merging filtered data with GATA4 labels...")
    merged_df = pd.merge(extracted_df, gata4_df[['rsID', '5/MPass']], on='rsID', how='left')

    logging.info("Applying final filter...")
    merged_df['Filter(H,I)'] = 0
    merged_df.loc[(merged_df['Filter(B,C,E,F)'] == 1) & (merged_df['5/MPass'] == 1), 'Filter(H,I)'] = 1

    logging.info("Saving results to output file...")
    merged_df.to_excel(output_file, index=False)

    end_time = time.time()
    logging.info(f"DataFrame with additional filter columns saved to '{output_file}'")
    logging.info(f"Execution time: {end_time - start_time:.2f} seconds")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process rsID filtering and apply filters.")
    parser.add_argument("--file_path", default="./output/GATA4/rsID_filtering.xlsx", help="Path to the rsID filtering Excel file.")
    parser.add_argument("--gata4_file_path", default="./output/GATA4_labels.xlsx", help="Path to the GATA4 labels Excel file.")
    parser.add_argument("--output_file", default="./output/GATA4/extracted_rsIDs.xlsx", help="Path to save the output Excel file.")

    args = parser.parse_args()
    main(args.file_path, args.gata4_file_path, args.output_file)