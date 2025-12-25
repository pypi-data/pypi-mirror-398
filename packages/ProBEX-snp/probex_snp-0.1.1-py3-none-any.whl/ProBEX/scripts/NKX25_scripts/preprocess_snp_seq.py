from abc import ABC, abstractmethod
import os
import re
import gzip
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed
import argparse
from pathlib import Path
import logging
import time
from contextlib import suppress

"""
-----------------------------------------------------------------------------
Author: [Shreya Sharma, PhD student @IITR]
Date: [2024-12-12]

=============================================================================
Script for Processing SNP Sequence Files: Extraction, Pattern Analysis, and Summary Report Generation
=============================================================================

This script provides a modular approach to process SNP sequence data across multiple steps.
It includes sequence extraction, pattern analysis, and generating comprehensive summaries.
The workflow is organized into four steps, implemented via processor classes for scalability.

Features:
- Parallel processing for efficiency.
- Handles `.fq.gz` compressed files and generates `.txt` and `.csv` outputs.
- Calculates nucleotide frequency at SNP positions.
- Supports error handling for robust execution.
- Generates a detailed Excel summary report with key metrics.

-----------------------------------------------------------------------------

Steps in the Workflow:
-----------------------------------------------------------------------------

Step 1: Sequence Extraction
- Processes `.fq.gz` files in directories starting with "R52_" to extract 44-character sequences.
- Extracted sequences matching the given pattern are saved in `.txt` files.
- Supports parallel processing with configurable thread count.

Step 2: Pattern Analysis
- Reads extracted `.txt` files, analyzes patterns, and calculates nucleotide frequencies.
- Generates `.csv` files summarizing patterns and nucleotide counts.
- Supports directory-based subfolder filtering and error handling.

Step 3: Data Aggregation and Summary Generation
- Aggregates counts from `.txt` files, total sequences in `.fq.gz`, and sum of `Total Count` from `.csv` files.
- Compiles the aggregated data into a structured Excel report.
- Operates across subdirectories to ensure all relevant data is captured.

Step 4: FASTA File Comparison for SNPs
- Compares reference and alternate allele sequences from FASTA files.
- Identifies and processes differences at specific SNP positions.
- Updates the existing `.csv` files with patterns derived from FASTA data.

-----------------------------------------------------------------------------

Usage:
-----------------------------------------------------------------------------

1. Command-line Arguments:
   - `--base_dir`: Base directory containing the raw sequence files.
   - `--pattern`: Regular expression for matching sequence patterns.
   - `--txt_folder`: Directory for storing `.txt` files.
   - `--csv_folder`: Directory for storing `.csv` files.
   - `--output_file`: Path for saving the final Excel summary file.

2. Command Execution:
   Example:
   python process_sequences.py --base_dir /path/to/raw/sequences \
                            --pattern 'GATCGGAAGAGCACACGTCTGAACTCCAGTCA' \
                            --txt_folder /path/to/save/txt_files \
                            --csv_folder /path/to/save/csv_files \
                            --output_file /path/to/output/summary.xlsx

-----------------------------------------------------------------------------
"""

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
class BaseProcessor(ABC):
    @abstractmethod
    def process(self):
        pass

class StepOneProcessor(BaseProcessor):
    EXTRACTION_LENGTH = 44
    VALID_FOLDER_PREFIX = "R52_"

    def __init__(self, base_dir, pattern, input_folder, txt_folder, num_workers=4, logger=None):
        self.base_dir = Path(base_dir)
        self.pattern = re.compile(pattern)  
        self.input_folder = input_folder
        self.txt_folder = Path(txt_folder)
        self.num_workers = num_workers
        self.logger = logger or logging.getLogger(__name__)

    def _is_valid_folder(self, folder_name):
        """Check if a folder is valid for processing."""
        folder_path = self.base_dir / folder_name
        return folder_path.is_dir() and folder_name.startswith(self.VALID_FOLDER_PREFIX)

    def _find_fq_gz_file(self, folder_path):
        """Find the first .fq.gz file in a folder."""
        return next(folder_path.glob("*.fq.gz"), None)

    def _process_file(self, input_file_path, output_file_path):
        """Process a single .fq.gz file and extract sequences."""
        try:
            with gzip.open(input_file_path, "rt") as input_file, output_file_path.open("w") as output_file:
                for line in input_file:
                    match = self.pattern.search(line[self.EXTRACTION_LENGTH:])
                    if match:
                        extracted_text = line[:self.EXTRACTION_LENGTH + match.start()]
                        if 'N' not in extracted_text and len(extracted_text) == self.EXTRACTION_LENGTH:
                            output_file.write(extracted_text + "\n")
            self.logger.info(f"Extraction completed. Output saved to: {output_file_path}")
        except Exception as e:
            self.logger.error(f"Error processing file {input_file_path}: {e}")

    def process_folder(self, folder_name):
        """Process a folder to extract sequences."""
        folder_path = self.base_dir / folder_name
        output_file_path = self.txt_folder / f"{folder_name}.txt"

        if output_file_path.exists():
            self.logger.warning(f"Skipping {folder_name}: Output file already exists.")
            return

        if not self._is_valid_folder(folder_name):
            self.logger.warning(f"Skipping {folder_name}: Not a valid folder.")
            return

        input_file_path = self._find_fq_gz_file(folder_path)
        if input_file_path:
            self._process_file(input_file_path, output_file_path)
        else:
            self.logger.info(f"No .fq.gz file found in {folder_name}")

    def process(self):
        """Process all valid folders in the base directory."""
        self.logger.info("Starting sequence extraction...")
        folder_names = [
            folder_name for folder_name in self.base_dir.iterdir() if folder_name.is_dir()
        ]

        errors = []
        with ThreadPoolExecutor(max_workers=self.num_workers) as executor:
            futures = {executor.submit(self.process_folder, folder.name): folder.name for folder in folder_names}
            for future in as_completed(futures):
                folder_name = futures[future]
                with suppress(Exception):  
                    future.result()
                if future.exception():
                    errors.append(folder_name)

        if errors:
            self.logger.error(f"Failed to process the following folders: {', '.join(errors)}")
        else:
            self.logger.info("Processing completed successfully.")

class StepTwoProcessor:
    def __init__(self, txt_folder, csv_folder, file_pattern, transcription_factor):
        self.txt_folder = txt_folder
        self.csv_folder = csv_folder
        self.file_pattern = file_pattern
        self.transcription_factor = transcription_factor

        if transcription_factor == "NKX25":
            self.range = range(1, 34)
        elif transcription_factor == "GATA4":
            self.range = range(34, 66)
        elif transcription_factor == "TBX5":
            self.range = range(66, 97)
        else:
            raise ValueError("Invalid transcription factor: Choose from 'NKX2-5', 'GATA4', or 'TBX5'")

    @staticmethod
    def base5_encode(sequence):
        encoding_dict = {'A': 0, 'T': 1, 'G': 2, 'C': 3, 'N': 4}
        return sum(encoding_dict[nucleotide] * (5 ** i) for i, nucleotide in enumerate(sequence))

    @staticmethod
    def read_lines(filename):
        with open(filename, 'r') as file:
            return [line.strip() for line in file]

    def process_lines(self, lines):
        pattern_dict = {}
        for line in lines:
            if len(line) != 44:
                continue
            sequence = line[:44]
            pattern_key = f"[ATGC]{{2}}{sequence[2:21]}[ATGC]{sequence[22:42]}[ATGC]{{2}}"
            nucleotide_22 = sequence[21]

            if pattern_key not in pattern_dict:
                pattern_dict[pattern_key] = {'total': 0, 'A': 0, 'T': 0, 'G': 0, 'C': 0}

            pattern_dict[pattern_key]['total'] += 1
            pattern_dict[pattern_key][nucleotide_22] += 1
        return pattern_dict

    def process_file(self, file_name):
        input_file_path = os.path.join(self.txt_folder, file_name)
        output_file_path = os.path.join(self.csv_folder, file_name.replace(".txt", ".csv"))

        if os.path.exists(output_file_path):
            logging.warning(f"Skipping {file_name}: CSV already exists.")
            return

        try:
            lines = self.read_lines(input_file_path)
            if not lines:
                logging.warning(f"Warning: No data in {input_file_path}")
                return

            pattern_dict = self.process_lines(lines)
            df = pd.DataFrame.from_dict(pattern_dict, orient='index').reset_index()
            df.rename(columns={'index': 'Pattern', 'total': 'Total Count'}, inplace=True)
            df.to_csv(output_file_path, index=False)
            logging.info(f"Pattern processing completed for {file_name}. CSV saved to: {output_file_path}")
        except Exception as e:
            logging.error(f"Error processing {file_name}: {e}")

    def process(self):
        print("Starting Step 2: Processing patterns in TXT files...")
        txt_files = [
            f for f in os.listdir(self.txt_folder) 
            if f.startswith(self.file_pattern.split("{}")[0]) and f.endswith(".txt")
        ]
        
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(self.process_file, file_name) for file_name in txt_files]
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    logging.error(f"Error in thread execution: {e}")


class StepThreeProcessor(BaseProcessor):
    def __init__(self, txt_folder, csv_folder, folders_to_check, output_file):
        self.txt_folder = txt_folder
        self.csv_folder = csv_folder
        self.folders_to_check = folders_to_check
        self.output_file = output_file

    def process(self):
        if os.path.exists(self.output_file):
            logging.info(f"Output file {self.output_file} already exists. Skipping processing.")
            return
        txt_data, csv_data, fq_data = {}, {}, {}

        for txt_file in os.listdir(self.txt_folder):
            if txt_file.endswith('.txt'):
                try:
                    with open(os.path.join(self.txt_folder, txt_file), 'r') as f:
                        txt_data[os.path.splitext(txt_file)[0]] = len(f.readlines())
                except Exception as e:
                    logging.error(f"Error reading TXT file {txt_file}: {e}")

        for csv_file in os.listdir(self.csv_folder):
            if csv_file.endswith('.csv'):
                try:
                    df = pd.read_csv(os.path.join(self.csv_folder, csv_file))
                    csv_data[os.path.splitext(csv_file)[0]] = df['Total Count'].sum()
                except Exception as e:
                    logging.error(f"Error reading CSV file {csv_file}: {e}")

        for folder in self.folders_to_check:
            if os.path.exists(folder): 
                for subfolder in os.listdir(folder):
                    if subfolder.startswith('R52_'):
                        for fq_file in os.listdir(os.path.join(folder, subfolder)):
                            if fq_file.endswith('.fq.gz'):
                                try:
                                    with gzip.open(os.path.join(folder, subfolder, fq_file), 'rt') as f:
                                        fq_data[subfolder] = sum(1 for _ in f) // 4
                                except Exception as e:
                                    logging.error(f"Error reading FASTQ file {fq_file}: {e}")

        data = []
        for file_name, total_lines in txt_data.items():
            total_count = csv_data.get(file_name, 0)
            fq_total_sequences = fq_data.get(file_name, 0)
            data.append([file_name, fq_total_sequences, total_lines, total_count])

        df = pd.DataFrame(data, columns=['Sample', 'FASTQ Total Sequences', 'TXT Total Lines', 'CSV Total Count'])
        try:
            df.to_excel(self.output_file, index=False)
            logging.info(f"Summary saved to {self.output_file}")
        except Exception as e:
            logging.error(f"Error saving Excel summary: {e}")

class StepFourProcessor(BaseProcessor):
    def __init__(self, fasta_alt, fasta_ref, csv_folder, output_folder):
        self.fasta_alt = fasta_alt
        self.fasta_ref = fasta_ref
        self.csv_folder = csv_folder
        self.output_folder = output_folder

    def process(self):
        logging.info("Processing FASTA files for ref and alt alleles...")
        start_time = time.time()
        pattern_data = self.process_fasta_files(self.fasta_alt, self.fasta_ref)
        logging.debug(f"Processed {len(pattern_data)} pattern data entries")
        self.update_csv_files(pattern_data)
        elapsed_time = time.time() - start_time
        logging.info(f"Step 4 completed. Time taken: {elapsed_time:.2f} seconds")

    def process_fasta_files(self, file1, file2):
        logging.debug("Reading FASTA files...")
        with open(file1, 'r') as f1, open(file2, 'r') as f2:
            lines1 = f1.readlines()
            lines2 = f2.readlines()

        logging.debug(f"FASTA file {file1} has {len(lines1)} lines")
        logging.debug(f"FASTA file {file2} has {len(lines2)} lines")

        data = []
        for header1, header2, seq1, seq2 in zip(lines1[::2], lines2[::2], lines1[1::2], lines2[1::2]):
            if header1.startswith('>chr') and header2.startswith('>chr'):
                chrLoc1 = header1.strip('>')
                chrLoc2 = header2.strip('>')
                if chrLoc1 == chrLoc2:
                    sequence1 = seq1.strip().upper()
                    sequence2 = seq2.strip().upper()
                    pattern1 = f"{sequence1[0:19]}[ATGC]{sequence1[20:40]}"
                    pattern2 = f"{sequence1[0:19]}[ATGC]{sequence2[20:40]}"
                    logging.debug(f"Pattern1: {pattern1}, Pattern2: {pattern2}")
                    if pattern1 == pattern2:
                        alt_allele = sequence1[19]
                        ref_allele = sequence2[19]
                        logging.debug(f"Alt: {alt_allele}, Ref: {ref_allele}")
                        data.append((chrLoc1, pattern1, alt_allele, ref_allele))
                        logging.debug(f"Match found: chrLoc={chrLoc1}, alt_allele={alt_allele}, ref_allele={ref_allele}")
        logging.debug(f"Processed {len(data)} matching chromosome locations")
        return data

    def update_csv_files(self, pattern_data):
        os.makedirs(self.output_folder, exist_ok=True)

        def match_pattern(x, pattern):
            """
            Custom pattern matching function.
            """
            return pattern.upper() in x.upper()

        for num in range(1, 35):
            file_number = str(num).zfill(2)
            csv_file = os.path.join(self.csv_folder, f"R52_{file_number}.csv")
            output_file = os.path.join(self.output_folder, f"R52_{file_number}.csv")
            
            if os.path.exists(output_file):
                logging.info(f"Output file {output_file} already exists. Skipping update.")
                continue

            if os.path.exists(csv_file):
                logging.debug(f"Updating file .. {csv_file}")
                df = pd.read_csv(csv_file)
                updated_rows = 0
                for chrLoc, pattern, alt_allele, ref_allele in pattern_data:
                    extended_pattern = f"[ATGC]{{2}}{pattern}[ATGC]{{2}}"
                    logging.debug(f"Searching for extended pattern: {extended_pattern}")
                    matches = df['Pattern'].apply(lambda x: match_pattern(x, extended_pattern))
                    if any(matches):
                        updated_rows += 1
                        df.loc[matches, 'chrLoc'] = chrLoc
                        df.loc[matches, 'RefAllele'] = ref_allele
                        df.loc[matches, 'AltAllele'] = alt_allele
                        logging.debug(f"Pattern matched in {os.path.basename(csv_file)}: chrLoc={chrLoc}, alt_allele={alt_allele}, ref_allele={ref_allele}")
                
                df.to_csv(output_file, index=False)
                logging.debug(f"Updated {os.path.basename(csv_file)} saved.")
            else:
                logging.warning(f"CSV file {csv_file} not found")

        logging.info("CSV files update completed.")

class RSIDUpdater:
    def __init__(self, base_path, inp_file_path, start_index, end_index):
        self.base_path = base_path
        self.inp_file_path = inp_file_path
        self.start_index = start_index
        self.end_index = end_index
        self.rsid_df = pd.read_csv(inp_file_path)
        self.rsID_folder = os.path.join(base_path, "rsID_added")
        
        os.makedirs(self.rsID_folder, exist_ok=True)
        logging.basicConfig(level=logging.INFO)
        logging.info(f"The rsID folder path is: {self.rsID_folder}")

    @staticmethod
    def convert_pattern(sequence):
        """Convert a sequence into the desired pattern."""
        replacement = "[ATGC]"
        return f"[ATGC]{{2}}{sequence[:19]}{replacement}{sequence[20:40]}[ATGC]{{2}}"

    def update_rsid(self):
        """Update rsID in the concatenated dataframes."""
        for i in range(self.start_index, self.end_index + 1):
            filename = os.path.join(self.base_path, f"R52_{i:02d}.csv")
            output_filename = os.path.join(self.rsID_folder, f"R52_{i:02d}.csv")

            if os.path.exists(filename):
                logging.info(f"Processing file {filename}...")

                if not os.path.exists(output_filename):
                    concatenated_df = pd.read_csv(filename)
                    logging.info(f"Columns in concatenated_df: {concatenated_df.columns}")

                    for _, row in self.rsid_df.iterrows():
                        sequence = row["Pattern"]
                        rsID = row["rsID"]
                        pattern = self.convert_pattern(sequence)
                        matching_indices = concatenated_df.index[concatenated_df["Pattern"] == pattern].tolist()

                        if matching_indices:
                            logging.info(f"rsID {rsID} found in {len(matching_indices)} rows.")  
                            concatenated_df.loc[matching_indices, "rsID"] = rsID

                    concatenated_df.to_csv(output_filename, index=False)
                    logging.info(f"Processed and saved {output_filename}.")
                else:
                    logging.info(f"File {output_filename} exist in the target directory. Skipping.")
            else:
                logging.info(f"File {filename} does not exist. Skipping.")
                
class SNPProcessor:
    def __init__(self, args):
        self.args = args
        self.directory = './output/NKX25/processsed_files/rsID_added'

    def process_file(self, file_name):
        df = pd.read_csv(file_name, low_memory=False)
        mask = df['rsID'].notnull() & ~df['rsID'].astype(str).str.startswith('chr')
        df.loc[mask, 'rsID'] = df.loc[mask, 'rsID'].str.replace("_G", "")
        df.to_csv(file_name, index=False)

    def process_files(self):
        csv_files = [file for file in os.listdir(self.directory) if file.endswith('.csv')]
        for file_name in csv_files:
            self.process_file(os.path.join(self.directory, file_name))
        logging.info("Processing completed for all files.")

class ScriptExecutor:
    def __init__(self, args):
        self.args = args

    def run(self):
        logging.info("Script started.")
        total_start_time = time.time()
        try:
            logging.info("Starting Step 1: Sequence extraction...")
            start_time = time.time()
            step1 = StepOneProcessor(self.args.base_dir, self.args.pattern, self.args.input_folder, self.args.txt_folder)
            step1.process()
            elapsed_time = time.time() - start_time
            logging.info(f"Step 1 completed. Time taken: {elapsed_time:.2f} seconds")

            logging.info("Starting Step 2: Processing patterns...")
            start_time = time.time()
            step2 = StepTwoProcessor(self.args.txt_folder, self.args.csv_folder, "R52_{}", self.args.transcription_factor)
            step2.process()
            elapsed_time = time.time() - start_time
            logging.info(f"Step 2 completed. Time taken: {elapsed_time:.2f} seconds")

            logging.info("Starting Step 3: Processing patterns...")
            start_time = time.time()
            step3 = StepThreeProcessor(self.args.txt_folder, self.args.csv_folder, ['GATA4', 'TBX5', 'NKX25'], self.args.output_file)
            step3.process()
            elapsed_time = time.time() - start_time
            logging.info(f"Step 3 completed. Time taken: {elapsed_time:.2f} seconds")

            logging.info("Starting Step 4: Processing patterns...")
            start_time = time.time()
            step4 = StepFourProcessor(self.args.fasta_alt, self.args.fasta_ref, self.args.csv_folder, self.args.output_folder)
            step4.process()
            elapsed_time = time.time() - start_time
            logging.info(f"Step 4 completed. Time taken: {elapsed_time:.2f} seconds")

            logging.info("Starting Step 5: Updating RSID...")
            start_time = time.time()
            rsid_updater = RSIDUpdater(base_path=self.args.output_folder, inp_file_path=self.args.rsid_file, start_index=self.args.rsid_start, end_index=self.args.rsid_end)
            rsid_updater.update_rsid()
            elapsed_time = time.time() - start_time
            logging.info(f"Step 5 completed. Time taken: {elapsed_time:.2f} seconds")

            snp_processor = SNPProcessor(self.args)
            snp_processor.process_files()
            logging.info("SNP processing completed.")
            total_elapsed_time = time.time() - total_start_time
            logging.info(f"Script execution completed. Total time taken: {total_elapsed_time:.2f} seconds")

        except Exception as e:
            logging.error(f"An error occurred: {e}")

if __name__ == "__main__":
    logging.info("Script started.")
    parser = argparse.ArgumentParser(description="Process SNP sequence files.")
    parser.add_argument('--base_dir', default="./data/NKX25", help="Provide the base directory path containing folders with gunzip files.")
    parser.add_argument('--pattern', default="GATCGGAAGAGCACACGTCTGAACTCCAGTCA", help="Library pattern to search in the sequencing file")
    parser.add_argument('--input_folder', default='./output/NKX25', help="Folder containing TXT files")
    parser.add_argument('--txt_folder', default='./output/NKX25/txt_files', help="Folder containing TXT files")
    parser.add_argument('--csv_folder', default='./output/NKX25/csv_files', help="Folder containing CSV files")
    parser.add_argument('--output_file', default='./output/NKX25_files_count_summary.xlsx', help="Output Excel count summary file")
    parser.add_argument('--output_folder', default='./output/NKX25/processsed_files', help="Folder containing CSV files with appended rsID and chr locations and alt and ref information.")
    parser.add_argument('--transcription_factor', default='NKX25', choices=['NKX25', 'GATA4', 'TBX5'], help="Transcription factor to process")
    parser.add_argument("--fasta_alt", default='./data/CHD_40mer_fasta_alt2', help="FASTA file with alternate alleles")
    parser.add_argument("--fasta_ref", default='./data/CHD_40mer_fasta_ref2', help="FASTA file with reference alleles")
    parser.add_argument('--rsid_file', default='./data/outputFromEdwin.csv', help="CSV file containing rsID from Edwin")
    parser.add_argument('--rsid_start', type=int, default=1, help="Start index for rsID files")
    parser.add_argument('--rsid_end', type=int, default=35, help="End index for rsID files")
    args = parser.parse_args()

    if not os.path.exists(args.txt_folder):
        os.makedirs(args.txt_folder)

    if not os.path.exists(args.csv_folder):
        os.makedirs(args.csv_folder)

    executor = ScriptExecutor(args)
    executor.run()
