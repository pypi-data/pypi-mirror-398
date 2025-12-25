# 🧬 PrOBEX: Probabilistic Optimization of Binding via Enrichment from SELEX

**Article URL:** [https://doi.org/10.64898/2025.12.02.691900]

---

## 📊 Graphical Overview
![Pipeline Overview](abstract/graph_abstract.png)

---

## 🧠 Overview

**PrOBEX** is a modular computational pipeline designed for **probabilistic optimization of transcription factor binding** using **SELEX (Systematic Evolution of Ligands by EXponential enrichment)** data.  
It provides a complete suite of scripts for **data preprocessing, visualization, motif discovery, enrichment analysis, and probabilistic model fitting**.

---

## 📦 Dataset 

⬇️ **Download the dataset from Zenodo** to reproduce results, perform analyses, or validate methods.  

**🌐 Zenodo DOI:** [10.5281/zenodo.XXXXXXX]()  

**Dataset Details:**  
- Generated at the Rodríguez-Martínez Lab ([Lab Website](https://thejarmlab.weebly.com/research.html))  

**Usage Instructions:**   
1. Download the Zenodo dataset  
2. Place files in the folder structure indicated in this repository to reproduce all analyses

---

## 📁 Project Structure

```bash
.
├── abstract
├── conda-recipe
├── data/    #Create data dir "data" and place all the downloaded folders/files "NKX2-5", "GATA4", "TBX5" here
├── dist
├── LICENSE
├── MANIFEST.in
├── ProBEX
├── ProBEX_snp.egg-info
├── README.md
└── setup.py

```

---

## ⚙️ Pipeline Execution Order

This repository includes scripts organized into logical stages.  
Follow the recommended order below for accurate and reproducible analysis.

---

### I. PREPROCESSING, SCATTER PLOTS & HEATMAPS

| Step | Script | Output |
|------|---------|---------|
| 1 | `preprocess_snp_seq.py` | `txt_files`, `csv_folder`, `{tf}_files_count_summary.xlsx`, `processed_files`, `processed_files/rsID_added` |
| 2 | `primary_thresholds.py` | `{tf}_row_counts_summary.xlsx`, `{tf}output_labels.csv`, `{tf}_labels.xlsx`, `summary_5MPass.csv` |
| 3 | `secondary_thresholds.py` | `rsID_filtering.xlsx` |
| 4 | `get_enrichment_calc_bound_unb.py` | `bound_vs_unbound` |
| 5 | `get_enrichment_calc_bound_lib.py` | `bound_vs_lib` |
| 6 | `extract_columns_withparameters.py` | `extracted_rsIDs.xlsx` |
| 7 | `getlist_accepted_discarded_rsIDs.py` | `{tf}_accepted_rsIDs.csv`, `{tf}_discarded_rsIDs.csv` |
| 8 | `lineplot_merged_replicates_with_errorBars_all_alleles_bound_unb.py` | `rsID_plots_bound_unb` |
| 9 | `lineplot_merged_replicates_with_errorBars_ref_alt_alleles_bound_unb.py` | `rsID_plots_with_errorBars_withoutgrid_bound_unb` |
| 10 | `lineplot_merged_replicates_with_errorBars_all_alleles_bound_lib.py` | `rsID_plots_all_with_errorBars_withoutgrid_scaled_lib` |
| 11 | `corr_plot_btw_rep.py` | `corr_heatmap_rep1_2.png` |
| 12 | `corr_plot_btw_rep_with_accepted_rsIDs.py` | `original_control.csv`, `corr_heatmap_rep1_2_with_accepted_rsIDs.png` |
| 13 | `scatter_plots_with_accepted_rsIDs.py` | `tables_tex_scatter_plots`, `scatter_plots`, `scatter_plot_document.pdf` |
| 14 | `scatter_plots_with_accepted_rsIDs_mean.py` | `plots_mean_scatter`, `tables_mean_scatter`, `scatter_plot_document_mean.pdf` |
| 15 | `create_heatmap_for_controls.py` | `HeatMap_controls_{tf}.png` |
| 16 | `extract_tables_foreach_conc_scatter.py` | `scatter_plots_tables` |
| 17 | `generate_mean_heatmap_from_scatter.py` | `heatmap_data_mean_scatter.png` |
| 18 | `extract_increased_decreased_rsIDs_from_scatterplot_foreach_conc.py` | `intersected_rsids_based_scatterPlot` |
| 19 | `generate_mean_heatmap_from_scatter_for_eachConc.py` | `mean_heatmaps_from_scatter` |

---

### II. MEME (Motif Discovery)

## Requirements

- **Operating System:** Linux (recommended)
- **MEME Suite:** Must be downloaded and available in the working directory


| Step | Script | Output |
|------|---------|---------|
| 20 | `get_fasta_bed_files_v1.py` | `{tf}_fasta_files`, `{tf}_bed_files` |
| 21 | `run_MEME_ChIP_v1.py` | `meme-output_MEME/` |
| 22 | `gen_motifs_pdf_from_meme.py` | `{tf}_meme_output.pdf` |

---

### III. FITTING

| Step | Script | Output |
|------|---------|---------|
| 23 | `get_enrichment_calc_bound_unb_without_pseudocounts.py` | `bound_vs_unbound_without_pseudocounts` |
| 24 | `combine_data_lib_unb_bound_v2.py` | `merged_df_{tf}_without_pseudocounts.csv` |
| 25 | `get_thedenominators_iteratively.py` | `results_100` |
| 26 | `fitting_poisson_eQ_2_also_withUnb_with_bi.py` | `iteration_results_withunb_with_bi` |
| 27 | `get_AT_GC_percent_withfitted_C_denom.py` | `updated_CORREL_with_bi.xlsx`, `rsID_sequence_percentages.xlsx` |
| 28 | `plot_ref_alt_allele_v3_withFC.py` | `FC_table_with_bi.xlsx`, `ref_vs_alt_correlation_plot.png` |
| 29 | `plot_ref_alt_allele_withFC_without_label.py` | `ref_vs_alt_correlation_plot_without_label.png` |
| 30 | `combine_data_lib_unb_bound_with_psuedocounts_2point5perM_for_unbound.py` | `merged_df_{tf}_with_pseudocounts_2point5.csv` |
| 31 | `lineplots_obs_pred_obs_shifted_2_point_5_psuedocounts.py` | `linePlots_fittedK` |

---

### IV. FITTING PLOTS

| Step | Script | Output |
|------|---------|---------|
| 32 | `heatmap_increased_decreased_with_K_values.py` | `K_value_heatmaps/` |

---

### V. MOTIF CREATION

| Step | Script | Output |
|------|---------|---------|
| 33 | `extract_top_K_values_for_MEME_LSGKM.py` | `500_sequences_for_meme.xlsx`, `all_sequences_for_lsgkm.xlsx` |
| 34 | `get_fasta_bed_files_v2.py` | `SNPs_500.fa`, `SNPs_500.bed` |
| 35 | `run_MEME_ChIP_v2.py` | `meme-output_MEME/` |

---

### VI. MOTIF POSITIONAL EFFECT ANALYSIS

| Step | Script | Output |
|------|---------|---------|
| 36 | `SNPscore_memePWM_logo_with_bars.py` | `processed_increased_sequences.csv`, `processed_decreased_sequences.csv`, `{tf}_motif_analysis_plot.png` |
| 37 | `motif_affected_unaffected_bySNP.py` | `Pos_motif_affect_reverse_withoutgrid.png`, `Pos_motif_affect_forward_withoutgrid.png`, `contribution_bar_plot_lightblue_orange_red_reverse_withoutgrid.png`, `contribution_bar_plot_lightblue_orange_red_withoutgrid.png` |

---

## 📦 Installation via PIP

To install the PrOBEX package using **pip**, run:

```bash
pip install ProBEX-snp
