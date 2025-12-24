#!/usr/bin/env Rscript
# GEDI R Benchmark with POST-INIT export
# This script runs R benchmark AND exports the POST-INIT values used,
# so Python can start from the exact same initial state.

suppressPackageStartupMessages({
  library(Matrix)
  library(gedi)
})

args <- commandArgs(trailingOnly = TRUE)
threads <- as.integer(args[1])
n_cells <- as.integer(args[2])
iterations <- as.integer(args[3])
output_dir <- args[4]

K <- 10
random_seed <- 42
track_interval <- 1

cat("============================================================\n")
cat("GEDI R Benchmark (with POST-INIT export)\n")
cat("============================================================\n")
cat("Threads:", threads, "\n")
cat("Cells:", n_cells, "\n")
cat("Iterations:", iterations, "\n")
cat("Output:", output_dir, "\n")
cat("------------------------------------------------------------\n\n")

# Set threads
RcppParallel::setThreadOptions(numThreads = threads)

# Load data
data_path <- "/home/saberi/projects/gedi/gedi-py/benchmarks/data/benchmark_data.rds"
cat("Loading data from:", data_path, "\n")
data <- readRDS(data_path)
M <- data$M
Sample_vec <- as.character(data$samples)

cat("  Data loaded:", nrow(M), "genes x", ncol(M), "cells\n")

# Subsample cells
cat("Subsampling to", n_cells, "cells...\n")
set.seed(random_seed)
if (n_cells < ncol(M)) {
  select_idx <- sample(1:ncol(M), n_cells)
  M <- M[, select_idx, drop = FALSE]
  Sample_vec <- Sample_vec[select_idx]
}

J <- nrow(M)
N <- ncol(M)
num_samples <- length(unique(Sample_vec))

cat("Final matrix:", J, "genes x", N, "cells\n")
cat("Number of samples:", num_samples, "\n\n")

# Convert to Y (log-transformed) - same as benchmark_r.R
Y <- log1p(as.matrix(M))

# Create model
cat("Creating GEDI model: J =", J, ", N =", N, ", K =", K, ", samples =", num_samples, "\n\n")
set.seed(random_seed)
model <- CreateGEDIObject(
  Samples = Sample_vec,
  Y = Y,
  K = K,
  verbose = 1,
  num_threads = threads
)

# Run initialize only
cat("[Step 1/3] Running initialize...\n")
t_init_start <- Sys.time()
model$initialize_lvs()
t_init_end <- Sys.time()
init_time <- as.numeric(difftime(t_init_end, t_init_start, units = "secs"))
cat("  Initialize time:", init_time, "seconds\n")

# Export POST-INIT values
cat("\n[Step 2/3] Exporting POST-INIT values...\n")
export_dir <- "/home/saberi/projects/gedi/gedi-py/benchmarks/data/r_init"
dir.create(export_dir, showWarnings = FALSE, recursive = TRUE)

# Get parameters
params <- model$params
hyperparams <- model$hyperparams

# Save Z, D, U, S, o, sigma2
write.csv(params$Z, file.path(export_dir, sprintf("Z_init_%d.csv", n_cells)), row.names = FALSE)
write.csv(params$D, file.path(export_dir, sprintf("D_init_%d.csv", n_cells)), row.names = FALSE)
write.csv(params$U, file.path(export_dir, sprintf("U_init_%d.csv", n_cells)), row.names = FALSE)
write.csv(params$S, file.path(export_dir, sprintf("S_init_%d.csv", n_cells)), row.names = FALSE)
write.csv(params$o, file.path(export_dir, sprintf("o_init_%d.csv", n_cells)), row.names = FALSE)
write.csv(params$sigma2, file.path(export_dir, sprintf("sigma2_init_%d.csv", n_cells)), row.names = FALSE)

# Save per-sample parameters
Bi_init <- params$Bi
Qi_init <- params$Qi
si_init <- params$si
oi_init <- params$oi

for (i in seq_along(Bi_init)) {
  write.csv(Bi_init[[i]], file.path(export_dir, sprintf("Bi_init_%d_sample%d.csv", n_cells, i-1)), row.names = FALSE)
  write.csv(Qi_init[[i]], file.path(export_dir, sprintf("Qi_init_%d_sample%d.csv", n_cells, i-1)), row.names = FALSE)
  write.csv(si_init[[i]], file.path(export_dir, sprintf("si_init_%d_sample%d.csv", n_cells, i-1)), row.names = FALSE)
  write.csv(oi_init[[i]], file.path(export_dir, sprintf("oi_init_%d_sample%d.csv", n_cells, i-1)), row.names = FALSE)
}

# Save Yi matrices (compute from raw data, same as R does internally)
unique_samples <- unique(Sample_vec)
Yi_list <- list()
for (s in unique_samples) {
  idx <- which(Sample_vec == s)
  Mi <- M[, idx, drop = FALSE]
  Yi_list[[length(Yi_list) + 1]] <- log1p(as.matrix(Mi))
}

for (i in seq_along(Yi_list)) {
  write.csv(Yi_list[[i]], file.path(export_dir, sprintf("Yi_%d_sample%d.csv", n_cells, i-1)), row.names = FALSE)
}

# Save sample info
sample_sizes <- sapply(Bi_init, ncol)
sample_info <- data.frame(
  sample_idx = 0:(num_samples-1),
  sample_name = unique_samples,
  n_cells = sample_sizes
)
write.csv(sample_info, file.path(export_dir, sprintf("sample_info_%d.csv", n_cells)), row.names = FALSE)

# Save hyperparameters
# Some hyperparams come from model, others need to be computed (matching export_r_init.R)
S_A <- 1.0  # Default shrinkage
S_R <- 1.0  # Default shrinkage

# Generate O matrix for randomized SVD (same seed as model creation)
set.seed(random_seed)
O_matrix <- matrix(rnorm(N * (K + 5)), nrow = N, ncol = K + 5)

write.csv(hyperparams$S_Z, file.path(export_dir, sprintf("hyperparams_S_Z_%d.csv", n_cells)), row.names = FALSE)
write.csv(S_A, file.path(export_dir, sprintf("hyperparams_S_A_%d.csv", n_cells)), row.names = FALSE)
write.csv(S_R, file.path(export_dir, sprintf("hyperparams_S_R_%d.csv", n_cells)), row.names = FALSE)
write.csv(hyperparams$S_o, file.path(export_dir, sprintf("hyperparams_S_o_%d.csv", n_cells)), row.names = FALSE)
write.csv(hyperparams$S_si, file.path(export_dir, sprintf("hyperparams_S_si_%d.csv", n_cells)), row.names = FALSE)
write.csv(hyperparams$S_oi, file.path(export_dir, sprintf("hyperparams_S_oi_%d.csv", n_cells)), row.names = FALSE)
write.csv(hyperparams$S_Qi, file.path(export_dir, sprintf("hyperparams_S_Qi_%d.csv", n_cells)), row.names = FALSE)
write.csv(hyperparams$o_0, file.path(export_dir, sprintf("hyperparams_o_0_%d.csv", n_cells)), row.names = FALSE)
write.csv(O_matrix, file.path(export_dir, sprintf("hyperparams_O_%d.csv", n_cells)), row.names = FALSE)

for (i in seq_along(hyperparams$si_0)) {
  write.csv(hyperparams$si_0[[i]], file.path(export_dir, sprintf("hyperparams_si_0_%d_sample%d.csv", n_cells, i-1)), row.names = FALSE)
}

cat("  Exported POST-INIT values to:", export_dir, "\n")

# Run optimize
cat("\n[Step 3/3] Running optimize for", iterations, "iterations...\n")
t_opt_start <- Sys.time()
model$optimize(iterations = iterations, track_interval = track_interval)
t_opt_end <- Sys.time()
opt_time <- as.numeric(difftime(t_opt_end, t_opt_start, units = "secs"))
cat("  Optimize time:", opt_time, "seconds\n")

# Extract and save results
cat("\nSaving results...\n")
dir.create(output_dir, showWarnings = FALSE, recursive = TRUE)

# Get final values
Z <- model$Z
D <- model$params$D
sigma2 <- model$params$sigma2
Bi <- model$params$Bi

# Compute DB projection
DB <- do.call(cbind, lapply(1:length(Bi), function(i) {
  sweep(Bi[[i]], 1, D, "*")
}))

# Compute SVD
svd_result <- model$embeddings$svd
svd_u <- svd_result$u
svd_v <- svd_result$v
svd_d <- svd_result$d

# Get tracking
tracking <- model$tracking
tracking_sigma2 <- tracking$sigma2

output_prefix <- sprintf("gedi_r_%dcells_%dthreads", n_cells, threads)

saveRDS(list(
  Z = Z,
  D = D,
  sigma2 = sigma2,
  DB = DB,
  svd_u = svd_u,
  svd_v = svd_v,
  svd_d = svd_d,
  tracking_sigma2 = tracking_sigma2
), file.path(output_dir, paste0(output_prefix, "_results.rds")))

# Save timing metrics
metrics <- list(
  threads = threads,
  n_cells = n_cells,
  iterations = iterations,
  init_time = init_time,
  opt_time = opt_time,
  total_time = init_time + opt_time,
  final_sigma2 = sigma2
)
jsonlite::write_json(metrics, file.path(output_dir, paste0(output_prefix, "_metrics.json")), pretty = TRUE)

cat("\n============================================================\n")
cat("BENCHMARK COMPLETE\n")
cat("============================================================\n")
cat("Initialize time:", init_time, "seconds\n")
cat("Optimize time:", opt_time, "seconds\n")
cat("Total time:", init_time + opt_time, "seconds\n")
cat("Final sigma2:", sigma2, "\n")
cat("============================================================\n")
