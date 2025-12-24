#!/usr/bin/env Rscript
# GEDI R Benchmark for Validation
# Usage: Rscript benchmark_validation_r.R <threads> <n_cells> <iterations> <output_dir>
#
# This script runs the R GEDI implementation and exports results in CSV format
# for cross-language comparison with Python.

suppressPackageStartupMessages({
  library(Matrix)
  library(gedi)  # gedi v2.2.9 from conda env 'gedi'
  library(jsonlite)
  library(RcppParallel)
})

args <- commandArgs(trailingOnly = TRUE)
if (length(args) != 4) {
  stop("Usage: Rscript benchmark_validation_r.R <threads> <n_cells> <iterations> <output_dir>")
}

threads <- as.integer(args[1])
n_cells <- as.integer(args[2])
iterations <- as.integer(args[3])
output_dir <- args[4]

K <- 10
random_seed <- 42
track_interval <- 10

cat("============================================================\n")
cat("GEDI R Benchmark for Validation\n")
cat("============================================================\n")
cat("Threads:    ", threads, "\n")
cat("Cells:      ", n_cells, "\n")
cat("Iterations: ", iterations, "\n")
cat("K:          ", K, "\n")
cat("Output:     ", output_dir, "\n")
cat("------------------------------------------------------------\n\n")

# Set threads
RcppParallel::setThreadOptions(numThreads = threads)

# Load data
data_dir <- "/home/saberi/projects/gedi/gedipy/benchmarks/data"
if (n_cells > 100000) {
  data_path <- file.path(data_dir, "benchmark_data_200k.rds")
} else {
  data_path <- file.path(data_dir, "benchmark_data.rds")
}

cat("Loading data from:", data_path, "\n")
data <- readRDS(data_path)
M <- data$M
Sample_vec <- as.character(data$samples)

cat("  Data loaded:", nrow(M), "genes x", ncol(M), "cells\n")

# Subsample cells with fixed seed for reproducibility
cat("Subsampling to", n_cells, "cells (seed=42)...\n")
set.seed(random_seed)
if (n_cells < ncol(M)) {
  select_idx <- sort(sample(1:ncol(M), n_cells))
  M <- M[, select_idx, drop = FALSE]
  Sample_vec <- Sample_vec[select_idx]
} else {
  select_idx <- 1:ncol(M)
}

J <- nrow(M)
N <- ncol(M)
num_samples <- length(unique(Sample_vec))

cat("Final matrix:", J, "genes x", N, "cells\n")
cat("Number of samples:", num_samples, "\n\n")

# Create output directory
dir.create(output_dir, showWarnings = FALSE, recursive = TRUE)

# Export cell indices so Python uses identical cells
write.csv(data.frame(idx = select_idx), file.path(output_dir, "cell_indices.csv"), row.names = FALSE)
cat("Exported cell indices for Python synchronization\n\n")

# Convert to Y (log-transformed) - CRITICAL for matching Python!
Y <- log1p(as.matrix(M))

# Create GEDI model with log-transformed data
cat("[Step 1/4] Creating and initializing GEDI model...\n")
set.seed(random_seed)

t_init_start <- Sys.time()
model <- CreateGEDIObject(
  Samples = Sample_vec,
  Y = Y,  # Use pre-computed Y for consistency with old working version
  K = K,
  verbose = 1,
  num_threads = threads
)
model$initialize_lvs()
t_init_end <- Sys.time()
init_time <- as.numeric(difftime(t_init_end, t_init_start, units = "secs"))
cat("  Initialize time:", round(init_time, 2), "seconds\n\n")

# Export POST-INIT values for Python synchronization
cat("[Step 2/4] Exporting POST-INIT values for Python...\n")
init_dir <- file.path(output_dir, "init")
dir.create(init_dir, showWarnings = FALSE, recursive = TRUE)

params <- model$params
hyperparams <- model$hyperparams

# Export initialized parameters
write.csv(params$Z, file.path(init_dir, "Z_init.csv"), row.names = FALSE)
write.csv(params$D, file.path(init_dir, "D_init.csv"), row.names = FALSE)
write.csv(params$U, file.path(init_dir, "U_init.csv"), row.names = FALSE)
write.csv(params$S, file.path(init_dir, "S_init.csv"), row.names = FALSE)
write.csv(params$o, file.path(init_dir, "o_init.csv"), row.names = FALSE)
write.csv(params$sigma2, file.path(init_dir, "sigma2_init.csv"), row.names = FALSE)

# Export per-sample parameters
Bi_init <- params$Bi
Qi_init <- params$Qi
si_init <- params$si
oi_init <- params$oi

for (i in seq_along(Bi_init)) {
  write.csv(Bi_init[[i]], file.path(init_dir, sprintf("Bi_init_sample%d.csv", i-1)), row.names = FALSE)
  write.csv(Qi_init[[i]], file.path(init_dir, sprintf("Qi_init_sample%d.csv", i-1)), row.names = FALSE)
  write.csv(si_init[[i]], file.path(init_dir, sprintf("si_init_sample%d.csv", i-1)), row.names = FALSE)
  write.csv(oi_init[[i]], file.path(init_dir, sprintf("oi_init_sample%d.csv", i-1)), row.names = FALSE)
}

# Export Yi matrices (log-transformed data per sample)
unique_samples <- unique(Sample_vec)
for (i in seq_along(unique_samples)) {
  s <- unique_samples[i]
  idx <- which(Sample_vec == s)
  Mi <- M[, idx, drop = FALSE]
  Yi <- log1p(as.matrix(Mi))
  write.csv(Yi, file.path(init_dir, sprintf("Yi_sample%d.csv", i-1)), row.names = FALSE)
}

# Export sample mapping
sample_info <- data.frame(
  sample_idx = 0:(num_samples-1),
  sample_name = unique_samples,
  n_cells = sapply(Bi_init, ncol)
)
write.csv(sample_info, file.path(init_dir, "sample_info.csv"), row.names = FALSE)

# Export hyperparameters (CRITICAL for identical results!)
write.csv(hyperparams$S_Z, file.path(init_dir, "hyperparams_S_Z.csv"), row.names = FALSE)
write.csv(1.0, file.path(init_dir, "hyperparams_S_A.csv"), row.names = FALSE)  # Default
write.csv(1.0, file.path(init_dir, "hyperparams_S_R.csv"), row.names = FALSE)  # Default
write.csv(hyperparams$S_o, file.path(init_dir, "hyperparams_S_o.csv"), row.names = FALSE)
write.csv(hyperparams$S_si, file.path(init_dir, "hyperparams_S_si.csv"), row.names = FALSE)
write.csv(hyperparams$S_oi, file.path(init_dir, "hyperparams_S_oi.csv"), row.names = FALSE)
write.csv(hyperparams$S_Qi, file.path(init_dir, "hyperparams_S_Qi.csv"), row.names = FALSE)
write.csv(hyperparams$o_0, file.path(init_dir, "hyperparams_o_0.csv"), row.names = FALSE)

# Generate O matrix for randomized SVD (same seed as model creation)
set.seed(random_seed)
O_matrix <- matrix(rnorm(N * (K + 5)), nrow = N, ncol = K + 5)
write.csv(O_matrix, file.path(init_dir, "hyperparams_O.csv"), row.names = FALSE)

# Export si_0 per sample
for (i in seq_along(hyperparams$si_0)) {
  write.csv(hyperparams$si_0[[i]], file.path(init_dir, sprintf("hyperparams_si_0_sample%d.csv", i-1)), row.names = FALSE)
}

cat("  Exported POST-INIT values to:", init_dir, "\n\n")

# Run optimization
cat("[Step 3/4] Running optimization for", iterations, "iterations...\n")
t_opt_start <- Sys.time()
model$optimize(iterations = iterations, track_interval = track_interval)
t_opt_end <- Sys.time()
opt_time <- as.numeric(difftime(t_opt_end, t_opt_start, units = "secs"))
cat("  Optimize time:", round(opt_time, 2), "seconds\n\n")

# Extract results
cat("[Step 4/4] Extracting and exporting results...\n")

# Get final values
Z <- model$Z  # J x K
D <- model$params$D  # K vector
sigma2 <- model$params$sigma2
Bi <- model$params$Bi  # List of K x Ni matrices

# Compute DB projection (K x N) - concatenate D*Bi across samples
DB <- do.call(cbind, lapply(1:length(Bi), function(i) {
  sweep(Bi[[i]], 1, D, "*")
}))

# Compute SVD of embeddings
svd_result <- model$embeddings$svd
svd_u <- svd_result$u  # J x K
svd_v <- svd_result$v  # N x K
svd_d <- svd_result$d  # K vector

# Export results as CSV for cross-language comparison
cat("  Saving Z (", nrow(Z), "x", ncol(Z), ")...\n")
write.csv(Z, file.path(output_dir, "Z.csv"), row.names = FALSE)

cat("  Saving DB (", nrow(DB), "x", ncol(DB), ")...\n")
# Transpose DB to N x K for easier comparison (cells as rows)
write.csv(t(DB), file.path(output_dir, "DB.csv"), row.names = FALSE)

cat("  Saving svd_u (", nrow(svd_u), "x", ncol(svd_u), ")...\n")
write.csv(svd_u, file.path(output_dir, "svd_u.csv"), row.names = FALSE)

cat("  Saving svd_v (", nrow(svd_v), "x", ncol(svd_v), ")...\n")
write.csv(svd_v, file.path(output_dir, "svd_v.csv"), row.names = FALSE)

# Save sample values for report (first 5 values of each parameter)
sample_values <- list(
  Z_sample = Z[1:min(5, nrow(Z)), 1:min(3, ncol(Z))],
  DB_sample = DB[1:min(3, nrow(DB)), 1:min(5, ncol(DB))],
  svd_u_sample = svd_u[1:min(5, nrow(svd_u)), 1:min(3, ncol(svd_u))],
  svd_v_sample = svd_v[1:min(5, nrow(svd_v)), 1:min(3, ncol(svd_v))]
)

# Save metrics as JSON
metrics <- list(
  language = "R",
  package = "gedi",
  threads = threads,
  n_cells = n_cells,
  n_genes = J,
  n_samples = num_samples,
  K = K,
  iterations = iterations,
  init_time_sec = round(init_time, 3),
  opt_time_sec = round(opt_time, 3),
  total_time_sec = round(init_time + opt_time, 3),
  final_sigma2 = sigma2,
  Z_shape = dim(Z),
  DB_shape = dim(DB),
  svd_u_shape = dim(svd_u),
  svd_v_shape = dim(svd_v),
  sample_values = sample_values
)

write_json(metrics, file.path(output_dir, "metrics.json"), auto_unbox = TRUE, pretty = TRUE)

# Also save full results as RDS for detailed analysis
saveRDS(list(
  Z = Z,
  D = D,
  DB = DB,
  svd_u = svd_u,
  svd_v = svd_v,
  svd_d = svd_d,
  sigma2 = sigma2,
  tracking = model$tracking
), file.path(output_dir, "full_results.rds"))

cat("\n============================================================\n")
cat("R BENCHMARK COMPLETE\n")
cat("============================================================\n")
cat("Initialize time: ", round(init_time, 2), " seconds\n")
cat("Optimize time:   ", round(opt_time, 2), " seconds\n")
cat("Total time:      ", round(init_time + opt_time, 2), " seconds\n")
cat("Final sigma2:    ", sigma2, "\n")
cat("\nOutput files:\n")
cat("  - Z.csv (", nrow(Z), " x ", ncol(Z), ")\n")
cat("  - DB.csv (", ncol(DB), " x ", nrow(DB), ") [N x K]\n")
cat("  - svd_u.csv (", nrow(svd_u), " x ", ncol(svd_u), ")\n")
cat("  - svd_v.csv (", nrow(svd_v), " x ", ncol(svd_v), ")\n")
cat("  - metrics.json\n")
cat("  - cell_indices.csv\n")
cat("============================================================\n")
