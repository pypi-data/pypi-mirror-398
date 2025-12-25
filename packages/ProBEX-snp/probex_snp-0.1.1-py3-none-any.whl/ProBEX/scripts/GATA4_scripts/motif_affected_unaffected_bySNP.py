import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
matplotlib.use('Agg')
import time, logging
"""
Script: Positional Contribution Visualization
Author: [Shreya Sharma]
Date: November 24, 2024

Description:
	This script processes CSV files containing sequence contributions and generates bar plots for positional bins.  
	It supports full, reversed, and subset visualizations.
"""

def load_and_process_data(increased_file, decreased_file):
    """
    Loads and processes the increased and decreased sequence data from CSV files.
    Returns the counts of 'Max Bin' values for both increased and decreased sequences.
    """
    inc_data = pd.read_csv(increased_file)
    inc_counts = inc_data['Max Bin'].value_counts().sort_index()
    dec_data = pd.read_csv(decreased_file)
    dec_counts = dec_data['Max Bin'].value_counts().sort_index()
    all_positions = list(range(1, 35))
    inc_counts = inc_counts.reindex(all_positions, fill_value=0)
    dec_counts = dec_counts.reindex(all_positions, fill_value=0)

    return inc_counts, dec_counts, all_positions

def plot_contribution(inc_counts, dec_counts, all_positions, output_path):
    """
    Plots a bar chart showing the contribution of increase and decrease sequences at each position.
    The plot is saved to the specified output path.
    """
    plt.figure(figsize=(12, 7))
    plt.bar(
        all_positions, 
        inc_counts, 
        label='Increase Contribution', 
        color='#254B96', 
        hatch='/', 
        edgecolor='black'
    )
    plt.bar(
        all_positions, 
        dec_counts, 
        bottom=inc_counts, 
        label='Decrease Contribution', 
        color='#BF212F', 
        hatch='\\', 
        edgecolor='black'
    )
    plt.minorticks_on()
    #plt.grid(which='both', linestyle='--', linewidth=0.5, alpha=0.7)
    #plt.grid(which='minor', color='gray', linestyle=':', linewidth=0.5, alpha=0.5)
    plt.xlabel("Position", fontsize=12)
    plt.ylabel("Frequency", fontsize=12)
    plt.title("Contribution to Each Position (Increase vs Decrease)", fontsize=14)
    plt.legend(fontsize=10)
    plt.xticks(all_positions, fontsize=10)
    plt.yticks(fontsize=10)
    plt.tight_layout()
    plt.savefig(output_path, dpi=350)
    #plt.show()

def plot_reversed_contribution(inc_counts, dec_counts, output_path):
    """
    Plots a bar chart showing the reversed contribution of increase and decrease sequences at each position,
    where positions are displayed in reverse order.
    """
    subset_positions = list(range(34, 0, -1))  # Reversed positions
    new_positions = list(range(1, 35))
    inc_subset = inc_counts.reindex(subset_positions, fill_value=0)
    dec_subset = dec_counts.reindex(subset_positions, fill_value=0)
    fig, ax = plt.subplots(figsize=(12, 7))
    ax.bar(
        new_positions, 
        inc_subset.values, 
        label='Increase Contribution', 
        color='#254B96', 
        hatch='/', 
        edgecolor='black'
    )
    ax.bar(
        new_positions, 
        dec_subset.values, 
        bottom=inc_subset.values, 
        label='Decrease Contribution', 
        color='#BF212F', 
        hatch='\\', 
        edgecolor='black'
    )
    ax.minorticks_on()
    #ax.grid(which='both', linestyle='--', linewidth=0.5, alpha=0.7)
    #ax.grid(which='minor', color='gray', linestyle=':', linewidth=0.5, alpha=0.5)
    ax.set_xlabel("Positions", fontsize=12)
    ax.set_ylabel("Frequency", fontsize=12)
    ax.set_title("Contribution to Positions (Increase vs Decrease)", fontsize=14)
    ax.legend(fontsize=10)
    ax.set_xticks(new_positions)
    ax.tick_params(axis='x', labelsize=10)
    ax.tick_params(axis='y', labelsize=10)
    plt.tight_layout()
    plt.savefig(output_path, dpi=350)
    #plt.show()

def plot_subset_contribution(inc_counts, dec_counts, subset_positions, new_positions, output_path):
    """
    Plots a bar chart showing the contribution of increase and decrease sequences at a specific subset of positions.
    Positions are renamed from a specified range to a new range.
    """
    inc_subset = inc_counts.reindex(subset_positions, fill_value=0)
    dec_subset = dec_counts.reindex(subset_positions, fill_value=0)
    fig, ax = plt.subplots(figsize=(12, 7))
    ax.bar(
        new_positions, 
        inc_subset.values,  
        label='Increase Contribution', 
        color='#254B96', 
        hatch='/', 
        edgecolor='black'
    )
    ax.bar(
        new_positions, 
        dec_subset.values,  
        bottom=inc_subset.values, 
        label='Decrease Contribution', 
        color='#BF212F', 
        hatch='\\', 
        edgecolor='black'
    )
    ax.minorticks_on()
    #ax.grid(which='both', linestyle='--', linewidth=0.5, alpha=0.7)
    #ax.grid(which='minor', color='gray', linestyle=':', linewidth=0.5, alpha=0.5)
    ax.set_xlabel("Positions", fontsize=12)
    ax.set_ylabel("Frequency", fontsize=12)
    ax.set_title("Contribution to Positions (Increase vs Decrease)", fontsize=14)
    ax.legend(fontsize=10)
    ax.set_xticks(new_positions)
    ax.tick_params(axis='x', labelsize=10)
    ax.tick_params(axis='y', labelsize=10)
    fig.tight_layout()
    plt.savefig(output_path, dpi=350)
    #plt.show()
    
start_time = time.time()    
inc_counts, dec_counts, all_positions = load_and_process_data('./output/GATA4/motif_affect_GATA4/processed_increased_sequences.csv', './output/GATA4/motif_affect_GATA4/processed_decreased_sequences.csv')
plot_contribution(inc_counts, dec_counts, all_positions, "./output/GATA4/motif_affect_GATA4/contribution_bar_plot_lightblue_orange_red_withoutgrid.png")
plot_reversed_contribution(inc_counts, dec_counts, "./output/GATA4/motif_affect_GATA4/contribution_bar_plot_lightblue_orange_red_reverse_withoutgrid.png")
plot_subset_contribution(inc_counts, dec_counts, list(range(15, 21)), list(range(1, 7)), "./output/GATA4/motif_affect_GATA4/Pos_motif_affect_forward_withoutgrid.png")
plot_subset_contribution(inc_counts, dec_counts, list(range(20, 14, -1)), list(range(1, 7)), "./output/GATA4/motif_affect_GATA4/Pos_motif_affect_reverse_withoutgrid.png")
end_time = time.time()  # End timing
total_time = end_time - start_time
print(f"Total time taken: {total_time:.2f} seconds")
