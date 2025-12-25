import os
import pandas as pd
import logging
import argparse
import time
from abc import ABC, abstractmethod

"""
-----------------------------------------------------------------------------
Author: [Shreya Sharma, PhD student @IITR]
Date: [2024-12-12]
Description:
	This script processes genomic CSV data by categorizing entries based on rsID patterns, generating summary statistics, reindexing datasets to match expected rsIDs, and filtering based on sequence count thresholds. It organizes data into "carried" and "not carried" categories, builds comprehensive summaries, and outputs labeled datasets for downstream analysis. The script supports modular execution using command-line arguments.
-----------------------------------------------------------------------------
"""

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

class BaseProcessor(ABC):
    @abstractmethod
    def process(self):
        pass

class RSIDProcessor(BaseProcessor):
    def __init__(self, input_dir, carried_dir, not_carried_dir):
        self.input_dir = input_dir
        self.carried_dir = carried_dir
        self.not_carried_dir = not_carried_dir
        os.makedirs(self.carried_dir, exist_ok=True)
        os.makedirs(self.not_carried_dir, exist_ok=True)

    def process_csv_file(self, file_path):
        df = pd.read_csv(file_path, low_memory=False)
        df['Carried'] = df['rsID'].apply(lambda x: 1 if isinstance(x, str) and (x.startswith('rs') or x.startswith('chr') or x.startswith('hANF')) else 0)
        df.to_csv(file_path, index=False)
        carried_df = df[df['Carried'] == 1]
        not_carried_df = df[df['Carried'] == 0]
        file_name = os.path.basename(file_path)
        carried_df.to_csv(os.path.join(self.carried_dir, file_name), index=False)
        not_carried_df.to_csv(os.path.join(self.not_carried_dir, file_name), index=False)

    def process(self):
        logging.debug(f"Processing directory: {self.input_dir}")
        for file_name in os.listdir(self.input_dir):
            if file_name.endswith(".csv"):
                file_path = os.path.join(self.input_dir, file_name)
                self.process_csv_file(file_path)
        logging.debug("Step 1: Processing completed.")

class RSIDSummary(BaseProcessor):
    def __init__(self, carried_dir, not_carried_dir, output_excel):
        self.carried_dir = carried_dir
        self.not_carried_dir = not_carried_dir
        self.output_excel = output_excel

    def count_rows_and_sum_total(self, file_path):
        df = pd.read_csv(file_path)
        row_count = len(df)
        total_count_sum = df['Total Count'].sum() if 'Total Count' in df.columns else 0
        return row_count, total_count_sum

    def process(self):
        logging.debug(f"Generating summary for carried and not carried directories.")
        file_names = []
        carried_counts = []
        not_carried_counts = []
        carried_total_counts = []
        not_carried_total_counts = []

        for file_name in os.listdir(self.carried_dir):
            if file_name.endswith(".csv"):
                file_path = os.path.join(self.carried_dir, file_name)
                file_names.append(file_name)
                rows, total_count = self.count_rows_and_sum_total(file_path)
                carried_counts.append(rows)
                carried_total_counts.append(total_count)

        for file_name in os.listdir(self.not_carried_dir):
            if file_name.endswith(".csv"):
                file_path = os.path.join(self.not_carried_dir, file_name)
                rows, total_count = self.count_rows_and_sum_total(file_path)
                not_carried_counts.append(rows)
                not_carried_total_counts.append(total_count)

        while len(not_carried_counts) < len(file_names):
            not_carried_counts.append(None)
            not_carried_total_counts.append(None)

        df_summary = pd.DataFrame({
            'Sample': file_names,
            'Carried': carried_counts,
            'notCarried': not_carried_counts,
            'Carried Sequences': carried_total_counts,
            'notCarried Sequences': not_carried_total_counts
        })

        df_summary.to_excel(self.output_excel, index=False)
        logging.debug(f"Step 3: Row counts and Total Count sums saved to {self.output_excel}")
        
class RSIDReindexer:
    def __init__(self, folder_path, rsIDs_file, output_folder):
        self.folder_path = folder_path
        self.rsIDs_df = pd.read_csv(rsIDs_file)
        self.output_folder = output_folder
        self.expected_rsIDs = self.rsIDs_df['rsID'].tolist()

    def reindex_dataframe(self, df):
        df = df.set_index('rsID')
        df = df.reindex(self.expected_rsIDs).reset_index()
        return df

    def add_missing_rows(self, df, all_dataframes):
        for rsID in self.expected_rsIDs:
            if rsID not in df['rsID'].values:
                found = False
                for other_df in all_dataframes.values():
                    if rsID in other_df['rsID'].values:
                        row_to_add = other_df[other_df['rsID'] == rsID].copy()
                        row_to_add[['Total Count', 'A', 'T', 'G', 'C']] = 0
                        df = pd.concat([df, row_to_add], ignore_index=True)
                        found = True
                        break
                if not found and rsID == 'rs28628732':
                    pattern = "[ATGC]{2}TAGGGCATCGCCAGCCAGA[ATGC]GTCTCTGGCTGGCAAAGTTG[ATGC]{2}"
                    chrLoc = "chr5:43071679-43071719"
                    new_row = pd.DataFrame({
                        'rsID': [rsID],
                        'Pattern': [pattern],
                        'chrLoc': [chrLoc],
                        'AltAllele': ['A'],
                        'RefAllele': ['G'],
                        'Total Count': [0],
                        'Carried': 1,
                        'A': [0],
                        'T': [0],
                        'G': [0],
                        'C': [0]
                    })
                    df = pd.concat([df, new_row], ignore_index=True)
        return df

    def process(self):
        logging.debug(f"Processing files in folder: {self.folder_path}")
        dataframes = {}
        for file_name in os.listdir(self.folder_path):
            if file_name.endswith(".csv"):
                file_path = os.path.join(self.folder_path, file_name)
                df = pd.read_csv(file_path)
                dataframes[file_name] = df

        for file_name, df in dataframes.items():
            df = self.add_missing_rows(df, dataframes)
            df = df[df['rsID'].str.startswith(('rs', 'chr', 'hANF'))]
            if len(df) != 3319:
                logging.warning(f"File {file_name} does not have 3319 rows. It has {len(df)} rows.")
                missing_rsIDs = set(self.expected_rsIDs) - set(df['rsID'].tolist())
                logging.warning(f"Missing rsIDs in {file_name}: {missing_rsIDs}")
            df = self.reindex_dataframe(df)
            dataframes[file_name] = df

        logging.debug("Processing completed.")
        self.save_dataframes(self.output_folder, dataframes)

        return dataframes

    def save_dataframes(self, output_folder, dataframes):
        os.makedirs(output_folder, exist_ok=True)
        for file_name, df in dataframes.items():
            output_path = os.path.join(output_folder, file_name)
            df.to_csv(output_path, index=False)
            logging.debug(f"File saved: {output_path}")

class RSIDFilter(BaseProcessor):
    def __init__(self, output_folder, seq_count_df, selected_files, output_label_file):
        self.output_folder = output_folder
        self.seq_count_df = seq_count_df
        self.selected_files = selected_files
        self.output_label_file = output_label_file

    def count_rows_and_filter(self, df, original_count):
        df["Counts in Million"] = (df["Total Count"] / original_count) * 1e6
        df["5MPass"] = (df["Counts in Million"] > 5).astype(int)
        return df[df["Counts in Million"] > 5]

    def process(self):
        logging.debug(f"Filtering files and applying 5MPass threshold.")
        summary_data = []
        labels_df = pd.DataFrame()

        for filename in self.selected_files:
            if filename.endswith(".csv"):
                file_path = os.path.join(self.output_folder, filename)
                df = pd.read_csv(file_path)

                if "Total Count" not in df.columns:
                    logging.warning(f"Column 'Total Count' not found in {filename}. Skipping this file.")
                    continue

                sample_name = filename
                original_count_row = self.seq_count_df[self.seq_count_df["Sample"] == sample_name]

                if original_count_row.empty:
                    logging.warning(f"No matching 'Original count' for {sample_name}. Skipping this file.")
                    continue
                original_count = original_count_row["Carried Sequences"].values[0]

                filtered_df = self.count_rows_and_filter(df, original_count)
                summary_data.append({
                    "Filename": filename,
                    "Rows Before Filtering": len(df),
                    "Rows After Filtering": len(filtered_df)
                })
                summary_df = pd.DataFrame(summary_data)
                summary_df.to_csv("./output/NKX25/summary_5MPass.csv", index=False)

                if labels_df.empty:
                    labels_df['rsID'] = df['rsID']
                labels_df[sample_name] = df["5MPass"]

                logging.debug(f"Processed and saved: {filename}")

        labels_df.to_csv(self.output_label_file, index=False)
        logging.debug(f"Step 4: Saved rsID labels to {self.output_label_file}.")

        labels_df = pd.read_csv(self.output_label_file)
        labels_df['5/MPass'] = labels_df.drop(columns=['rsID']).all(axis=1).astype(int)
        labels_df.to_excel("./output/NKX25_labels.xlsx", index=False)
        logging.debug("Saved final labels with '5/MPass' column to NKX25_labels.xlsx.")

def parse_arguments():
    parser = argparse.ArgumentParser(description="Process RSID CSV files.")
    parser.add_argument('--input-dir', type=str, default='./output/NKX25/processsed_files/rsID_added', help="Input directory with CSV files (default: current directory)")
    parser.add_argument('--carried-dir', type=str, default='./output/NKX25/Carried', help="Directory to save carried CSV files (default: './Carried')")
    parser.add_argument('--not-carried-dir', type=str, default='./output/NKX25/notCarried', help="Directory to save not carried CSV files (default: './notCarried')")
    parser.add_argument('--output-excel', type=str, default='./output/NKX25_row_counts_summary.xlsx', help="Output Excel file for summary (default: './output.xlsx')")
    parser.add_argument('--selected-files', nargs='+', default=["R52_01.csv", "R52_03.csv", "R52_05.csv", "R52_07.csv", "R52_09.csv", "R52_11.csv", "R52_13.csv", "R52_18.csv", "R52_20.csv", "R52_22.csv", "R52_24.csv", "R52_26.csv", "R52_28.csv", "R52_30.csv"], help="List of selected CSV files for filtering (optional)")
    parser.add_argument('--rsids-file', type=str, default='./data/rsIDs.csv', help="CSV file with expected rsIDs (default: './rsIDs.csv')")
    parser.add_argument('--output_folder', type=str, default='./output/NKX25/CarriedForward', help="Folder to save processed data (default: './CarriedForward')")
    parser.add_argument('--output_file', type=str, default='./output/NKX25/rsID_filtering.xlsx', help='Path to save the processed output file')
    parser.add_argument('--output-label-file', type=str, default='./output/NKX25_labels.csv', help="Output CSV file for labels (default: './output_labels.csv')")
    return parser.parse_args()

def main():
    start_time = time.time()
    args = parse_arguments()

    processor = RSIDProcessor(args.input_dir, args.carried_dir, args.not_carried_dir)
    processor.process()
    
    summary = RSIDSummary(args.carried_dir, args.not_carried_dir, args.output_excel)
    summary.process()

    reindexer = RSIDReindexer(args.carried_dir, args.rsids_file, args.output_folder)
    reindexer.process()

    if args.selected_files:
        seq_count_df = pd.read_excel(args.output_excel)
        filter = RSIDFilter(args.output_folder, seq_count_df, args.selected_files, args.output_label_file)
        filter.process()
    
    end_time = time.time()
    total_time = end_time - start_time
    print(f"Total time taken: {total_time:.2f} seconds")

if __name__ == '__main__':
    main()
