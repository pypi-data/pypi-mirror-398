import os
import pandas as pd
import re
import argparse
import time, logging
from datetime import datetime

"""
Description:
	This Python script processes .tex files containing tables with genetic data,
	extracting relevant information on rsIDs based on their fold enrichment values.
	It reads the content of the files, cleans up LaTeX formatting, and identifies
	rsIDs with fold enrichment values greater than 1 (increased) or less than -1
	(decreased). The extracted data is then saved into CSV files, separating
	increased and decreased rsIDs for further analysis. The script also logs its
	progress and any errors encountered during processing.

Author: [Shreya Sharma]
Date: [January 17, 2025]
"""

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)

def extract_table_from_tex(filepath):
    """Extracts the table from a .tex file and returns a DataFrame."""
    logging.info(f"Processing file: {filepath}")
    with open(filepath, 'r') as file:
        content = file.read()
    table_pattern = r'\\midrule(.*?)\\bottomrule'
    match = re.search(table_pattern, content, re.DOTALL)
    
    if match:
        table_content = match.group(1)
        table_content = re.sub(r'\\[a-zA-Z]*', '', table_content)  # Remove LaTeX commands
        table_content = re.sub(r'\n+', '\n', table_content)  # Clean up newlines
        rows = [line.strip().split('&') for line in table_content.strip().split('\n')]
        data = {
            'Ref Enrichment': [row[0].strip() for row in rows],
            'Alt Enrichment': [row[1].strip() for row in rows],
            'Fold Enrichment': [row[2].strip() for row in rows],
            'Total Count in Unbound': [row[3].strip() for row in rows],
            'rsID': [row[4].strip() for row in rows],
            'Category': [row[5].strip() for row in rows],
        }
        logging.info(f"Extracted {len(data['rsID'])} rows from the table.")
        return pd.DataFrame(data)
    else:
        raise ValueError(f"No table found in {filepath}")

def extract_rsids_from_df(df):
    """Extract rsIDs where Fold Enrichment > 1 and Fold Enrichment < 1."""
    logging.info("Extracting rsIDs with Fold Enrichment > 1 and < 1.")
    df['Fold Enrichment'] = pd.to_numeric(df['Fold Enrichment'], errors='coerce')
    df = df.dropna(subset=['Fold Enrichment'])
    increased_df = df[df['Fold Enrichment'] >= 1][['rsID', 'Fold Enrichment']]
    decreased_df = df[df['Fold Enrichment'] <= -1][['rsID', 'Fold Enrichment']]
    
    logging.info(f"Found {len(increased_df)} increased rsIDs and {len(decreased_df)} decreased rsIDs.")
    
    return increased_df, decreased_df

def process_tex_files(input_dir, output_dir):
    """Processes all .tex files in the input directory and saves the results."""
    logging.info(f"Started processing files in directory: {input_dir}")
    
    for filename in os.listdir(input_dir):
        if filename.endswith(".tex"):
            filepath = os.path.join(input_dir, filename)
            try:
                df = extract_table_from_tex(filepath)
                increased_df, decreased_df = extract_rsids_from_df(df)
                
                filename = filename.replace("_table.tex", "")
                output_increased = os.path.join(output_dir, f"{filename}_increased.csv")
                output_decreased = os.path.join(output_dir, f"{filename}_decreased.csv")
                
                increased_df.to_csv(output_increased, index=False, header=True)
                decreased_df.to_csv(output_decreased, index=False, header=True)
                
                logging.info(f"Saved increased and decreased rsIDs for {filename}.")
                
            except Exception as e:
                logging.error(f"Error processing {filename}: {e}")

def main():
    parser = argparse.ArgumentParser(description="Extract rsIDs based on Fold Enrichment from .tex files.")
    parser.add_argument("--input_dir", default="./output/GATA4/tables_tex_scatter_plots", help="Directory containing .tex files.")
    parser.add_argument("--output_dir", default="./output/GATA4/scatter_plots_tables", help="Directory to save the output files.")
    args = parser.parse_args()
    
    os.makedirs(args.output_dir, exist_ok=True)
    process_tex_files(args.input_dir, args.output_dir)

if __name__ == "__main__":
    start_time = time.time()
    logging.info(f"Script started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    main()
    logging.info(f"Script finished at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    end_time = time.time()
    total_time = end_time - start_time
    print(f"Total time taken: {total_time:.2f} seconds")