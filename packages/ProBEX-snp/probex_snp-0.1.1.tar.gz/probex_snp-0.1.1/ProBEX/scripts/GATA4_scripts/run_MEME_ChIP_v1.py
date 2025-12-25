import os
import subprocess
import logging
import time

"""
===============================================================================
MEME Logo Prediction Script
===============================================================================
This script is designed to process input FASTA files for motif discovery 
and logo prediction using the MEME Suite. The script reads FASTA sequences, 
performs necessary preprocessing, and predicts motif logos based on the 
given input sequences. The MEME tool is used to analyze DNA sequence motifs 
to find conserved patterns across multiple sequences. The output is a 
graphical representation (logo) of the identified motif.

Author: [Shreya Sharma]
Date: [Aug 9, 2024]
===============================================================================
"""

class MemeChipProcessor:
    def __init__(self, fasta_folder_path, output_base_path):
        self.fasta_folder_path = fasta_folder_path
        self.output_base_path = output_base_path
        os.makedirs(self.output_base_path, exist_ok=True)
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    def process_fasta_files(self): 
        logging.info("Starting MEME-ChIP processing...")
        
        for fasta_file in os.listdir(self.fasta_folder_path):
            if fasta_file.endswith(".fa"):
                fasta_file_path = os.path.join(self.fasta_folder_path, fasta_file)

                output_dir = os.path.join(self.output_base_path, os.path.splitext(fasta_file)[0])
                os.makedirs(output_dir, exist_ok=True)
                
                self.run_meme_chip(fasta_file_path, output_dir)

    def run_meme_chip(self, fasta_file_path, output_dir):
        try:
            logging.info("  ")
            logging.info("=============================================================================================")
            logging.info(f"Running MEME-ChIP for file: {fasta_file_path}")
            logging.info("=============================================================================================")
            logging.info("  ")
            subprocess.run(
                ['/home/dell/meme/bin/meme-chip', '-meme-mod', 'anr', '-minw', '5', '-maxw', '6', '-meme-nmotifs', '5', fasta_file_path, '-oc', output_dir],
                check=True
            )
            logging.info(f"MEME-ChIP completed for {fasta_file_path}, results saved to {output_dir}")
        except subprocess.CalledProcessError as e:
            logging.error(f"Error occurred while running MEME-ChIP for {fasta_file_path}: {e}")
        except Exception as e:
            logging.error(f"Unexpected error occurred: {e}")

if __name__ == "__main__":
    start_time = time.time()
    fasta_folder_path = "./output/GATA4/bound_vs_unbound/GATA4_fasta_files/" 
    output_base_path = "./output/GATA4/bound_vs_unbound/meme-output_MEME/"
    
    #fasta_folder_path = "../motif_affect_GATA4/MEME/" 
    #output_base_path = "../motif_affect_GATA4/MEME/meme-output_MEME/"
    os.makedirs(output_base_path, exist_ok=True)

    meme_processor = MemeChipProcessor(fasta_folder_path, output_base_path)
    meme_processor.process_fasta_files()
    elapsed_time = time.time() - start_time
    logging.info(f"Processing completed in {elapsed_time:.2f} seconds.")
