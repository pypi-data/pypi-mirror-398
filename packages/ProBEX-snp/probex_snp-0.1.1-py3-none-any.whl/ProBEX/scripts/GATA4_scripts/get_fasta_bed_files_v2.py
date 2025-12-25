import os
import pandas as pd
import time
import argparse
import logging

"""
Author: [Shreya Sharma]
Date: [May 12, 2025]
Description:
    This script processes SNP data from CSV files to generate FASTA and BED files. The main functionalities include:
    Creating FASTA sequences from top K-values.
"""
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

def create_fasta(sequence, header):
    return f">{header}\n{sequence}\n"

def modify_snp_sequence(sequence, nucl):
    parts = sequence.split("[ATGC]")
    if len(parts) >= 3:
        new_sequence = f"{parts[0]}[ATGC]{parts[1]}{nucl}{parts[2]}[ATGC]{parts[3]}"
        new_sequence = new_sequence.replace("[ATGC]{2}", "")
        return new_sequence
    else:
        return sequence.replace("[ATGC]{2}", "")
        
def save_to_fasta(df, output_filename):
    with open(output_filename, 'w') as fasta_file:
        for idx, row in df.iterrows():
            if pd.notna(row['chrLoc']):
                nucl = row['original_rsID'].split("_")[1]
                header = f"{row['rsID_base']}_nucl:{nucl}_{row['chrLoc'].replace(chr(10), '')}"
                sequence = row['Pattern']
                sequence = modify_snp_sequence(sequence, nucl)
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
                bed_file.write(f"{chrom}\t{start}\t{end}\n")
            except (ValueError, AttributeError):
                logging.warning(f"Skipping invalid chrLoc: {chr_loc}")

def process_files(meme_excel, reference_csv, output_fasta, output_bed):
    start_time = time.time()
    logging.info("Reading data...")

    meme_df = pd.read_excel(meme_excel)
    meme_df = meme_df.rename(columns={'rsID': 'original_rsID'})  # avoid column name conflict
    meme_df['rsID_base'] = meme_df['original_rsID'].apply(lambda x: x.split("_")[0])

    reference_df = pd.read_csv(reference_csv)

    merged_df = pd.merge(
        meme_df, 
        reference_df[['rsID', 'chrLoc', 'Pattern']], 
        left_on='rsID_base', 
        right_on='rsID', 
        how='left'
    )
    #merged_df.to_csv("merged_output_500.csv", index=False)
    logging.info(f"Merged DataFrame shape: {merged_df.shape}")

    # Save FASTA and BED
    save_to_fasta(merged_df, output_fasta)
    save_to_bed(merged_df, output_bed)

    end_time = time.time()
    logging.info(f"Processing completed in {end_time - start_time:.2f} seconds.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract sequences from meme.xlsx and reference CSV to generate FASTA and BED files.")
    parser.add_argument("--meme_excel", default='./output/GATA4/motif_affect_GATA4/MEME/200_sequences_for_meme.xlsx', help="Path to meme Excel file.")
    parser.add_argument("--reference_csv", default='./output/GATA4/bound_vs_unbound/R52_38_Vs_R52_39.csv', help="CSV file with chrLoc and Pattern. You can use any file from TF NKX2.5")
    parser.add_argument("--output_fasta", default='./output/GATA4/motif_affect_GATA4/MEME/SNPs_200.fa', help="Output FASTA file path.")
    parser.add_argument("--output_bed", default='./output/GATA4/motif_affect_GATA4/MEME/SNPs_200.bed', help="Output BED file path.")

    args = parser.parse_args()
    process_files(args.meme_excel, args.reference_csv, args.output_fasta, args.output_bed)
