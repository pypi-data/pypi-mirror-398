#!/usr/bin/env Rscript
# export_r_init.R - Export R's POST-INITIALIZATION values for Python
# This creates a GEDI model, runs initialize(), then exports all parameters
# Python can then skip its own initialization and use these values directly

suppressPackageStartupMessages({
  library(Matrix)
  library(gedi)
  library(jsonlite)
})

args <- commandArgs(trailingOnly = TRUE)
n_cells <- if (length(args) >= 1) as.integer(args[1]) else 10000
random_seed <- 42
K <- 10

cat("Exporting R POST-INITIALIZATION values for", n_cells, "cells\n")

# Load full dataset
data_path <- "/home/saberi/projects/gedi/gedi-py/benchmarks/data/benchmark_data.rds"
data <- readRDS(data_path)
M <- data$M
Sample_vec <- as.character(data$samples)

cat("Full data:", nrow(M), "genes x", ncol(M), "cells\n")

# Generate cell indices with R's random seed
set.seed(random_seed)
select_idx <- sample(1:ncol(M), n_cells)

# Subsample
M_sub <- M[, select_idx, drop = FALSE]
Sample_vec_sub <- Sample_vec[select_idx]

cat("Subsampled:", nrow(M_sub), "genes x", ncol(M_sub), "cells\n")

unique_samples <- unique(Sample_vec_sub)
num_samples <- length(unique_samples)
J <- nrow(M_sub)

cat("Number of samples:", num_samples, "\n")

# Compute Yi = log1p(M)
cat("\nComputing Yi = log1p(M)...\n")
Y_sub <- log1p(as.matrix(M_sub))

# Create GEDI model with Y input (obs_type="Y") for fair comparison with Python
cat("Creating GEDI model with Y input (obs_type=Y)...\n")
# Use more threads for faster computation
n_threads <- if (length(args) >= 2) as.integer(args[2]) else 8
cat("Using", n_threads, "threads\n")

set.seed(random_seed)
model <- CreateGEDIObject(
  Samples = Sample_vec_sub,
  Y = Y_sub,  # Use Y instead of M for obs_type="Y"
  K = K,
  verbose = 1,
  num_threads = n_threads
)

# Initialize only (no optimization)
cat("Running initialization (SVD)...\n")
model$initialize_lvs()

cat("Initialization complete.\n")

# Extract POST-INIT parameters
params <- model$params
Z_init <- params$Z
D_init <- params$D
Bi_init <- params$Bi
Qi_init <- params$Qi
oi_init <- params$oi
si_init <- params$si
o_init <- params$o
sigma2_init <- params$sigma2

# CRITICAL: U and S are used in solve_Z_orthogonal() - must export these!
U_init <- params$U  # J x K matrix
S_init <- params$S  # K vector (singular values from rSVD)

# Get Yi matrices from raw data (same as R computed internally)
# Organize Yi by sample
Yi_list <- list()
for (s in unique_samples) {
  idx <- which(Sample_vec_sub == s)
  Mi <- M_sub[, idx, drop = FALSE]
  Yi_list[[length(Yi_list) + 1]] <- log1p(as.matrix(Mi))
}

# Also get hyperparameters from the model's private fields
# Access the underlying C++ model and its hyperparameters
# These are computed in R and passed to C++ during construction

# Get dimensional info
N <- ncol(M_sub)  # total cells
Ni <- sapply(Bi_init, ncol)  # cells per sample

# Default shrinkage parameters (matching R's defaults)
o_shrinkage <- 1.0
si_shrinkage <- 1.0
Z_shrinkage <- 1.0
A_shrinkage <- 1.0
Rk_shrinkage <- 1.0
oi_shrinkage <- 1.0
Qi_shrinkage <- 1.0

# Compute hyperparameters matching R's logic
S_o <- 1 / N / o_shrinkage
S_si <- 1 / J / si_shrinkage
S_Z <- 1 / Z_shrinkage
S_A <- 1 / A_shrinkage
S_R <- 1 / Rk_shrinkage
S_oi <- 1 / Ni / oi_shrinkage  # vector, one per sample
S_Qi <- N / Ni / Qi_shrinkage  # vector, one per sample

# Compute o_0 and si_0 from data (matching R's internal logic for Y input case)
# Based on gedi_class.R lines 257-262

# s_0 computation: for each cell, compute log of mean expression across genes
# This matches compute_s_0_dense which does: log(colSums(exp(Y)) / J)
s_0 <- log(colSums(exp(Y_sub)) / J)

# Yp computation: subtract s_0 from each column of Y
# This matches compute_Yp_dense
Yp <- Y_sub - matrix(rep(s_0, each = J), nrow = J, ncol = N)

# o_0 computation: row means of Yp
# This matches compute_o_0_dense
o_0 <- rowMeans(Yp)

# Split s_0 by sample
si_0 <- list()
for (s in unique_samples) {
  idx <- which(Sample_vec_sub == s)
  si_0[[length(si_0) + 1]] <- s_0[idx]
}

# Generate O matrix for randomized SVD (same seed as model creation)
set.seed(random_seed)
O_matrix <- matrix(rnorm(N * (K + 5)), nrow = N, ncol = K + 5)

cat("\nPost-init values:\n")
cat("  Z:", dim(Z_init), "\n")
cat("  D:", length(D_init), "values:", head(D_init), "\n")
cat("  U:", dim(U_init), "\n")
cat("  S:", length(S_init), "values:", head(S_init), "\n")
cat("  sigma2:", sigma2_init, "\n")
cat("  Bi: list of", length(Bi_init), "matrices\n")

cat("\nHyperparameters:\n")
cat("  S_o:", S_o, "\n")
cat("  S_si:", S_si, "\n")
cat("  S_Z:", S_Z, "\n")
cat("  S_A:", S_A, "\n")
cat("  S_R:", S_R, "\n")
cat("  S_oi:", head(S_oi), "...\n")
cat("  S_Qi:", head(S_Qi), "...\n")
cat("  o_0: length", length(o_0), ", first values:", head(o_0), "\n")
cat("  si_0: list of", length(si_0), "vectors\n")
cat("  O_matrix:", dim(O_matrix), "\n")

# Output directory
output_dir <- "/home/saberi/projects/gedi/gedi-py/benchmarks/data/r_init"
dir.create(output_dir, recursive = TRUE, showWarnings = FALSE)

# Save cell indices
write.csv(select_idx, file.path(output_dir, sprintf("cell_indices_%d.csv", n_cells)),
          row.names = FALSE)

# Save Yi matrices
for (i in seq_along(Yi_list)) {
  write.csv(Yi_list[[i]],
            file.path(output_dir, sprintf("Yi_%d_sample%d.csv", n_cells, i-1)),
            row.names = FALSE)
}

# Save sample info
sample_sizes <- sapply(Bi_init, ncol)
write.csv(data.frame(
  sample_idx = 0:(num_samples-1),
  sample_name = unique_samples,
  n_cells = sample_sizes
), file.path(output_dir, sprintf("sample_info_%d.csv", n_cells)), row.names = FALSE)

# Save POST-INIT Bi
for (i in seq_along(Bi_init)) {
  write.csv(Bi_init[[i]],
            file.path(output_dir, sprintf("Bi_init_%d_sample%d.csv", n_cells, i-1)),
            row.names = FALSE)
}

# Save POST-INIT Qi
for (i in seq_along(Qi_init)) {
  write.csv(Qi_init[[i]],
            file.path(output_dir, sprintf("Qi_init_%d_sample%d.csv", n_cells, i-1)),
            row.names = FALSE)
}

# Save POST-INIT oi
for (i in seq_along(oi_init)) {
  write.csv(oi_init[[i]],
            file.path(output_dir, sprintf("oi_init_%d_sample%d.csv", n_cells, i-1)),
            row.names = FALSE)
}

# Save POST-INIT si
for (i in seq_along(si_init)) {
  write.csv(si_init[[i]],
            file.path(output_dir, sprintf("si_init_%d_sample%d.csv", n_cells, i-1)),
            row.names = FALSE)
}

# Save Z, D, U, S, o, sigma2
write.csv(Z_init, file.path(output_dir, sprintf("Z_init_%d.csv", n_cells)), row.names = FALSE)
write.csv(D_init, file.path(output_dir, sprintf("D_init_%d.csv", n_cells)), row.names = FALSE)
write.csv(U_init, file.path(output_dir, sprintf("U_init_%d.csv", n_cells)), row.names = FALSE)
write.csv(S_init, file.path(output_dir, sprintf("S_init_%d.csv", n_cells)), row.names = FALSE)
write.csv(o_init, file.path(output_dir, sprintf("o_init_%d.csv", n_cells)), row.names = FALSE)
write.csv(sigma2_init, file.path(output_dir, sprintf("sigma2_init_%d.csv", n_cells)), row.names = FALSE)

# Save hyperparameters
write.csv(S_o, file.path(output_dir, sprintf("hyperparams_S_o_%d.csv", n_cells)), row.names = FALSE)
write.csv(S_si, file.path(output_dir, sprintf("hyperparams_S_si_%d.csv", n_cells)), row.names = FALSE)
write.csv(S_Z, file.path(output_dir, sprintf("hyperparams_S_Z_%d.csv", n_cells)), row.names = FALSE)
write.csv(S_A, file.path(output_dir, sprintf("hyperparams_S_A_%d.csv", n_cells)), row.names = FALSE)
write.csv(S_R, file.path(output_dir, sprintf("hyperparams_S_R_%d.csv", n_cells)), row.names = FALSE)
write.csv(S_oi, file.path(output_dir, sprintf("hyperparams_S_oi_%d.csv", n_cells)), row.names = FALSE)
write.csv(S_Qi, file.path(output_dir, sprintf("hyperparams_S_Qi_%d.csv", n_cells)), row.names = FALSE)
write.csv(o_0, file.path(output_dir, sprintf("hyperparams_o_0_%d.csv", n_cells)), row.names = FALSE)

# Save si_0 per sample
for (i in seq_along(si_0)) {
  write.csv(si_0[[i]],
            file.path(output_dir, sprintf("hyperparams_si_0_%d_sample%d.csv", n_cells, i-1)),
            row.names = FALSE)
}

# Save O matrix
write.csv(O_matrix, file.path(output_dir, sprintf("hyperparams_O_%d.csv", n_cells)), row.names = FALSE)

# Run optimization on the same model
cat("\nRunning optimization (100 iterations)...\n")
model$optimize(iterations = 100, track_interval = 10)

# Extract final parameters
params_final <- model$params
Z_final <- params_final$Z
D_final <- params_final$D
sigma2_final <- params_final$sigma2
Bi_final <- params_final$Bi

# Compute DB projection
DB_final <- do.call(cbind, lapply(1:length(Bi_final), function(i) {
  sweep(Bi_final[[i]], 1, D_final, "*")
}))

cat("\nFinal values after optimization:\n")
cat("  Z:", dim(Z_final), "\n")
cat("  D:", length(D_final), "values:", head(D_final), "\n")
cat("  sigma2:", sigma2_final, "\n")

# Save final results for comparison
write.csv(Z_final, file.path(output_dir, sprintf("Z_final_%d.csv", n_cells)), row.names = FALSE)
write.csv(D_final, file.path(output_dir, sprintf("D_final_%d.csv", n_cells)), row.names = FALSE)
write.csv(sigma2_final, file.path(output_dir, sprintf("sigma2_final_%d.csv", n_cells)), row.names = FALSE)
write.csv(DB_final, file.path(output_dir, sprintf("DB_final_%d.csv", n_cells)), row.names = FALSE)

cat("\nExported POST-INIT values to:", output_dir, "\n")
cat("Files created:\n")
cat("  - cell_indices_", n_cells, ".csv\n", sep = "")
cat("  - Yi_", n_cells, "_sample*.csv (", num_samples, " files)\n", sep = "")
cat("  - sample_info_", n_cells, ".csv\n", sep = "")
cat("  - Bi_init_", n_cells, "_sample*.csv (", num_samples, " files) [POST-INIT]\n", sep = "")
cat("  - Qi_init_", n_cells, "_sample*.csv (", num_samples, " files) [POST-INIT]\n", sep = "")
cat("  - oi_init_", n_cells, "_sample*.csv (", num_samples, " files) [POST-INIT]\n", sep = "")
cat("  - si_init_", n_cells, "_sample*.csv (", num_samples, " files) [POST-INIT]\n", sep = "")
cat("  - Z_init_", n_cells, ".csv [POST-INIT]\n", sep = "")
cat("  - D_init_", n_cells, ".csv [POST-INIT]\n", sep = "")
cat("  - U_init_", n_cells, ".csv [POST-INIT] (CRITICAL for solve_Z_orthogonal)\n", sep = "")
cat("  - S_init_", n_cells, ".csv [POST-INIT] (CRITICAL for solve_Z_orthogonal)\n", sep = "")
cat("  - o_init_", n_cells, ".csv [POST-INIT]\n", sep = "")
cat("  - sigma2_init_", n_cells, ".csv [POST-INIT]\n", sep = "")
cat("  - hyperparams_*.csv files [HYPERPARAMETERS]\n", sep = "")
cat("  - Z_final_", n_cells, ".csv [FINAL after optimization]\n", sep = "")
cat("  - D_final_", n_cells, ".csv [FINAL after optimization]\n", sep = "")
cat("  - sigma2_final_", n_cells, ".csv [FINAL after optimization]\n", sep = "")
cat("  - DB_final_", n_cells, ".csv [FINAL after optimization]\n", sep = "")
