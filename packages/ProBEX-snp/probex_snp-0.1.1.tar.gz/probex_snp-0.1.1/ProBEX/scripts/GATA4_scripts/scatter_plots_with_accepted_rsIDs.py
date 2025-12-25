import os
import glob
import re
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from adjustText import adjust_text
import math
import logging
import subprocess
import time
import argparse
import warnings
from matplotlib import MatplotlibDeprecationWarning
warnings.filterwarnings("ignore", category=MatplotlibDeprecationWarning)

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
            "R52_46_Vs_R52_47.csv": "3000 nM Bound",
            "R52_44_Vs_R52_45.csv": "2000 nM Bound",
            "R52_42_Vs_R52_43.csv": "1500 nM Bound",
            "R52_40_Vs_R52_41.csv": "1000 nM Bound",
            "R52_38_Vs_R52_39.csv": "500 nM Bound",
            "R52_36_Vs_R52_37.csv": "100 nM Bound",
            "R52_34_Vs_R52_35.csv": "0 nM Bound",
            "R52_50_Vs_R52_51.csv": "0 nM Bound_2",
            "R52_52_Vs_R52_53.csv": "100 nM Bound_2",
            "R52_54_Vs_R52_55.csv": "500 nM Bound_2",
            "R52_56_Vs_R52_57.csv": "1000 nM Bound_2",
            "R52_58_Vs_R52_59.csv": "1500 nM Bound_2",
            "R52_60_Vs_R52_61.csv": "2000 nM Bound_2",
            "R52_62_Vs_R52_63.csv": "3000 nM Bound_2"
        }
        self.accepted_rsids_df = pd.read_csv(self.accepted_rsids_file)
        self.accepted_rsids = self.accepted_rsids_df['rsID'].tolist()
        self.csv_files = glob.glob(os.path.join(self.folder_path, '*.csv'))

        os.makedirs(self.plot_output_folder, exist_ok=True)
        os.makedirs(self.table_output_folder, exist_ok=True)

        logging.basicConfig(level=logging.INFO)

    def extract_number(self, filename):
        match = re.search(r'R52_(\d+)', filename)
        return int(match.group(1)) if match else float('inf')

    def plot_and_save(self, df, csv_file):
        x_values = []
        y_values = []
        rs_ids = []
        for _, row in df.iterrows():
            ref_allele = row['RefAllele']
            alt_allele = row['AltAllele']
            enrich_ref_col = f'Enrich {ref_allele}'
            enrich_alt_col = f'Enrich {alt_allele}'

            if enrich_ref_col in df.columns and enrich_alt_col in df.columns:
                x_values.append(row[enrich_ref_col])
                y_values.append(row[enrich_alt_col])
                rs_ids.append(row['rsID'])

        plot_df = pd.DataFrame({
            'Enrichment of Reference Allele': x_values,
            'Enrichment of Alternate Allele': y_values,
            'rsID': rs_ids
        })

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
        #plt.grid(True)
        plt.title(f'Scatter Plot of Enrichment Values: {os.path.basename(csv_file)}')

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

                unbound_file = csv_file.split('_Vs_')[1]
                unbound_df = pd.read_csv(os.path.join(self.unbound_path, unbound_file))
                matching_row = unbound_df[unbound_df['rsID'] == row['rsID']]
                if not matching_row.empty:
                    total_count_unbound = matching_row['Total Count'].values[0]
                else:
                    total_count_unbound = np.nan

                texts.append(plt.text(row['Enrichment of Reference Allele'], row['Enrichment of Alternate Allele'],
                                      row['rsID'], fontsize=8, ha='right', va='bottom'))
                texts_data.append({
                    'Ref Enrichment': row['Enrichment of Reference Allele'],
                    'Alt Enrichment': row['Enrichment of Alternate Allele'],
                    'Fold Enrichment': np.log2((row['Enrichment of Alternate Allele'] + start_value) /
                                               (row['Enrichment of Reference Allele'] + start_value)),
                    'Total Count in Unbound': total_count_unbound,
                    'rsID': row['rsID'],
                    'Category': category
                })

        adjust_text(texts, arrowprops=dict(arrowstyle='->', color='black'))
        plt.legend()
        plot_file = os.path.join(self.plot_output_folder, f"{os.path.basename(csv_file).replace('.csv', '')}_scatter_plot.png")
        plt.savefig(plot_file)
        plt.close()

        table_df = pd.DataFrame(texts_data)
        concentration = self.concentration_map.get(os.path.basename(csv_file), "Unknown Concentration")
        replicate = "Replicate: 01" if not concentration.endswith("_2") else "Replicate: 02"
        table_file = os.path.join(self.table_output_folder, f"{os.path.basename(csv_file).replace('.csv', '')}_table.tex")
        csv_file_escaped = os.path.basename(csv_file).replace('_', r'\_')
        table_df.to_latex(
            table_file,
            index=False,
            header=True,
            caption=f'Table for {csv_file_escaped}\nConcentration: {concentration}, {replicate}',
            label=f'table:{csv_file_escaped}')

    def create_latex_document(self):
        logging.info("Creating LaTeX document...")
        
        output_dir = os.path.abspath(os.path.join(self.plot_output_folder, '..', 'scatter_plot_output'))
        os.makedirs(output_dir, exist_ok=True)

        latex_file_path = os.path.join(output_dir, 'scatter_plot_document.tex')

        with open(latex_file_path, 'w') as f:
            f.write(r'''\documentclass{article}
\usepackage{graphicx}
\usepackage{geometry}
\geometry{a4paper, margin=1in}
\begin{document}
''')

            for csv_file in sorted(self.csv_files, key=self.extract_number):
                base_name = os.path.basename(csv_file).replace('.csv', '')
                plot_path = os.path.join(self.plot_output_folder, f"{base_name}_scatter_plot.png")
                table_path = os.path.join(self.table_output_folder, f"{base_name}_table.tex")

                # Make relative paths from LaTeX file
                plot_rel = os.path.relpath(plot_path, output_dir)
                table_rel = os.path.relpath(table_path, output_dir)
                
                base_name_escaped = base_name.replace('_', r'\_')
                concentration = self.concentration_map.get(os.path.basename(csv_file), "Unknown Concentration")
                replicate = "Replicate: 01" if not concentration.endswith("_2") else "Replicate: 02"

                f.write(r'\clearpage' + '\n')
                f.write(f'\\begin{{center}}\\section*{{Plot and Table for {base_name_escaped}}} \\hspace{{1em}}Concentration: {concentration}, {replicate}\\end{{center}}\n')
                f.write(r'\vspace{1em}' + '\n')
                f.write(f'\\begin{{figure}}[h!]\n')
                f.write(f'\\centering\n')
                f.write(f'\\includegraphics[width=\\textwidth]{{{plot_file}}}\n')
                f.write(f'\\caption{{Scatter plot for {base_name_escaped}.}}\n')
                f.write(f'\\end{{figure}}\n')
                f.write(f'\\input{{{table_file}}}\n')
                f.write(r'\clearpage' + '\n')
            f.write(r'''\end{document}''')

        logging.info(f'LaTeX document has been created at {latex_file_path}')
        self.compile_latex(latex_file_path)
    
    def compile_latex(self, latex_file_path):
        latex_dir = os.path.dirname(latex_file_path)
        latex_filename = os.path.basename(latex_file_path)
        try:
            subprocess.run(['pdflatex', '-interaction=nonstopmode', latex_filename], check=True, cwd=latex_dir)
            subprocess.run(['pdflatex', '-interaction=nonstopmode', latex_filename], check=True, cwd=latex_dir)
            logging.info("pdflatex finished successfully.")
        except subprocess.CalledProcessError:
            logging.error("Please check the LaTeX document for errors.")  

    def process(self):
        start_time = time.time()

        for csv_file in self.csv_files:
            df = pd.read_csv(csv_file)
            df['rsID'] = df['rsID'].fillna('')
            df_filtered = df[df['rsID'].str.startswith('rs') | df['rsID'].isin(self.accepted_rsids)]

            self.plot_and_save(df_filtered, csv_file)

        self.create_latex_document()
        elapsed_time = time.time() - start_time
        logging.info(f"Processing completed in {elapsed_time:.2f} seconds.")

if __name__ == '__main__':
    start_time = time.time()
    parser = argparse.ArgumentParser(description="Plot scatter plots of enrichment values for SNPs.")
    parser.add_argument('--folder_path', type=str, default='./output/GATA4/bound_vs_unbound/', help="Folder containing the CSV files.")
    parser.add_argument('--plot_output_folder', type=str, default='./output/GATA4/scatter_plots/', help="Folder to save the scatter plots.")
    parser.add_argument('--table_output_folder', type=str, default='./output/GATA4/tables_tex_scatter_plots/', help="Folder to save the table outputs.")
    parser.add_argument('--unbound_path',  type=str, default='./output/GATA4/CarriedForward/', help="Folder containing the unbound files.")
    parser.add_argument('--accepted_rsids_file', type=str, default='./output/GATA4_accepted_rsIDs.csv', help="CSV file with accepted rsIDs.")

    args = parser.parse_args()

    plotter = PolygonPlotter(args.folder_path, args.plot_output_folder, args.table_output_folder,
                            args.unbound_path, args.accepted_rsids_file)

    for csv_file in plotter.csv_files:
        df = pd.read_csv(csv_file)
        plotter.plot_and_save(df, csv_file)

    plotter.create_latex_document()
    end_time = time.time()
    total_time = end_time - start_time
    print(f"Total time taken: {total_time:.2f} seconds")
