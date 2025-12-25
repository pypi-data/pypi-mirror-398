import pandas as pd
import re, os, time

"""
Author: [Shreya Sharma]
Date: [March 24, 2025]
Description:
	This Python script processes DNA pattern data to compute GC% and AT% compositions, expands the sequence data by base substitution, and merges the results with external fitting data for downstream analysis.
"""

input_file = './output/GATA4/bound_vs_unbound/R52_38_Vs_R52_39.csv'
df = pd.read_csv(input_file, usecols=['rsID', 'Pattern', 'Total Count', 'A', 'T', 'G', 'C', 'RefAllele', 'AltAllele'])

def clean_pattern(pattern):
    """Removes '[ATGC]{2}' from both ends of a pattern string."""
    if pattern.startswith("[ATGC]{2}"):
        pattern = pattern[len("[ATGC]{2}"):]
    if pattern.endswith("[ATGC]{2}"):
        pattern = pattern[:-len("[ATGC]{2}")]
    return pattern

def gc_at_percentage(seq):
    """Calculates GC% and AT% of a DNA sequence."""
    length = len(seq)
    g = seq.count('G')
    c = seq.count('C')
    a = seq.count('A')
    t = seq.count('T')
    gc_percent = 100 * (g + c) / length if length > 0 else 0
    at_percent = 100 * (a + t) / length if length > 0 else 0
    return round(gc_percent, 2), round(at_percent, 2)

start_time = time.time()
records = []
for _, row in df.iterrows():
    rsid = row['rsID']
    pattern = clean_pattern(row['Pattern'])
    RefAllele = row["RefAllele"]
    AltAllele = row["AltAllele"]
    for base in ['A', 'T', 'G', 'C']:
        seq = re.sub(r'\[ATGC\]', base, pattern)
        gc, at = gc_at_percentage(seq)
        records.append({
            'rsID': f"{rsid}_{base}",
            'Sequence': seq,
            'RefAllele': RefAllele,
            'AltAllele': AltAllele,
            'GC%': gc,
            'AT%': at
        })

sequence_df = pd.DataFrame(records)
sequence_output_path = './output/GATA4/fitting/rsID_sequence_percentages.xlsx'
sequence_df.to_excel(sequence_output_path, index=False)

# CSV to EXCEL
csv_path = "./output/GATA4/fitting/iteration_results_withunb_with_bi/fitted_K_results_iteration_10.csv"
df = pd.read_csv(csv_path)
excel_path = os.path.splitext(csv_path)[0] + ".xlsx"
df.to_excel(excel_path, index=False)

fitted_c_results_path = "./output/GATA4/fitting/iteration_results_withunb_with_bi/fitted_K_results_iteration_10.xlsx"
external_df = pd.read_excel(fitted_c_results_path)
merged_df = pd.merge(sequence_df, external_df, on='rsID', how='inner')

final_output_path = './output/GATA4/fitting/updated_CORREL_with_bi.xlsx'
merged_df.to_excel(final_output_path, index=False)
print(f"Final merged data saved to: {final_output_path}")
end_time = time.time()
total_time = end_time - start_time
print(f"Total time taken: {total_time:.2f} seconds")