import os
import glob
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
import numpy as np
import logging
import time
import argparse

"""
Author: [Shreya Sharma]
Date: [2024-12-18]

Description:
	This script generates a heatmap of Fold Enrichments across different concentrations for a set of SNP data.
	The script loads data from CSV files, processes the Fold Enrichment values for different concentrations, 
	and creates a heatmap to visualize the Fold Enrichments across concentrations.

	Usage:
	python generate_heatmap.py -i <input_folder> -o <output_heatmap>

	Arguments:
	    -i, --input_folder    Path to the folder containing CSV files. Default is '../volcano_plots_tables'.
	    -o, --output_heatmap  Path to save the generated heatmap image. Default is '../heatmap_data_mean_volcano.png'.

"""

def setup_logging():
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(levelname)s - %(message)s')
    
def parse_arguments():
    parser = argparse.ArgumentParser(description="Generate a heatmap for Fold Enrichments across concentrations.")
    parser.add_argument('-i', '--input_folder', type=str, default='./output/NKX25/scatter_plots_tables', help="Path to input folder containing CSV files.")
    parser.add_argument('-o', '--output_heatmap', type=str, default="./output/NKX25/heatmap_data_mean_scatter.png", help="Path to save the output heatmap image.")
    return parser.parse_args()

def load_data(input_folder, concentration_map):
    logging.info("Loading data from CSV files...")
    csv_files = glob.glob(os.path.join(input_folder, '*.csv'))
    if not csv_files:
        logging.warning("No CSV files found in the input folder.")
    combined_data = []
    
    for file in csv_files:
        print(f"Processing file: {file}")  # Check the files being processed
        file_name = os.path.basename(file).replace('_increased.csv', '').replace('_decreased.csv', '')
        concentration = concentration_map.get(file_name, None)
        if concentration:
            df = pd.read_csv(file)
            if 'rsID' in df.columns and 'Fold Enrichment' in df.columns:
                temp_df = df[['rsID', 'Fold Enrichment']].copy()
                temp_df['Concentration'] = concentration
                combined_data.append(temp_df)
            else:
                logging.warning(f"Columns 'rsID' or 'Fold Enrichment' not found in {file}")
        else:
            logging.warning(f"Concentration not found for {file_name}")
    
    if not combined_data:
        logging.warning("No data to concatenate.")
    
    return pd.concat(combined_data, ignore_index=True) if combined_data else pd.DataFrame()

def generate_heatmap(data, concentration_order, output_heatmap):
    logging.info("Generating heatmap...")
    if 'Fold Enrichment' not in data.columns:
        logging.error("'Fold Enrichment' column is missing in the data. Cannot generate heatmap.")
        return

    try:
        heatmap_data = data.pivot_table(index='rsID',
                                        columns='Concentration',
                                        values='Fold Enrichment',
                                        aggfunc='mean').fillna(0)

        heatmap_data = heatmap_data[concentration_order]
        heatmap_data = heatmap_data.loc[heatmap_data.mean(axis=1).sort_values(ascending=False).index]
        #cmap = sns.diverging_palette(220, 20, as_cmap=True)
        #colors = cmap(np.linspace(0, 1, cmap.N))
        #reversed_cmap = ListedColormap(colors[::-1])
        
        plt.figure(figsize=(12, 15))
        sns.set(font_scale=0.7)
        ax = sns.heatmap(heatmap_data, cmap='coolwarm', center=0, annot=False, linewidths=0.5, cbar_kws={"label": "Fold Enrichment"})
        colorbar = ax.collections[0].colorbar
        colorbar.ax.tick_params(labelsize=18)
        colorbar.set_label("Fold Enrichment", fontsize=18)
        plt.title('Fold Change Heatmap Across Concentrations', fontsize=18)
        plt.xlabel('Concentration', fontsize=18)
        plt.ylabel('rsID', fontsize=18)
        plt.tight_layout()
        plt.savefig(output_heatmap, dpi=300)
        plt.close()
        logging.info(f"Heatmap saved to {output_heatmap}")
    except Exception as e:
        logging.error(f"Error generating heatmap: {e}")

def main():
    start_time = time.time()
    setup_logging()
    args = parse_arguments()
    concentration_map = {
	    "R52_01_Vs_R52_02": "0 nM",
	    "R52_03_Vs_R52_04": "100 nM",
	    "R52_05_Vs_R52_06": "500 nM",
	    "R52_07_Vs_R52_08": "1000 nM",
	    "R52_09_Vs_R52_10": "1500 nM",
	    "R52_11_Vs_R52_12": "2000 nM",
	    "R52_13_Vs_R52_14": "3000 nM",
	    "R52_18_Vs_R52_19": "0 nM",
	    "R52_20_Vs_R52_21": "100 nM",
	    "R52_22_Vs_R52_23": "500 nM",
	    "R52_24_Vs_R52_25": "1000 nM",
	    "R52_26_Vs_R52_27": "1500 nM",
	    "R52_28_Vs_R52_29": "2000 nM",
	    "R52_30_Vs_R52_31": "3000 nM"
	}

    data = load_data(args.input_folder, concentration_map)
    if data.empty:
        logging.error("No valid data to generate heatmap.")
        return
    
    concentration_order = ['100 nM', '500 nM', '1000 nM', '1500 nM', '2000 nM', '3000 nM']
    generate_heatmap(data, concentration_order, args.output_heatmap)
    execution_time = time.time() - start_time
    logging.info(f"Execution time: {execution_time:.2f} seconds")

if __name__ == '__main__':
    main()