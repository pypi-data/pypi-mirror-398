import numpy as np
import pandas as pd
from scipy.optimize import least_squares
import logging, time
import os
import matplotlib.pyplot as plt

"""

Author: [Shreya Sharma]
Date: [March 22, 2025]
Description:

	Script to perform non-linear least squares fitting for modeling molecular enrichment data.

	This script processes high-throughput sequencing data to estimate binding constants (K values) 
	for different genetic variants (rsIDs) across a range of concentrations. It uses observed 
	fractional enrichments derived from sequencing counts and models these through a custom 
	enrichment equation. The optimization is performed using SciPy's `least_squares`.
"""

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
log = logging.getLogger(__name__)

def enrichment_equation(K_values, concentrations, denominators):
    predicted_enrich = []
    denominator_terms = []
    for i, conc in enumerate(concentrations):
        numerator = 1 / (1 + (1 / (K_values * conc)))
        denominator = denominators[i]
        predicted_enrich.append(numerator / denominator)
    return predicted_enrich, denominator_terms

def residual(K_values_log, Frac_all, concentrations, denominators):
    predicted, _ = enrichment_equation(np.power(10, K_values_log), concentrations, denominators)
    predicted = np.array(predicted).flatten()
    observed_enrichment = np.array(Frac_all).flatten()
    return predicted - observed_enrichment

def update_denominators(fitted_K, Frac_lib_conc, concentrations):
    denominators = []
    for i, conc in enumerate(concentrations):
        numerator = 1 / (1 + (1 / (fitted_K * conc)))
        denominator_term = numerator * Frac_lib_conc[i]
        denominator = np.sum(denominator_term)
        denominators.append(denominator)
    return denominators

def save_results_to_file(result_dir, filename, rsIDs, fitted_K, denominators_history, K_history, mse_history, mse_per_rsID_history, iteration=None):
    os.makedirs(result_dir, exist_ok=True)

    if iteration is None:
        iter_range = range(len(denominators_history))
    else:
        iter_range = [iteration]

    df = pd.DataFrame({'rsID': rsIDs, 'Fitted_K': fitted_K})
    df.to_csv(os.path.join(result_dir, filename), index=False)

    concentration_names = ["100_R1", "500_R1", "1000_R1", "1500_R1", "2000_R1", "3000_R1",
                           "100_R2", "500_R2", "1000_R2", "1500_R2", "2000_R2", "3000_R2"]

    for i in iter_range:
        df_denominators = pd.DataFrame([denominators_history[i]], columns=concentration_names)
        df_denominators.to_csv(f'{result_dir}/denominators_iteration_{i+1}.csv', index=False)

        df_K = pd.DataFrame({'rsID': rsIDs, 'K_values': K_history[i]})
        df_K.to_csv(f'{result_dir}/K_values_iteration_{i+1}.csv', index=False)

        df_mse_rsid = pd.DataFrame({'rsID': rsIDs, 'MSE': mse_per_rsID_history[i]})
        df_mse_rsid.to_csv(f'{result_dir}/mse_per_rsid_iteration_{i+1}.csv', index=False)

    df_mse = pd.DataFrame({'Iteration': list(range(1, len(mse_history) + 1)), 'MSE': mse_history})
    df_mse.to_csv(f'{result_dir}/mse_history.csv', index=False)

def save_fractions(rsIDs, Frac_all, Frac_lib_conc,
                   filename_all="./output/NKX25/fitting/frac_all_interm.txt",
                   filename_lib="./output/NKX25/fitting/frac_lib_con_interm.txt"):
    Frac_all_array = np.column_stack(Frac_all)
    Frac_lib_conc_array = np.column_stack(Frac_lib_conc)

    df_frac_all = pd.DataFrame(Frac_all_array, columns=[f"Conc_{i+1}" for i in range(Frac_all_array.shape[1])])
    df_frac_all.insert(0, "rsID", rsIDs[:len(df_frac_all)])

    df_frac_lib_conc = pd.DataFrame(Frac_lib_conc_array, columns=[f"Conc_{i+1}" for i in range(Frac_lib_conc_array.shape[1])])
    df_frac_lib_conc.insert(0, "rsID", rsIDs[:len(df_frac_lib_conc)])

    df_frac_all.to_csv(filename_all, sep="\t", index=False)
    df_frac_lib_conc.to_csv(filename_lib, sep="\t", index=False)

def fit_all_Ks(merged_df, batch_size, result_dir="./output/NKX25/fitting/results_1000"):
    rsIDs = merged_df["rsID"].values
    Counts_Lib_1 = merged_df["Library_1"].values
    Counts_Lib_2 = merged_df["Library_2"].values

    concentrations = np.array([100, 500, 1000, 1500, 2000, 3000, 100, 500, 1000, 1500, 2000, 3000])

    count_arrays = {
        'Lib_1': Counts_Lib_1,
        'Lib_2': Counts_Lib_2,
        '100_R1': merged_df["100_count_R1_b"].values,
        '500_R1': merged_df["500_count_R1_b"].values,
        '1000_R1': merged_df["1000_count_R1_b"].values,
        '1500_R1': merged_df["1500_count_R1_b"].values,
        '2000_R1': merged_df["2000_count_R1_b"].values,
        '3000_R1': merged_df["3000_count_R1_b"].values,
        '100_R2': merged_df["100_count_R2_b"].values,
        '500_R2': merged_df["500_count_R2_b"].values,
        '1000_R2': merged_df["1000_count_R2_b"].values,
        '1500_R2': merged_df["1500_count_R2_b"].values,
        '2000_R2': merged_df["2000_count_R2_b"].values,
        '3000_R2': merged_df["3000_count_R2_b"].values
    }

    all_arrays = np.stack(list(count_arrays.values()), axis=1)
    valid_indices = np.where(np.all(all_arrays != 0, axis=1))[0]
    rsIDs = rsIDs[valid_indices]
    for key in count_arrays:
        count_arrays[key] = count_arrays[key][valid_indices]

    total_K = len(rsIDs)

    Frac_Lib_R1 = count_arrays['Lib_1'] / np.sum(count_arrays['Lib_1'])
    Frac_Lib_R2 = count_arrays['Lib_2'] / np.sum(count_arrays['Lib_2'])

    Frac_Concs_R1 = []
    Frac_Concs_R2 = []
    for conc in [100, 500, 1000, 1500, 2000, 3000]:
        Frac_Concs_R1.append(count_arrays[f'{conc}_R1'] / np.sum(count_arrays[f'{conc}_R1']))
        Frac_Concs_R2.append(count_arrays[f'{conc}_R2'] / np.sum(count_arrays[f'{conc}_R2']))

    Enrich_R1 = [Frac_Concs_R1[i] / Frac_Lib_R1 for i in range(6)]
    Enrich_R2 = [Frac_Concs_R2[i] / Frac_Lib_R2 for i in range(6)]

    Frac_all = Enrich_R1 + Enrich_R2
    Frac_lib_conc = [Frac_Lib_R1] * 6 + [Frac_Lib_R2] * 6

    save_fractions(rsIDs, Frac_all, Frac_lib_conc)

    max_observed_enrichment = [arr.max() for arr in Frac_all]
    initial_denominators = [0.9 / max_enrich for max_enrich in max_observed_enrichment]

    initial_K = np.full(total_K, 1.0)
    bounds = (-12, 10)

    denominators_history = []
    K_history = []
    mse_history = []
    mse_per_rsID_history = []

    for iteration in range(1000):
        log.info(f"Iteration {iteration + 1}")

        denominators_history.append(initial_denominators.copy())
        mse_per_rsID = np.zeros(total_K)
        fitted_K = np.zeros(total_K)

        for i in range(total_K):
            Frac_all_i = [frac[i] for frac in Frac_all]
            Frac_lib_conc_i = [frac[i] for frac in Frac_lib_conc]

            result = least_squares(
                residual,
                np.log10([initial_K[i]]),
                bounds=bounds,
                args=(Frac_all_i, concentrations, initial_denominators),
                method='trf',
                max_nfev=500000,
                ftol=1e-12,
                xtol=1e-12
            )

            if result.success:
                fitted_K[i] = np.power(10, result.x[0])
            else:
                fitted_K[i] = np.nan

            predicted, _ = enrichment_equation(fitted_K[i], concentrations, initial_denominators)
            predicted = np.array(predicted).flatten()
            observed = np.array(Frac_all_i).flatten()
            mse_per_rsID[i] = np.mean((predicted - observed) ** 2)

        K_history.append(fitted_K.copy())
        mse_per_rsID_history.append(mse_per_rsID.copy())

        predicted_enrich, _ = enrichment_equation(fitted_K, concentrations, initial_denominators)
        predicted_enrich = np.concatenate([np.array(x).flatten() for x in predicted_enrich])
        observed_enrichment = np.concatenate([np.array(x).flatten() for x in Frac_all])
        mse = np.mean((predicted_enrich - observed_enrichment) ** 2)
        mse_history.append(mse)

        # Save intermediate results
        save_results_to_file(
            result_dir,
            "fitted_parameters.csv",
            rsIDs,
            fitted_K,
            denominators_history,
            K_history,
            mse_history,
            mse_per_rsID_history,
            iteration=iteration
        )

        initial_denominators = update_denominators(fitted_K, Frac_lib_conc, concentrations)
        initial_K = fitted_K

    return fitted_K, K_history, denominators_history, mse_history, mse_per_rsID_history

if __name__ == "__main__":
    start_time = time.time() 
    os.makedirs('./output/NKX25/fitting/results_1000', exist_ok=True)
    merged_df = pd.read_csv("./output/NKX25/merged_df_NKX25_without_pseudocounts.csv")
    fitted_K, K_history, denominators_history, mse_history, mse_per_rsID_history = fit_all_Ks(merged_df, batch_size=1)
    end_time = time.time()
    total_time = end_time - start_time
    print(f"Total time taken: {total_time:.2f} seconds")