import pandas as pd
import time, logging
from datetime import datetime

"""
Author: [Shreya Sharma]
Date: [Dec 26, 2024]
Description: Script to extract and save rsID values from an Excel file based on filter conditions.

	This script reads the input Excel file 'extracted_rsIDs.xlsx', filters the rows based on the 
	'Filter(H,I)' column values (1 for accepted and 0 for discarded), and then extracts the 
	'rsID' column for each filtered subset. The extracted rsIDs are saved into separate CSV 
	files: 'accepted.csv' for accepted rsIDs and 'discarded.csv' for discarded rsIDs.
"""
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

def extract_and_save_rsids(input_file: str, accepted_file: str, discarded_file: str):
    try:
        logging.info(f"Started extraction process from {input_file}")
        df = pd.read_excel(input_file)
        logging.info(f"Loaded file: {input_file}")
        if "Filter(H,I)" not in df.columns or "rsID" not in df.columns:
            logging.error("Required columns ('Filter(H,I)', 'rsID') are missing in the input file")
            return
        accepted_df = df[df["Filter(H,I)"] == 1]
        discarded_df = df[df["Filter(H,I)"] == 0]
        logging.info(f"Filtered accepted: {len(accepted_df)} rsIDs, discarded: {len(discarded_df)} rsIDs")
        accepted_df["rsID"].to_csv(accepted_file, index=False)
        discarded_df["rsID"].to_csv(discarded_file, index=False)
        logging.info(f"Saved accepted rsIDs to {accepted_file} and discarded rsIDs to {discarded_file}")
        logging.info("Extraction process completed successfully")

    except Exception as e:
        logging.error(f"An error occurred during the extraction process: {e}")

if __name__ == "__main__":
    start_time = datetime.now()
    logging.info(f"Script started at {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    input_file = './output/TBX5/extracted_rsIDs.xlsx'
    accepted_file = './output/TBX5_accepted_rsIDs.csv'
    discarded_file = './output/TBX5_discarded_rsIDs.csv'
    
    extract_and_save_rsids(input_file, accepted_file, discarded_file)
    
    end_time = datetime.now()
    logging.info(f"Script finished at {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    logging.info(f"Total execution time: {end_time - start_time}")