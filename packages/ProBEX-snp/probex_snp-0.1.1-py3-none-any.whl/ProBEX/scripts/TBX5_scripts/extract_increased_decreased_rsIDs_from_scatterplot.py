import os
import re
import logging
import time

"""
Author: [Shreya Sharma]
Date:[2024-12-23]
Description: 
	This script processes .tex files in a specified directory to extract rsIDs associated with 
	Increased and Decreased categories for a particular transcription factor (TF). It collects the 
	rsIDs and writes them into separate text files: one for Increased rsIDs and one for Decreased rsIDs.

	Example:
	    tex_dir = "../tables_tex_scatter_plots"
	    increased_file = "../TBX5increased_rsIDs.txt"
	    decreased_file = "../TBX54decreased_rsIDs.txt"
"""

class RsIDExtractor:
    def __init__(self, tex_dir, increased_file, decreased_file):
        self.tex_dir = tex_dir
        self.increased_file = increased_file
        self.decreased_file = decreased_file
        self.increased_rsIDs = set()
        self.decreased_rsIDs = set()
        self.pattern = re.compile(r"rs\d+\s+&\s+(Increased|Decreased)")
        self.logger = self.setup_logger()

    def setup_logger(self):
        logger = logging.getLogger('RsIDExtractor')
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        return logger

    def extract_rsIDs(self):
        start_time = time.time()
        self.logger.info("Starting rsID extraction process...")
        for tex_file in os.listdir(self.tex_dir):
            if tex_file.endswith(".tex"):
                self.logger.info(f"Processing file: {tex_file}")
                self.process_tex_file(tex_file)
                
        self.save_rsIDs()

        end_time = time.time()
        elapsed_time = end_time - start_time
        self.logger.info(f"rsID extraction process completed in {elapsed_time:.2f} seconds.")

    def process_tex_file(self, tex_file):
        try:
            with open(os.path.join(self.tex_dir, tex_file), 'r') as file:
                for line in file:
                    match = self.pattern.search(line)
                    if match:
                        rsID = re.search(r"rs\d+", line).group(0)
                        category = match.group(1)
                        if category == "Increased":
                            self.increased_rsIDs.add(rsID)
                        elif category == "Decreased":
                            self.decreased_rsIDs.add(rsID)
        except Exception as e:
            self.logger.error(f"Error processing file {tex_file}: {e}")

    def save_rsIDs(self):
        try:
            with open(self.increased_file, 'w') as f_inc, open(self.decreased_file, 'w') as f_dec:
                f_inc.write("\n".join(sorted(self.increased_rsIDs)))
                f_dec.write("\n".join(sorted(self.decreased_rsIDs)))
            self.logger.info("Increased and Decreased rsIDs have been written to files.")
        except Exception as e:
            self.logger.error(f"Error saving rsIDs to files: {e}")

if __name__ == "__main__":
    tex_dir = "../tables_tex_scatter_plots"
    increased_file = "../TBX5increased_rsIDs.txt"
    decreased_file = "../TBX5decreased_rsIDs.txt"

    extractor = RsIDExtractor(tex_dir, increased_file, decreased_file)
    extractor.extract_rsIDs()
