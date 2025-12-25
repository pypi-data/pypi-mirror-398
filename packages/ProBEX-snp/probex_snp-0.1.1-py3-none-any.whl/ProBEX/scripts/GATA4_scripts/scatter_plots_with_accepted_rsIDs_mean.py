import os
import glob
import re, time, subprocess
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from adjustText import adjust_text
import warnings
import logging
import argparse

warnings.filterwarnings("ignore", category=UserWarning)
logging.basicConfig(level=logging.INFO)

"""
Author: [Shreya Sharma]
Date: [2024-12-23]

Description:
------------
	This script processes multiple CSV files containing enrichment data for SNPs (Single Nucleotide Polymorphisms)
	to generate scatter plots comparing reference vs. alternate allele enrichment. Each plot is annotated with SNP
	IDs, categorized by change (Increased, Decreased, Unchanged), and shaded to highlight the differential enrichment.

"""

class PolygonPlotter:
    def __init__(self, folder_path, plot_output_folder, table_output_folder, unbound_path, accepted_rsids_file):
        self.folder_path = folder_path
        self.plot_output_folder = plot_output_folder
        self.table_output_folder = table_output_folder
        self.unbound_path = unbound_path
        self.accepted_rsids_file = accepted_rsids_file
        self.concentration_map = {
	    "3000 nM Bound": ["R52_46_Vs_R52_47.csv", "R52_62_Vs_R52_63.csv"],
	    "2000 nM Bound": ["R52_44_Vs_R52_45.csv", "R52_60_Vs_R52_61.csv"],
	    "1500 nM Bound": ["R52_42_Vs_R52_43.csv", "R52_58_Vs_R52_59.csv"],
	    "1000 nM Bound": ["R52_40_Vs_R52_41.csv", "R52_56_Vs_R52_57.csv"],
	    "500 nM Bound": ["R52_38_Vs_R52_39.csv", "R52_54_Vs_R52_55.csv"],
	    "100 nM Bound": ["R52_36_Vs_R52_37.csv", "R52_52_Vs_R52_53.csv"],
	    "0 nM Bound": ["R52_34_Vs_R52_35.csv", "R52_50_Vs_R52_51.csv"]
	}

        self.accepted_rsids_df = pd.read_csv(self.accepted_rsids_file)
        self.accepted_rsids = self.accepted_rsids_df['rsID'].tolist()
        self.csv_files = glob.glob(os.path.join(self.folder_path, '*.csv'))

        os.makedirs(self.plot_output_folder, exist_ok=True)
        os.makedirs(self.table_output_folder, exist_ok=True)
        
        logging.basicConfig(level=logging.INFO)
        
    def plot_and_save(self, df1, df2, concentration):
    
        logging.info(f"Processing concentration: {concentration}")

        x_values = []
        y_values = []
        rs_ids = []
        
        for _, row1 in df1.iterrows():
            rs_id = row1['rsID']

            row2 = df2[df2['rsID'] == rs_id]
            
            if not row2.empty:
                ref_allele = row1['RefAllele']
                alt_allele = row1['AltAllele']
                enrich_ref_col = f'Enrich {ref_allele}'
                enrich_alt_col = f'Enrich {alt_allele}'
                
                if pd.notna(row1.get(enrich_ref_col)) and pd.notna(row2.iloc[0].get(enrich_ref_col)) and \
                    pd.notna(row1.get(enrich_alt_col)) and pd.notna(row2.iloc[0].get(enrich_alt_col)):

                    x_mean = (row1[enrich_ref_col] + row2.iloc[0][enrich_ref_col]) / 2
                    y_mean = (row1[enrich_alt_col] + row2.iloc[0][enrich_alt_col]) / 2

                    x_values.append(x_mean)
                    y_values.append(y_mean)
                    rs_ids.append(rs_id)
        
        if not x_values or not y_values:
            logging.info("No valid data points to plot.")
            return

        plot_df = pd.DataFrame({
            'Enrichment of Reference Allele': x_values,
            'Enrichment of Alternate Allele': y_values,
            'rsID': rs_ids
        })
        plot_df = plot_df.reset_index(drop=True)
        plot_df = plot_df.dropna(subset=['Enrichment of Reference Allele'])
        plot_df = plot_df.dropna(subset=['Enrichment of Alternate Allele'])

        x_min, x_max = plot_df['Enrichment of Reference Allele'].min(), plot_df['Enrichment of Reference Allele'].max()
        y_min, y_max = plot_df['Enrichment of Alternate Allele'].min(), plot_df['Enrichment of Alternate Allele'].max()

        axis_min = min(x_min, y_min)
        axis_max = max(x_max, y_max) + 10

        plt.figure(figsize=(10, 8))
        plt.scatter(plot_df['Enrichment of Reference Allele'], plot_df['Enrichment of Alternate Allele'], alpha=0.6)
        plt.xlabel('Enrichment of Reference Allele')
        plt.ylabel('Enrichment of Alternate Allele')
        plt.xlim(axis_min, axis_max)
        plt.ylim(axis_min, axis_max)
        plt.title(f'Scatter Plot of Enrichment Values: {concentration}')

        start_value = 0.10 * axis_max
        plt.plot([start_value, start_value + (axis_max - axis_min)],
                 [0, (axis_max - axis_min)],
                 linestyle='-', color='black', linewidth=1)

        plt.plot([0, (axis_max - axis_min)],
                 [start_value, start_value + (axis_max - axis_min)],
                 linestyle='-', color='black', linewidth=1)

        offset_angle = 15

        slope_above_upper = np.tan(np.deg2rad(45 + offset_angle))  
        slope_below_lower = np.tan(np.deg2rad(45 - offset_angle))  

        plt.plot([0, (1 / slope_above_upper) * (axis_max - axis_min)],
                 [start_value, start_value + (axis_max - axis_min)],
                 linestyle='--', color='black', linewidth=1)

        plt.plot([start_value, start_value + (axis_max - axis_min)],
                 [0, slope_below_lower * (axis_max - axis_min)],
                 linestyle='--', color='black', linewidth=1)

        x_fill = np.linspace(axis_min, axis_max, 100)
        y_upper = start_value + slope_above_upper * (x_fill)
        y_lower = slope_below_lower * (x_fill - start_value)
        plt.fill_between(x_fill, y_lower, y_upper, color='lightgrey', alpha=0.3)

        plot_df['Category'] = 'Unchanged'
        plot_df.loc[plot_df['Enrichment of Reference Allele'] < plot_df['Enrichment of Alternate Allele'].apply(
            lambda x: slope_below_lower * (x - start_value)), 'Category'] = 'Increased'
        plot_df.loc[plot_df['Enrichment of Alternate Allele'] < plot_df['Enrichment of Reference Allele'].apply(
            lambda x: slope_below_lower * (x - start_value)), 'Category'] = 'Decreased'

        colors = {'Increased': '#254B96', 'Decreased': '#BF212F', 'Unchanged': 'grey'}
        for category, color in colors.items():
            category_df = plot_df[plot_df['Category'] == category]
            plt.scatter(category_df['Enrichment of Reference Allele'], category_df['Enrichment of Alternate Allele'],
                        color=color, alpha=0.6, label=f'{category} ({len(category_df)})')

        texts = []
        texts_data = []
        for category in ['Increased', 'Decreased']:
            category_df = plot_df[plot_df['Category'] == category]

            for i, row in category_df.iterrows():

                texts.append(plt.text(row['Enrichment of Reference Allele'], row['Enrichment of Alternate Allele'],
                                      row['rsID'], fontsize=8, ha='right', va='bottom'))
                texts_data.append({
                    'Ref Enrichment': row['Enrichment of Reference Allele'],
                    'Alt Enrichment': row['Enrichment of Alternate Allele'],
                    'Fold Enrichment': np.log2((row['Enrichment of Alternate Allele'] + start_value) /
                                               (row['Enrichment of Reference Allele'] + start_value)),
                    'rsID': row['rsID'],
                    'Category': category
                })

        adjust_text(texts, arrowprops=dict(arrowstyle='->', color='black'))
        plt.legend()
        plot_file = os.path.join(self.plot_output_folder, f"{concentration}_scatter_plot.png")
        plt.savefig(plot_file)
        plt.close()

        table_df = pd.DataFrame(texts_data)
        table_file = os.path.join(self.table_output_folder, f"{concentration}_table.tex")
        table_df.to_latex(
            table_file,
            index=False,
            header=True,
            caption=f'Concentration: {concentration}',
            label=f'table:{concentration}')
    
    def create_latex_document(self):
        logging.info("Creating LaTeX document...")
        latex_file_path = './output/GATA4/scatter_plot_document_mean.tex'

        with open(latex_file_path, 'w') as f:
            f.write(r'''\documentclass{article}
\usepackage{graphicx}
\usepackage{geometry}
\geometry{a4paper, margin=1in}
\begin{document}
''')
            for concentration in self.concentration_map.keys():

                f.write(f"\\section*{{{concentration}}}\n")
                plot_image = os.path.join(self.plot_output_folder, f"{concentration}_scatter_plot.png")
                table_latex = f"{concentration}_table.tex"

                f.write(r'\begin{figure}[htbp]\n')
                f.write(r'\centering \includegraphics[width=0.8\textwidth]{' + plot_image + r'}\n')
                f.write(r'\caption{Scatter plot for ' + concentration + r'}\n')
                f.write(r'\end{figure}\n')

                f.write(r'\input{' + table_latex + r'}\n')
                f.write(r'\newpage\n')

            f.write(r"\end{document}")
    
        logging.info("LaTeX document created successfully.")
    
    def compile_latex(self, latex_file_path):
        logging.info("Please keep pressing Enter until pdflatex finishes processing the LaTeX document.")
        logging.info("Please keep continuing.")
        try:
            latex_dir = os.path.dirname(os.path.abspath(latex_file_path))
            base_name = os.path.basename(latex_file_path)
            subprocess.run(['pdflatex', '-interaction=nonstopmode', base_name], check=True, cwd=latex_dir)
            subprocess.run(['pdflatex', '-interaction=nonstopmode', base_name], check=True, cwd=latex_dir)
            subprocess.run(['pdflatex', latex_file_path], check=True)
            logging.info("pdflatex finished successfully.")
        except subprocess.CalledProcessError:
            logging.error("Please check the LaTeX document for errors.")  

    def process_files(self):
        start_time = time.time()
        logging.info("Starting processing...")

        for csv_file in self.csv_files:
            if any(accepted_rs in csv_file for accepted_rs in self.accepted_rsids):
                try:
                    df1 = pd.read_csv(csv_file)
                    logging.info(f"Processing file: {csv_file}")

                    for concentration, corresponding_files in self.concentration_map.items():
                        current_file = os.path.basename(csv_file)
                        if current_file in corresponding_files:
                            other_file = corresponding_files[1] if corresponding_files[0] == current_file else corresponding_files[0]
                            other_file_path = os.path.join(self.folder_path, other_file)
                            if os.path.exists(other_file_path):
                                df2 = pd.read_csv(other_file_path)
                            else:
                                logging.warning(f"Paired file not found: {other_file_path}")
                                continue
                            df1_filtered = df1[df1['rsID'].str.startswith('rs') | df1['rsID'].isin(self.accepted_rsids)]
                            df2_filtered = df2[df2['rsID'].str.startswith('rs') | df2['rsID'].isin(self.accepted_rsids)]
                            self.plot_and_save(df1_filtered, df2_filtered, concentration)
                        else:
                            logging.debug(f"File {current_file} does not belong to {concentration}")

                except Exception as e:
                    logging.error(f"Error processing file {csv_file}: {e}")
        self.create_latex_document()
        elapsed_time = time.time() - start_time
        logging.info(f"Processing completed in {elapsed_time:.2f} seconds.")

if __name__ == '__main__':
    start_time = time.time()
    parser = argparse.ArgumentParser(description="Plot scatter plots of enrichment values for SNPs.")
    parser.add_argument('--folder_path', type=str, default='./output/GATA4/bound_vs_unbound/', help="Folder containing the CSV files.")
    parser.add_argument('--plot_output_folder', type=str, default='./output/GATA4/plots_mean_scatter/', help="Folder to save the scatter plots.")
    parser.add_argument('--table_output_folder', type=str, default='./output/GATA4/tables_mean_scatter/', help="Folder to save the table outputs.")
    parser.add_argument('--unbound_path',  type=str, default='./output/GATA4/CarriedForward/', help="Folder containing the unbound files.")
    parser.add_argument('--accepted_rsids_file', type=str, default='./output/GATA4_accepted_rsIDs.csv', help="CSV file with accepted rsIDs.")

    args = parser.parse_args()

    plotter = PolygonPlotter(args.folder_path, args.plot_output_folder, args.table_output_folder,
                            args.unbound_path, args.accepted_rsids_file)

    for concentration, csv_files in plotter.concentration_map.items():

        for i in range(len(csv_files)):
            for j in range(i + 1, len(csv_files)):
                file1 = os.path.join(args.folder_path, csv_files[i])
                file2 = os.path.join(args.folder_path, csv_files[j])
            
                df1 = pd.read_csv(file1)
                df2 = pd.read_csv(file2)
                plotter.plot_and_save(df1, df2, concentration)
    plotter.create_latex_document()
    latex_file_path = './output/GATA4/scatter_plot_document_mean.tex'
    plotter.compile_latex(latex_file_path)
    end_time = time.time()
    total_time = end_time - start_time
    print(f"Total time taken: {total_time:.2f} seconds")