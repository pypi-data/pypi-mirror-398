import os
import pandas as pd
import time
import logging
import argparse

"""
Author: [Shreya Sharma]
Date:[2024-12-23]
Description: 
	This script processes .tex files in a specified directory to extract rsIDs associated with 
	Increased and Decreased categories for a particular transcription factor (TF). It collects the 
	rsIDs and writes them into separate text files: one for Increased rsIDs and one for Decreased rsIDs.
"""

DEFAULT_INPUT_DIR = "./output/TBX5/scatter_plots_tables"
DEFAULT_OUTPUT_DIR = "./output/TBX5/intersected_rsids_based_scatterPlot"
CONCENTRATION_MAP = {
    "3000 nM Bound": ("R52_78_Vs_R52_79", "R52_94_Vs_R52_95"),
    "2000 nM Bound": ("R52_76_Vs_R52_77", "R52_92_Vs_R52_93"),
    "1500 nM Bound": ("R52_74_Vs_R52_75", "R52_90_Vs_R52_91"),
    "1000 nM Bound": ("R52_72_Vs_R52_73", "R52_88_Vs_R52_89"),
    "500 nM Bound": ("R52_70_Vs_R52_71", "R52_86_Vs_R52_87"),
    "100 nM Bound": ("R52_68_Vs_R52_69", "R52_84_Vs_R52_85")
}

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()

def extract_rsids_from_csv(file_path, rsid_column='rsID'):
    """
    Extracts rsIDs from a given CSV file.
    
    Parameters:
    - file_path (str): Path to the CSV file.
    - rsid_column (str): Name of the column containing rsIDs.
    
    Returns:
    - Set of rsIDs.
    """
    try:
        df = pd.read_csv(file_path)
        if rsid_column in df.columns:
            rsids = set(df[rsid_column].dropna().astype(str).str.strip())
            return rsids
        else:
            rsids = set()
            for item in df.values.flatten():
                if isinstance(item, str) and item.startswith('rs'):
                    rsids.add(item.strip())
            return rsids
    except Exception as e:
        logger.error(f"Error reading {file_path}: {e}")
        return set()

def main(input_dir=DEFAULT_INPUT_DIR, output_dir=DEFAULT_OUTPUT_DIR):
    start_time = time.time()
    os.makedirs(output_dir, exist_ok=True)
    for concentration, (comp1, comp2) in CONCENTRATION_MAP.items():
        logger.info(f"Processing Concentration: {concentration}")
        
        comp1_increased_file = os.path.join(input_dir, f"{comp1}_increased.csv")
        comp1_decreased_file = os.path.join(input_dir, f"{comp1}_decreased.csv")
        comp2_increased_file = os.path.join(input_dir, f"{comp2}_increased.csv")
        comp2_decreased_file = os.path.join(input_dir, f"{comp2}_decreased.csv")
        missing_files = [file for file in [comp1_increased_file, comp1_decreased_file, comp2_increased_file, comp2_decreased_file] if not os.path.isfile(file)]
        
        if missing_files:
            logger.warning(f"  Missing files for concentration '{concentration}':")
            for mf in missing_files:
                logger.warning(f"    - {mf}")
            logger.info("  Skipping this concentration due to missing files.\n")
            continue
        comp1_increased_rsids = extract_rsids_from_csv(comp1_increased_file)
        comp1_decreased_rsids = extract_rsids_from_csv(comp1_decreased_file)
        comp2_increased_rsids = extract_rsids_from_csv(comp2_increased_file)
        comp2_decreased_rsids = extract_rsids_from_csv(comp2_decreased_file)
        common_increased = comp1_increased_rsids.intersection(comp2_increased_rsids)
        common_decreased = comp1_decreased_rsids.intersection(comp2_decreased_rsids)
        concentration_safe = concentration.replace(" ", "_").replace("/", "_")  # Replace spaces and slashes
        concentration_dir = os.path.join(output_dir, concentration_safe)
        os.makedirs(concentration_dir, exist_ok=True)
        
        increased_output_file = os.path.join(concentration_dir, "common_increased_rsIDs.txt")
        decreased_output_file = os.path.join(concentration_dir, "common_decreased_rsIDs.txt")
        with open(increased_output_file, "w") as f:
            for rsid in sorted(common_increased):
                f.write(f"{rsid}\n")
        logger.info(f"  Saved common increased rsIDs to {increased_output_file}")
        
        with open(decreased_output_file, "w") as f:
            for rsid in sorted(common_decreased):
                f.write(f"{rsid}\n")
        logger.info(f"  Saved common decreased rsIDs to {decreased_output_file}\n")
    execution_time = time.time() - start_time
    logger.info(f"All results have been saved to the '{output_dir}' directory.")
    logger.info(f"Execution Time: {execution_time:.2f} seconds.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process concentration files and extract common rsIDs.")
    parser.add_argument('-i', '--input', type=str, default=DEFAULT_INPUT_DIR, help='Input directory (default: current directory)')
    parser.add_argument('-o', '--output', type=str, default=DEFAULT_OUTPUT_DIR, help='Output directory (default: "intersected_rsids_based_scatterPlot")')
    
    args = parser.parse_args()
    main(input_dir=args.input, output_dir=args.output)