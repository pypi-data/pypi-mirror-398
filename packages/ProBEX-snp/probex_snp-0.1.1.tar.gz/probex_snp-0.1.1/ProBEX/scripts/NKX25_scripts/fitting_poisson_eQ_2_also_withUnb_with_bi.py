import os
import numpy as np
import pandas as pd
from scipy.optimize import minimize
import time, logging
import matplotlib.pyplot as plt
from scipy.special import expit

'''
Author: [Shreya Sharm]
Date: [March 26, 2025]
Description:
	This script iteratively fits binding model parameters (K, λ for replicates, and binding bias bⱼ) for SNP count data using maximum likelihood estimation.
It updates normalization denominators across 10 iterations, optimizing per-SNP using `scipy.optimize.minimize`.
Final parameters are saved, and λ distributions are visualized for quality assessment.

'''

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
log = logging.getLogger(__name__)
results_dir = "./output/NKX25/fitting/iteration_results_withunb_with_bi"
os.makedirs(results_dir, exist_ok=True)
merged_df_combined = pd.read_csv("./output/NKX25/merged_df_NKX25_without_pseudocounts.csv")
denom_df = pd.read_csv("./output/NKX25/fitting/results_1000/denominators_iteration_361.csv")
concentrations = np.array([100, 500, 1000, 1500, 2000, 3000])
initial_denominators_R1 = denom_df[["100_R1", "500_R1", "1000_R1", "1500_R1", "2000_R1", "3000_R1"]].values.flatten().astype(float)
initial_denominators_R2 = denom_df[["100_R2", "500_R2", "1000_R2", "1500_R2", "2000_R2", "3000_R2"]].values.flatten().astype(float)
initial_denominators = np.concatenate([initial_denominators_R1, initial_denominators_R2])

Counts_Lib_1 = merged_df_combined["Library_1"].values
Counts_Lib_2 = merged_df_combined["Library_2"].values

T_L_R1 = np.sum(Counts_Lib_1)
T_L_R2 = np.sum(Counts_Lib_2)

# Calculate total unbound counts for each concentration and replicate
T_Uj_R1 = np.array([np.sum(merged_df_combined[f"{conc}_count_R1_unb"]) for conc in concentrations])
T_Uj_R2 = np.array([np.sum(merged_df_combined[f"{conc}_count_R2_unb"]) for conc in concentrations])
T_Uj = T_Uj_R1 + T_Uj_R2

# Calculate total bound counts for each concentration and replicate
T_cj_R1 = np.array([np.sum(merged_df_combined[f"{conc}_count_R1_b"]) for conc in concentrations])
T_cj_R2 = np.array([np.sum(merged_df_combined[f"{conc}_count_R2_b"]) for conc in concentrations])
T_cj = np.concatenate([T_cj_R1, T_cj_R2])

# Prepare count matrices
n_sij_R1 = np.stack([merged_df_combined[f"{conc}_count_R1_b"].values for conc in concentrations], axis=1)
n_sij_R2 = np.stack([merged_df_combined[f"{conc}_count_R2_b"].values for conc in concentrations], axis=1)
n_Uij_R1 = np.stack([merged_df_combined[f"{conc}_count_R1_unb"].values for conc in concentrations], axis=1)
n_Uij_R2 = np.stack([merged_df_combined[f"{conc}_count_R2_unb"].values for conc in concentrations], axis=1)


def update_denominators_withLambda(denominators, K_values, lambda_Li_R1_opt, lambda_Li_R2_opt, T_L_R1, T_L_R2, bi, concentrations):
    concentrations = np.tile(concentrations, 2)
    K_values = np.nan_to_num(K_values, nan=1.0)
    new_denominators = np.zeros_like(denominators)

    for j in range(12):
        if j < 6:
            lambda_L1_i = lambda_Li_R1_opt
            T_L = T_L_R1
        else:
            lambda_L1_i = lambda_Li_R2_opt
            T_L = T_L_R2

        Frac_lib_conc = lambda_L1_i / T_L
        denominator_term = (1 / (1 + (1 / (K_values * concentrations[j % 6])))) * Frac_lib_conc * (1 - bi)
        new_denominators[j] = np.sum(denominator_term)

    return new_denominators


def calculate_unbound_denominators(denominators, K_values, lambda_Li_R1_opt, lambda_Li_R2_opt, T_L_R1, T_L_R2, bi, concentrations):
    """Calculate denominators for unbound fractions for both replicates."""
    concentrations = np.tile(concentrations, 2)
    K_values = np.nan_to_num(K_values, nan=1.0)
    new_denominators = np.zeros_like(denominators)

    for j in range(12):
        if j < 6:
            lambda_L1_i = lambda_Li_R1_opt
            T_L = T_L_R1
            #T_U = T_Uj_R1[j % 6]
        else:
            lambda_L1_i = lambda_Li_R2_opt
            T_L = T_L_R2
            #T_U = T_Uj_R2[j % 6]
        
        Frac_lib_conc = lambda_L1_i / T_L
        denominator_term = (1 - (1 / (1 + (1 / (K_values * concentrations[j % 6]))))) * Frac_lib_conc 
        new_denominators[j] = np.sum(denominator_term)
    return new_denominators

def neg_log_likelihood(params, n_sij_R1_i, n_sij_R2_i, n_Uij_R1_i, n_Uij_R2_i, n_L1, n_L2, 
                      T_cj_R1, T_cj_R2, denominators_R1, denominators_R2, unbound_denominators_R1, unbound_denominators_R2, concentrations, 
                      T_L_R1, T_L_R2, T_Uj_R1, T_Uj_R2):
    """Negative log likelihood function for optimization."""
    K = 10 ** params[0]  # Single K value for both replicates
    lambda_Li_R1, lambda_Li_R2 = params[1], params[2]  # Separate lambda_Li for each replicate
    bi = params[3]

    
    # Calculate lambda_Sij for bound counts (using bound denominators)
    lambda_Sij_R1 = ((T_cj_R1 * lambda_Li_R1) / (denominators_R1 * T_L_R1)) * (1 / (1 + (1 / (K * concentrations)))) * (1-bi)
    lambda_Sij_R2 = ((T_cj_R2 * lambda_Li_R2) / (denominators_R2 * T_L_R2)) * (1 / (1 + (1 / (K * concentrations)))) * (1-bi) 

    lambda_Uij_R1 = ((T_Uj_R1 * lambda_Li_R1) / (unbound_denominators_R1 * T_L_R1)) * (1 - (1 / (1 + (1 / (K * concentrations)))))
    lambda_Uij_R2 = ((T_Uj_R2 * lambda_Li_R2) / (unbound_denominators_R2 * T_L_R2)) * (1 - (1 / (1 + (1 / (K * concentrations)))))
    
    # Clip values to avoid numerical issues
    lambda_Sij_R1 = np.clip(lambda_Sij_R1, 1e-12, None)
    lambda_Sij_R2 = np.clip(lambda_Sij_R2, 1e-12, None)
    lambda_Uij_R1 = np.clip(lambda_Uij_R1, 1e-12, None)
    lambda_Uij_R2 = np.clip(lambda_Uij_R2, 1e-12, None)
    lambda_Li_R1 = np.clip(lambda_Li_R1, 1e-12, None)
    lambda_Li_R2 = np.clip(lambda_Li_R2, 1e-12, None)
    
    # Calculate log likelihood components
    SNP_log_likelihood_R1 = np.sum(n_sij_R1_i * np.log(lambda_Sij_R1) - lambda_Sij_R1)
    SNP_log_likelihood_R2 = np.sum(n_sij_R2_i * np.log(lambda_Sij_R2) - lambda_Sij_R2)
    
    SNP_unb_log_likelihood_R1 = np.sum(n_Uij_R1_i * np.log(lambda_Uij_R1) - lambda_Uij_R1)
    SNP_unb_log_likelihood_R2 = np.sum(n_Uij_R2_i * np.log(lambda_Uij_R2) - lambda_Uij_R2)
    
    library_log_likelihood_R1 = n_L1 * np.log(lambda_Li_R1) - lambda_Li_R1
    library_log_likelihood_R2 = n_L2 * np.log(lambda_Li_R2) - lambda_Li_R2
    
    total_log_likelihood = (SNP_log_likelihood_R1 + SNP_log_likelihood_R2 + 
                           library_log_likelihood_R1 + library_log_likelihood_R2 + 
                           SNP_unb_log_likelihood_R1 + SNP_unb_log_likelihood_R2)
    
    return -total_log_likelihood

def optimize_K_and_lambda_Li(merged_df_combined, T_cj, T_cj_R1, T_cj_R2, initial_denominators, 
                            initial_denominators_R1, initial_denominators_R2, concentrations, 
                            Counts_Lib_1, Counts_Lib_2, max_iters=10):
    """Main optimization function with separate unbound denominators."""
    denominators_R1 = initial_denominators_R1.copy()
    denominators_R2 = initial_denominators_R2.copy()
    denominators = initial_denominators.copy()
    
    # Initialize unbound denominators
    unbound_denominators_R1 = 1-initial_denominators_R1.copy()
    unbound_denominators_R2 = 1-initial_denominators_R2.copy()
    unbound_denominators = 1-initial_denominators.copy()
    
    for iteration in range(max_iters):
        log.info(f"Starting iteration {iteration + 1}/{max_iters}...")
        K_opt, lambda_Li_R1_opt, lambda_Li_R2_opt, bi_opt = [], [], [], []
        
        for i in range(len(merged_df_combined)):
            n_L1_i, n_L2_i = Counts_Lib_1[i], Counts_Lib_2[i]
            initial_params = np.array([np.log10(1.0), 1.0, 1.0, 0.1])
            bounds = [(-6, 1), (0, None), (0, None), (0, 1)]

            res = minimize(
                neg_log_likelihood,
                x0=initial_params,
                bounds=bounds,
                args=(n_sij_R1[i], n_sij_R2[i], n_Uij_R1[i], n_Uij_R2[i], 
                      n_L1_i, n_L2_i, T_cj_R1, T_cj_R2, 
                      denominators_R1, denominators_R2, 
                      unbound_denominators_R1, unbound_denominators_R2, concentrations, 
                      T_L_R1, T_L_R2, T_Uj_R1, T_Uj_R2),
                method='L-BFGS-B',
                options={'maxiter': 1000}
            )
            
            C_value = 10 ** res.x[0]
            lambda_Li_R1_value, lambda_Li_R2_value = res.x[1], res.x[2]
            bi = res.x[3]
            
            K_opt.append(C_value)
            lambda_Li_R1_opt.append(lambda_Li_R1_value)
            lambda_Li_R2_opt.append(lambda_Li_R2_value)
            #print (bi)
            bi_opt.append(round(bi, 8))
            #print(f"Before optimization: initial_params = {initial_params}")
            #print(f"After optimization: optimized_params = {res.x}")

        # Update results in dataframe
        merged_df_combined[f"Fitted_K_iter{iteration+1}"] = K_opt
        merged_df_combined[f"Fitted_lambda_R1_iter{iteration+1}"] = lambda_Li_R1_opt
        merged_df_combined[f"Fitted_lambda_R2_iter{iteration+1}"] = lambda_Li_R2_opt
        merged_df_combined[f"Fitted_bi_iter{iteration+1}"] = bi_opt
        
        # Save intermediate results
        merged_df_combined[["rsID", f"Fitted_K_iter{iteration+1}", 
                      f"Fitted_lambda_R1_iter{iteration+1}", 
                      f"Fitted_lambda_R2_iter{iteration+1}", f"Fitted_bi_iter{iteration+1}"]].to_csv(
            f"{results_dir}/fitted_K_results_iteration_{iteration+1}.csv", index=False)
        
        # Update bound denominators
        denominators = update_denominators_withLambda(
            denominators, np.array(K_opt), np.array(lambda_Li_R1_opt), np.array(lambda_Li_R2_opt), 
            T_L_R1, T_L_R2, np.array(bi_opt), concentrations)
        
        # Update unbound denominators
        unbound_denominators = calculate_unbound_denominators(
            unbound_denominators, np.array(K_opt), np.array(lambda_Li_R1_opt), np.array(lambda_Li_R2_opt),
            T_L_R1, T_L_R2, np.array(bi_opt), concentrations)

        np.savetxt(f"{results_dir}/updated_bound_denominators_iteration_{iteration+1}.csv", 
                  denominators, delimiter=",")
        np.savetxt(f"{results_dir}/updated_unbound_denominators_iteration_{iteration+1}.csv", 
                  unbound_denominators, delimiter=",")
        
        # Split bound denominators for next iteration
        denominators_R1 = denominators[:6]
        denominators_R2 = denominators[6:]
        unbound_denominators_R1 = unbound_denominators[:6]
        unbound_denominators_R2 = unbound_denominators[6:]
    
    return denominators, unbound_denominators

start_time = time.time() 
denominators, unbound_denominators = optimize_K_and_lambda_Li(merged_df_combined, T_cj, T_cj_R1, T_cj_R2, initial_denominators, initial_denominators_R1, initial_denominators_R2, concentrations,  	Counts_Lib_1, Counts_Lib_2, max_iters=10)

log.info("Optimization completed. Final results saved.")
plt.figure(figsize=(10, 6))
final_df = pd.read_csv(f"{results_dir}/fitted_K_results_iteration_10.csv")
plt.hist(np.log10(final_df["Fitted_lambda_R1_iter10"].dropna()), bins=50, alpha=0.5, label='Replicate 1')
plt.hist(np.log10(final_df["Fitted_lambda_R2_iter10"].dropna()), bins=50, alpha=0.5, label='Replicate 2')
plt.xlabel("log10(lambda_Li)")
plt.ylabel("Frequency")
plt.title("Distribution of fitted lambda_Li values (Final Iteration)")
plt.legend()
plt.tight_layout()
plt.savefig(f"{results_dir}/lambda_distribution_final_iteration.png")
#plt.show()
end_time = time.time()
total_time = end_time - start_time
print(f"Total time taken: {total_time:.2f} seconds")