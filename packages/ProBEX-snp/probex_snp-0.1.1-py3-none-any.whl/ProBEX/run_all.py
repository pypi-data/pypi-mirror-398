import subprocess
import os
import sys

TF_FACTORS = {
    "nkx25": "NKX25_scripts",
    "tbx5": "TBX5_scripts",
    "gata4": "GATA4_scripts"
}

SCRIPT_GROUPS = {
    "preprocessing": [
        "preprocess_snp_seq.py",
        "primary_thresholds.py",
        "secondary_thresholds.py",
        "get_enrichment_calc_bound_unb.py",
        "get_enrichment_calc_bound_lib.py",
        "extract_columns_withparameters.py",
        "getlist_accepted_discarded_rsIDs.py",
    ],
    "plotting": [
        "lineplot_merged_replicates_with_errorBars_all_alleles_bound_unb.py",
        "lineplot_merged_replicates_with_errorBars_ref_alt_alleles_bound_unb.py",
        "lineplot_merged_replicates_with_errorBars_all_alleles_bound_lib.py",
        "corr_plot_btw_rep.py",
        "corr_plot_btw_rep_with_accepted_rsIDs.py",
        "scatter_plots_with_accepted_rsIDs.py",
        "scatter_plots_with_accepted_rsIDs_mean.py",
        "create_heatmap_for_controls.py",
        "extract_tables_foreach_conc_scatter.py",
        "generate_mean_heatmap_from_scatter.py",
        "extract_increased_decreased_rsIDs_from_scatterplot_foreach_conc.py",
        "generate_mean_heatmap_from_scatter_for_eachConc.py",
    ],
    "plot_only_ref":["lineplot_merged_replicates_with_errorBars_ref.py"
    ],
    "meme": [
        "get_fasta_bed_files_v1.py",
        "run_MEME_ChIP_v1.py",
        "gen_motifs_pdf_from_meme.py"
    ],
    "fitting": [
        "get_enrichment_calc_bound_unb_without_pseudocounts.py",
        "combine_data_lib_unb_bound_v2.py",
        "get_thedenominators_iteratively.py",
        "fitting_poisson_eQ_2_also_withUnb_with_bi.py",
        "get_AT_GC_percent_withfitted_C_denom.py",
        "plot_ref_alt_allele_v3_withFC.py",
        "plot_ref_alt_allele_withFC_without_label.py",
        "combine_data_lib_unb_bound_with_psuedocounts_2point5perM_for_unbound.py",
        "lineplots_obs_pred_obs_shifted_2_point_5_psuedocounts.py",
        "heatmap_increased_decreased_with_K_values.py"
    ],
    "combine_data": [
        "combine_data_with_zeronM_lib_unb_bound_with_psuedocounts_2point5perM_for_unbound.py"
    ],
    "fitting_plots": [
        "heatmap_increased_decreased_with_K_values.py"
    ],
    "motif_analysis_1": [
        "extract_top_K_values_for_MEME_LSGKM.py",
        "get_fasta_bed_files_v2.py",
        "run_MEME_ChIP_v2.py"
    ],
    "motif_analysis_2": [
        "SNPscore_memePWM_logo_with_bars.py",
        "motif_affected_unaffected_bySNP.py"
    ]
}

def main():
    print("Initializing systems... Live long and prosper — Spock!.")
    print("Select the transcription factor (TF) analysis to run:")
    tf_list = list(TF_FACTORS.keys())
    for i, tf in enumerate(tf_list, start=1):
        print(f"{i}. {tf.upper()}")
    tf_choice = input("Enter the number of your choice: ").strip()

    try:
        tf_name = tf_list[int(tf_choice) - 1]
    except (IndexError, ValueError):
        print("Invalid TF choice. Exiting.")
        sys.exit(1)

    print("\nSelect the analysis group to run:")
    group_list = list(SCRIPT_GROUPS.keys())
    for i, group in enumerate(group_list, start=1):
        print(f"{i}. {group}")
    group_choice = input("Enter the number of your choice: ").strip()

    try:
        group_name = group_list[int(group_choice) - 1]
    except (IndexError, ValueError):
        print("Invalid group choice. Exiting.")
        sys.exit(1)

    print(f"\nRunning '{group_name}' scripts for TF: {tf_name.upper()}")

    script_dir = os.path.join(os.path.dirname(__file__), "scripts", TF_FACTORS[tf_name])
    scripts = SCRIPT_GROUPS[group_name]

    for script in scripts:
        script_path = os.path.join(script_dir, script)
        if not os.path.isfile(script_path):
            print(f"Warning: Script '{script}' not found in {script_dir}. Skipping.")
            continue

        print(f"\n🔹 Running: {script}")
        subprocess.run(["python", script_path], check=True)

if __name__ == "__main__":
    print("PrOBEX successfully installed! Add your pipeline logic here.")
    main()
