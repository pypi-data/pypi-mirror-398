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
    parser.add_argument('-i', '--input_folder', type=str, default='./output/TBX5/scatter_plots_tables', help="Path to input folder containing CSV files.")
    parser.add_argument('-o', '--output_heatmap', type=str, default="./output/TBX5/heatmap_data_mean_scatter.png", help="Path to save the output heatmap image.")
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
        cmap = sns.diverging_palette(220, 20, as_cmap=True)
        colors = cmap(np.linspace(0, 1, cmap.N))
        reversed_cmap = ListedColormap(colors[::-1])
        
        plt.figure(figsize=(12, 15))
        sns.set(font_scale=0.7)
        sns.heatmap(heatmap_data, cmap=reversed_cmap, center=0, annot=False, linewidths=0.5, cbar_kws={"label": "Fold Enrichment"})
        plt.title('Fold Change Heatmap Across Concentrations')
        plt.xlabel('Concentration')
        plt.ylabel('rsID')
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
        "R52_78_Vs_R52_79": "3000 nM",
        "R52_76_Vs_R52_77": "2000 nM",
        "R52_74_Vs_R52_75": "1500 nM",
        "R52_72_Vs_R52_73": "1000 nM",
        "R52_70_Vs_R52_71": "500 nM", 
        "R52_68_Vs_R52_69": "100 nM",
        "R52_66_Vs_R52_67": "0 nM",   
        "R52_82_Vs_R52_83": "0 nM",
        "R52_84_Vs_R52_85": "100 nM", 
        "R52_86_Vs_R52_87": "500 nM", 
        "R52_88_Vs_R52_89": "1000 nM",
        "R52_90_Vs_R52_91": "1500 nM",
        "R52_92_Vs_R52_93": "2000 nM", 
        "R52_94_Vs_R52_95": "3000 nM"
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