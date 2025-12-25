import re
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import time
import logging
import argparse

"""
SNP Motif Analysis
Author: [Shreya Sharma]
Date: [November 24, 2024]

Description:
	This script performs motif analysis for SNPs (Single Nucleotide Polymorphisms) to determine their impact on sequence motifs using Position Weight Matrices (PWMs). It processes SNPs from two different files: one for increased rsIDs and another for decreased rsIDs. The analysis involves scoring sequence motifs in the context of SNP positions, removing flexible regions, and calculating the effect of SNPs on motif scores. Results are output as CSV files and visualized in a bar plot showing the number of affected vs non-affected SNPs for each category (increased and decreased). The script uses the `argparse` library for command-line argument parsing and logs the progress of its operations.
"""

class SNPMotifAnalysis:
    def __init__(self, rsid_inc_file, rsid_dec_file, input_file, pwm_matrix):
        self.rsid_inc_file = rsid_inc_file
        self.rsid_dec_file = rsid_dec_file
        self.input_file = input_file
        self.pwm_matrix = pwm_matrix
        self.logger = self.setup_logging()

    def setup_logging(self):
        logger = logging.getLogger("SNPMotifAnalysis")
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        return logger

    def remove_flexible_regions(self, pattern):
        while '[ATGC]{2}' in pattern:
            pattern = pattern.replace('[ATGC]{2}', '')
        return pattern

    def reverse_complement(self, sequence):
        complement = {'A': 'T', 'T': 'A', 'C': 'G', 'G': 'C'}
        return ''.join(complement[base] for base in reversed(sequence))

    def score_sequence(self, sequence):
        scores = []
        bins = []
        for i in range(len(sequence) - self.pwm_matrix.shape[0] + 1):
            window = sequence[i:i + self.pwm_matrix.shape[0]]
            score = sum(self.pwm_matrix[j, "ACGT".index(base)] for j, base in enumerate(window))
            scores.append(score)
            bins.append(i + 1)
        return scores, bins

    def count_snp_impact(self, max_bins, snp_position=20, kmer_size=6):
        affected = 0
        not_affected = 0

        for window_start in max_bins:
            window_end = window_start + kmer_size - 1
            if window_start <= snp_position <= window_end:
                affected += 1
            else:
                not_affected += 1

        return affected, not_affected

    def process_rsIDs(self, rsid_file, output_file):
        self.logger.info(f"Processing rsID file: {rsid_file}")
        rsid_list = pd.read_csv(rsid_file, header=None)[0].tolist()
        input_df = pd.read_csv(self.input_file)
        filtered_df = input_df[input_df['rsID'].isin(rsid_list)]
        processed_data = []
        max_bins = []

        for _, row in filtered_df.iterrows():
            pattern = row['Pattern']
            ref_allele = row['RefAllele']
            alt_allele = row['AltAllele']

            processed_pattern = self.remove_flexible_regions(pattern)
            processed_pattern = processed_pattern[:-1]
            ref_seq = re.sub(r'\[ATGC\]', ref_allele, processed_pattern, count=1)
            alt_seq = re.sub(r'\[ATGC\]', alt_allele, processed_pattern, count=1)
            ref_rc_seq = self.reverse_complement(ref_seq)
            alt_rc_seq = self.reverse_complement(alt_seq)

            ref_scores, ref_bins = self.score_sequence(ref_seq)
            alt_scores, alt_bins = self.score_sequence(alt_seq)
            ref_rc_scores, ref_rc_bins = self.score_sequence(ref_rc_seq)
            alt_rc_scores, alt_rc_bins = self.score_sequence(alt_rc_seq)

            ref_max_score = max(ref_scores, default=0)
            alt_max_score = max(alt_scores, default=0)
            ref_rc_max_score = max(ref_rc_scores, default=0)
            alt_rc_max_score = max(alt_rc_scores, default=0)

            ref_max_bin = ref_bins[ref_scores.index(ref_max_score)] if ref_scores else None
            alt_max_bin = alt_bins[alt_scores.index(alt_max_score)] if alt_scores else None
            ref_rc_max_bin = ref_rc_bins[ref_rc_scores.index(ref_rc_max_score)] if ref_rc_scores else None
            alt_rc_max_bin = alt_rc_bins[alt_rc_scores.index(alt_rc_max_score)] if alt_rc_scores else None

            max_scores_and_bins = [
                (ref_max_score, ref_max_bin),
                (alt_max_score, alt_max_bin),
                (ref_rc_max_score, ref_rc_max_bin),
                (alt_rc_max_score, alt_rc_max_bin)
            ]
            max_score, max_bin = max(max_scores_and_bins, key=lambda x: x[0])
            max_bins.append(max_bin)

            processed_data.append([
                row['rsID'], ref_allele, alt_allele, pattern, processed_pattern,
                ref_seq, alt_seq, ref_rc_seq, alt_rc_seq,
                ref_scores, alt_scores, ref_rc_scores, alt_rc_scores,
                ref_max_score, ref_max_bin,
                alt_max_score, alt_max_bin,
                ref_rc_max_score, ref_rc_max_bin,
                alt_rc_max_score, alt_rc_max_bin,
                max_score, max_bin
            ])

        output_df = pd.DataFrame(
            processed_data,
            columns=[
                'rsID', 'RefAllele', 'AltAllele', 'Original Pattern', 'Processed Pattern',
                'Ref Sequence', 'Alt Sequence', 'Ref RC Sequence', 'Alt RC Sequence',
                'Ref Scores', 'Alt Scores', 'Ref RC Scores', 'Alt RC Scores',
                'Ref Max Score', 'Ref Max Bin',
                'Alt Max Score', 'Alt Max Bin',
                'Ref RC Max Score', 'Ref RC Max Bin',
                'Alt RC Max Score', 'Alt RC Max Bin',
                'Max Score', 'Max Bin'
            ]
        )
        output_df.to_csv(output_file, index=False)
        self.logger.info(f"Processed data saved to: {output_file}")
        return max_bins

    def plot_results(self, increased_affected, increased_not_affected, decreased_affected, decreased_not_affected, output_filename='./output/GATA4/motif_affect_GATA4/GATA4_motif_analysis_plot_withoutgrid.png'):
        self.logger.info("Generating plot...")
        categories = ['Motif Dependent', 'Motif Independent']
        increased_counts = [increased_affected, increased_not_affected]
        decreased_counts = [decreased_affected, decreased_not_affected]
        fig, ax = plt.subplots(figsize=(8, 6))
        width = 0.35
        x = np.arange(len(categories))

        ax.bar(x - width/2, increased_counts, width, label='Increased rsID', color='#254B96', edgecolor='black')
        ax.bar(x + width/2, decreased_counts, width, label='Decreased rsID', color='#BF212F', edgecolor='black')
        ax.set_ylabel('Number of rsIDs', fontsize=12)
        ax.set_title('Motif Dependent vs Motif Independent by rsID', fontsize=14)
        ax.set_xticks(x)
        ax.set_xticklabels(categories, fontsize=12)
        ax.legend(title='RSID Type', fontsize=12)

        #ax.grid(True, which='both', axis='y', linestyle='--', alpha=0.7)
        ax.minorticks_on()
        #ax.grid(True, which='minor', axis='y', linestyle=':', alpha=0.5)
        plt.tight_layout()
        plt.savefig(output_filename, dpi=350)
        self.logger.info(f"Plot saved to {output_filename}")
        #plt.show()

def main(args):
    pwm_matrix_500_anr = np.array([
    [1.000000, 0.000000, 0.000000, 0.000000],
    [0.000000, 0.000000, 1.000000, 0.000000],
    [1.000000, 0.000000, 0.000000, 0.000000],
    [0.000000, 0.000000, 0.000000, 1.000000],
    [1.000000, 0.000000, 0.000000, 0.000000],
    [1.000000, 0.000000, 0.000000, 0.000000]
    ])
    
    pwm_matrix_500_zoops = np.array([
    [0.642412, 0.000000, 0.041580, 0.316008],
    [0.000000, 0.000000, 1.000000, 0.000000],
    [1.000000, 0.000000, 0.000000, 0.000000],
    [0.000000, 0.000000, 0.000000, 1.000000],
    [0.611227, 0.020790, 0.068607, 0.299376],
    [0.571726, 0.062370, 0.205821, 0.160083]
    ])
    
    pwm_matrix = np.array([
    [0.611111, 0.000000, 0.035354, 0.353535],
    [0.000000, 0.000000, 1.000000, 0.000000],
    [1.000000, 0.000000, 0.000000, 0.000000],
    [0.000000, 0.015152, 0.000000, 0.984848],
    [0.767677, 0.000000, 0.015152, 0.217172],
    [0.641414, 0.050505, 0.146465, 0.161616]
    ])
    
    pwm_matrix_200_anr = np.array([
    [0.634409, 0.000000, 0.000000, 0.365591],
    [0.000000, 0.000000, 1.000000, 0.000000],
    [1.000000, 0.000000, 0.000000, 0.000000],
    [0.000000, 0.000000, 0.000000, 1.000000],
    [1.000000, 0.000000, 0.000000, 0.000000],
    [1.000000, 0.000000, 0.000000, 0.000000]
    ]) 
    
    start_time = time.time()
    analysis = SNPMotifAnalysis(args.rsid_inc, args.rsid_dec, args.input_file, pwm_matrix)

    increased_max_bins = analysis.process_rsIDs(args.rsid_inc, args.increased_output)
    decreased_max_bins = analysis.process_rsIDs(args.rsid_dec, args.decreased_output)

    increased_affected, increased_not_affected = analysis.count_snp_impact(increased_max_bins)
    decreased_affected, decreased_not_affected = analysis.count_snp_impact(decreased_max_bins)

    analysis.plot_results(increased_affected, increased_not_affected, decreased_affected, decreased_not_affected)

    elapsed_time = time.time() - start_time
    analysis.logger.info(f"Script executed in {elapsed_time:.2f} seconds.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SNP Motif Analysis")
    parser.add_argument('--rsid_inc', default='./output/GATA4/motif_affect_GATA4/GATA4increased_rsIDs.txt', help="Path to the file containing increased rsIDs.")
    parser.add_argument('--rsid_dec', default='./output/GATA4/motif_affect_GATA4/GATA4decreased_rsIDs.txt', help="Path to the file containing decreased rsIDs.")
    parser.add_argument('--input_file', default='./output/GATA4/bound_vs_unbound/R52_38_Vs_R52_39.csv', help="Path to the input SNP data CSV file.")
    parser.add_argument('--increased_output', default='./output/GATA4/motif_affect_GATA4/processed_increased_sequences.csv', help="Path to save processed increased SNP data.")
    parser.add_argument('--decreased_output', default='./output/GATA4/motif_affect_GATA4/processed_decreased_sequences.csv', help="Path to save processed decreased SNP data.")
    args = parser.parse_args()

    main(args)
