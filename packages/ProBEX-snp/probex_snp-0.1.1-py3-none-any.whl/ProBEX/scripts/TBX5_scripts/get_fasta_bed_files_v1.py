import os
import re
import pandas as pd
import time
import logging
import argparse
"""
Author: [Shreya Sharma]
Date: [December 27, 2024]
Description:
    This script processes SNP data from CSV files to generate FASTA and BED files. Top 500 SNPs extracted based on the top enrichment.
Usage:
    python script_name.py --input_folder [path_to_input_folder] --output_fasta_folder [path_to_output_fasta_folder] --output_bed_folder [path_to_output_bed_folder]
    
    --input_folder: Directory containing the CSV files to be processed.
    --output_fasta_folder: Directory to save the generated FASTA files.
    --output_bed_folder: Directory to save the generated BED files.

"""

logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

def create_fasta(sequence, header):
    return f">{header}\n{sequence}\n"
    
def modify_snp_sequence(sequence, row):
    sorted_by_value = row['Max_Enrich_Type']
    nucl = sorted_by_value.split()[-1] 
    parts = sequence.split("[ATGC]")
    if len(parts) >= 3:
        new_sequence = f"{parts[0]}[ATGC]{parts[1]}{nucl}{parts[2]}[ATGC]{parts[3]}"
        new_sequence = new_sequence.replace("[ATGC]{2}", "")
        return new_sequence
    else:
        return sequence.replace("[ATGC]{2}", "") 

def save_to_fasta(df, output_filename, modify_snp_sequence):
    with open(output_filename, 'w') as fasta_file:
        for _, row in df.iterrows():
            if pd.notna(row['chrLoc']):
                header = row['chrLoc'].replace("\n", "")
                sequence = row['Pattern']
                if modify_snp_sequence:
                    sequence = modify_snp_sequence(sequence, row)
                    sequence = sequence.replace("\n", "")
                fasta_file.write(create_fasta(sequence, header))

def save_to_bed(df, output_filename):
    with open(output_filename, 'w') as bed_file:
        for _, row in df.iterrows():
            chr_loc = row.get('chrLoc', None)
            if pd.isna(chr_loc):
                continue
            try:
                chr_loc = str(chr_loc)
                chrom, pos = chr_loc.split(':')
                start, end = pos.split('-')
                bed_file.write(f"{chrom}\t{start}\t{end}")
            except (ValueError, AttributeError):
                logging.warning(f"Skipping invalid chrLoc: {chr_loc}")

def process_file(file_path, enrich_columns, output_fasta_folder, output_bed_folder):
    start_time = time.time()
    filename = os.path.basename(file_path)
    logging.info(f"Processing file: {filename}")
    
    df = pd.read_csv(file_path)
    
    df['Max_Enrich_Value'] = df[enrich_columns].max(axis=1)
    df['Max_Enrich_Type'] = df[enrich_columns].idxmax(axis=1)
    df['Min_Enrich_Value'] = df[enrich_columns].min(axis=1)
    df['Min_Enrich_Type'] = df[enrich_columns].idxmin(axis=1)

    df_sorted_pos_o = df.sort_values(by='Max_Enrich_Value', ascending=False).head(600)
    df_sorted_pos_b = df_sorted_pos_o[pd.notna(df_sorted_pos_o['chrLoc'])]
    df_sorted_pos = df_sorted_pos_b.head(500)
    logging.info(f"Number of rows: {df_sorted_pos.shape[0]}")
    fasta_output_pos = os.path.join(output_fasta_folder, os.path.splitext(filename)[0] + '_SNPs.fa')
    output_bed = os.path.join(output_bed_folder, os.path.splitext(filename)[0] + '_SNPs.bed')
    save_to_fasta(df_sorted_pos, fasta_output_pos, modify_snp_sequence)
    save_to_bed(df_sorted_pos_b, output_bed)
    end_time = time.time()
    logging.info(f"Processing of {filename} completed in {end_time - start_time:.2f} seconds.")

def main(input_folder, output_fasta_folder, output_bed_folder):
    start_time = time.time()

    os.makedirs(output_fasta_folder, exist_ok=True)
    os.makedirs(output_bed_folder, exist_ok=True)
    
    enrich_columns = ['Enrich A', 'Enrich T', 'Enrich G', 'Enrich C']
    
    for filename in os.listdir(input_folder):
        if filename.endswith(".csv"):
            file_path = os.path.join(input_folder, filename)
            process_file(file_path, enrich_columns, output_fasta_folder, output_bed_folder)

    end_time = time.time()
    logging.info(f"All files processed in {end_time - start_time:.2f} seconds.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process SNP files to generate FASTA and BED files.")
    parser.add_argument("--input_folder", default='./output/TBX5/bound_vs_unbound', help="Input folder containing CSV files.")
    parser.add_argument("--output_fasta_folder", default='./output/TBX5/bound_vs_unbound/TBX5_fasta_files', help="Output folder to save FASTA files.")
    parser.add_argument("--output_bed_folder", default='./output/TBX5/bound_vs_unbound/TBX5_bed_files', help="Output folder to save BED files.")
    
    args = parser.parse_args()
    main(args.input_folder, args.output_fasta_folder, args.output_bed_folder)