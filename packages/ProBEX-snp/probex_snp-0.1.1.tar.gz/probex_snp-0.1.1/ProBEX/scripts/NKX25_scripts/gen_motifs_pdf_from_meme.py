import os
import subprocess
import re
from pylatex import Document, Section, Command, Package, NewPage, NoEscape, Figure, Tabular
import time

"""
This Python script automates the generation of a PDF report from MEME motif analysis output, 
specifically for NKX25, but can be easily adapted for other transcription factors (TFs).
The script extracts motif data such as motif name, width, number of sites, and E-value 
from MEME output text files and organizes this information into a LaTeX document.
The LaTeX document includes motif logos and their associated metadata in a table format.
Finally, the script compiles the LaTeX document into a PDF report.
The concentration map can be adjusted to accommodate different TFs and experimental conditions.

Author: [Shreya Sharma]
Date: [02 Jan, 2015]
"""

class MemeToPdf:
    def __init__(self, base_path, output_pdf, concentration_map):
        self.base_path = base_path
        os.makedirs(self.base_path, exist_ok=True)
        self.output_pdf = output_pdf
        self.concentration_map = concentration_map
        self.doc = Document()
        self.doc.preamble.append(Package('geometry', options=['margin=1in']))
        self.doc.preamble.append(Package('graphicx'))
        self.doc.preamble.append(Package('array'))
        self.doc.preamble.append(Command('title', 'Logos and Data'))
        self.doc.preamble.append(Command('author', 'Automated Report'))
        self.doc.preamble.append(Command('date', NoEscape(r'\today')))
        self.pattern = re.compile(
            r'MOTIF\s+(\S+)\s+MEME-(\d+)\s+width\s*=\s*(\d+)\s+sites\s*=\s*(\d+)\s+llr\s*=\s*(\d+)\s+E-value\s*=\s*(\S+)'
        )

    def extract_data_from_txt(self, txt_file):
        extracted_data = []
        try:
            with open(txt_file, 'r') as file:
                content = file.read()
            matches = self.pattern.findall(content)
            if not matches:
                print(f"No matches found in {txt_file}. Check the file format or regex.")
            for match in matches:
                motif, number, width, sites, llr, e_value = match
                number = int(number)
                if 1 <= number <= 2:
                    extracted_data.append({
                        'motif': motif,
                        'number': number,
                        'width': int(width),
                        'sites': int(sites),
                        'llr': int(llr),
                        'e_value': e_value
                    })
            data_dict = {str(d['number']): d for d in extracted_data}
            return data_dict
        except FileNotFoundError:
            print(f"File not found: {txt_file}")
            return {}

    def to_latex_path(self, path):
        return path.replace(os.sep, '/')

    def compile_pdf(self):
        self.doc.append(NoEscape(r'\maketitle'))

        for fold_name in sorted(os.listdir(self.base_path)):
            if fold_name.endswith("_SNPs"):
                folder_path = os.path.join(self.base_path, fold_name)
                meme_out_path = os.path.join(folder_path, "meme_out")

                if os.path.exists(meme_out_path):
                    png_files = sorted([f for f in os.listdir(meme_out_path) if f.endswith('.png')])
                    if len(png_files) >= 10:
                        txt_file = os.path.join(meme_out_path, "meme.txt")
                        data = self.extract_data_from_txt(txt_file)

                        file_name = fold_name.replace("_SNPs", ".csv")
                        concentration = self.concentration_map.get(file_name, "Unknown Concentration")
                        replicate = "Replicate: 01" if not concentration.endswith("_2") else "Replicate: 02"

                        self.doc.append(NewPage())
                        self.doc.append(Section(f"File: {fold_name} ({concentration}, {replicate})"))

                        with self.doc.create(Tabular('|c|c|c|', pos='ht')) as table:
                            table.add_hline()
                            table.add_row([NoEscape(r'\textbf{Logo}'), NoEscape(r'\textbf{RC Logo}'), NoEscape(r'\textbf{Data}')])
                            table.add_hline()

                            for i in range(1, 3):  
                                logo_file = os.path.join(meme_out_path, f'logo{i}.png')
                                rc_logo_file = os.path.join(meme_out_path, f'logo_rc{i}.png')

                                if os.path.exists(logo_file) and os.path.exists(rc_logo_file):
                                    logo_file_rel = self.to_latex_path(os.path.relpath(logo_file, self.base_path))
                                    rc_logo_file_rel = self.to_latex_path(os.path.relpath(rc_logo_file, self.base_path))

                                    e_value = data.get(str(i), {}).get('e_value', 'N/A')
                                    sites = data.get(str(i), {}).get('sites', 'N/A')
                                    width = data.get(str(i), {}).get('width', 'N/A')

                                    table.add_row([
                                        NoEscape(r'\includegraphics[width=0.34\textwidth]{%s}' % logo_file_rel),
                                        NoEscape(r'\includegraphics[width=0.34\textwidth]{%s}' % rc_logo_file_rel),
                                        NoEscape(f'Width: {width}, Sites: {sites}, E-value: {e_value}')
                                    ])
                                    table.add_hline()
                                else:
                                    print(f"Missing logos for {fold_name} (Motif {i})")

        tex_file = os.path.join(self.base_path, "NKX25_meme_output")
        self.doc.generate_tex(tex_file)

        try:
            subprocess.run(
                ['pdflatex', '--interaction=nonstopmode', 'NKX25_meme_output.tex'],
                cwd=self.base_path, check=True
            )
            print(f"PDF generated: {self.output_pdf}")
        except subprocess.CalledProcessError as e:
            print(f"Error during PDF generation: {e}")

base_path = "./output/NKX25/bound_vs_unbound/meme-output_MEME"
output_pdf = "./output/NKX25/bound_vs_unbound/meme-output_MEME/NKX25_meme_output.pdf"
concentration_map = {
	    "R52_13_Vs_R52_14.csv": "3000 nM Bound",
	    "R52_11_Vs_R52_12.csv": "2000 nM Bound",
	    "R52_09_Vs_R52_10.csv": "1500 nM Bound",
	    "R52_07_Vs_R52_08.csv": "1000 nM Bound",
	    "R52_05_Vs_R52_06.csv": "500 nM Bound",
	    "R52_03_Vs_R52_04.csv": "100 nM Bound",
	    "R52_01_Vs_R52_02.csv": "0 nM Bound",
	    "R52_18_Vs_R52_19.csv": "0 nM Bound_2",
	    "R52_20_Vs_R52_21.csv": "100 nM Bound_2",
	    "R52_22_Vs_R52_23.csv": "500 nM Bound_2",
	    "R52_24_Vs_R52_25.csv": "1000 nM Bound_2",
	    "R52_26_Vs_R52_27.csv": "1500 nM Bound_2",
	    "R52_28_Vs_R52_29.csv": "2000 nM Bound_2",
	    "R52_30_Vs_R52_31.csv": "3000 nM Bound_2"
	}
start_time = time.time()
meme_to_pdf = MemeToPdf(base_path, output_pdf, concentration_map)
meme_to_pdf.compile_pdf()
end_time = time.time()
total_time = end_time - start_time
print(f"Total time taken: {total_time:.2f} seconds")
