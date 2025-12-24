#!/usr/bin/env Rscript
# benchmark_r.R - Benchmark R gedi2 implementation
# Usage: Rscript benchmark_r.R <threads> <n_cells> [iterations] [output_dir]

suppressPackageStartupMessages({
  library(Matrix)
  library(gedi)
})

# Parse command line arguments
args <- commandArgs(trailingOnly = TRUE)

if (length(args) < 2) {
  stop("Usage: Rscript benchmark_r.R <threads> <n_cells> [iterations] [output_dir]")
}

n_threads <- as.integer(args[1])
n_cells <- as.integer(args[2])
iterations <- if (length(args) >= 3) as.integer(args[3]) else 100
output_dir <- if (length(args) >= 4) args[4] else "../results/r"

# Configuration
K <- 10
track_interval <- 10
random_seed <- 42

cat(strrep("=", 60), "\n")
cat("GEDI R Benchmark\n")
cat(strrep("=", 60), "\n")
cat("Threads:", n_threads, "\n")
cat("Cells:", n_cells, "\n")
cat("Latent factors (K):", K, "\n")
cat("Iterations:", iterations, "\n")
cat("Random seed:", random_seed, "\n")
cat("Output directory:", output_dir, "\n")
cat(strrep("-", 60), "\n\n")

# Create output directory
dir.create(output_dir, recursive = TRUE, showWarnings = FALSE)

# Load data
cat("[1/5] Loading data...\n")
data_path <- "/home/saberi/projects/gedi/gedi-py/benchmarks/data/benchmark_data.rds"
if (!file.exists(data_path)) {
  stop("Data file not found at: ", data_path,
       "\nPlease run preprocess_single_file.py and convert_h5ad_to_rds.R first.")
}

t_load_start <- Sys.time()
data <- readRDS(data_path)
M <- data$M
Sample_vec <- as.character(data$samples)
t_load_end <- Sys.time()
cat("  Data loaded:", nrow(M), "genes x", ncol(M), "cells\n")
cat("  Load time:", as.numeric(difftime(t_load_end, t_load_start, units = "secs")),
    "seconds\n\n")

# Subsample cells
cat("[2/5] Subsampling to", n_cells, "cells...\n")
set.seed(random_seed)
if (n_cells < ncol(M)) {
  select_idx <- sample(1:ncol(M), n_cells)
  M <- M[, select_idx, drop = FALSE]
  Sample_vec <- Sample_vec[select_idx]
}
cat("  Final matrix:", nrow(M), "genes x", ncol(M), "cells\n")

n_samples <- length(unique(Sample_vec))
cat("  Number of samples:", n_samples, "\n\n")

# Memory usage before training
gc_before <- gc(reset = TRUE)
mem_before <- sum(gc_before[, 2])

# Create GEDI model with Y input (obs_type="Y") for fair comparison with Python
cat("[3/5] Creating GEDI model with Y input (obs_type=Y)...\n")
Y <- log1p(as.matrix(M))  # Convert to dense and compute log1p
t_create_start <- Sys.time()
set.seed(random_seed)
model <- CreateGEDIObject(
  Samples = Sample_vec,
  Y = Y,  # Use Y instead of M for obs_type="Y"
  K = K,
  verbose = 1,
  num_threads = n_threads
)
t_create_end <- Sys.time()
create_time <- as.numeric(difftime(t_create_end, t_create_start, units = "secs"))
cat("  Model creation time:", create_time, "seconds\n\n")

# Train model
cat("[4/5] Training model...\n")
cat(strrep("-", 40), "\n")
t_train_start <- Sys.time()
model$train(iterations = iterations, track_interval = track_interval)
t_train_end <- Sys.time()
cat(strrep("-", 40), "\n")
training_time <- as.numeric(difftime(t_train_end, t_train_start, units = "secs"))
cat("  Training time:", training_time, "seconds\n\n")

# Memory usage after training
gc_after <- gc()
mem_after <- sum(gc_after[, 2])
peak_mem <- sum(gc_after[, 6])

# Extract results
cat("[5/5] Extracting and saving results...\n")
Z <- model$Z
params <- model$params
D <- params$D
sigma2 <- params$sigma2
Bi <- params$Bi

# Compute DB projection for comparison
cat("  Computing DB projection...\n")
# D is a vector, Bi is a list of matrices (K x Ni)
DB <- do.call(cbind, lapply(1:length(Bi), function(i) {
  sweep(Bi[[i]], 1, D, "*")  # multiply each row of Bi by corresponding D element
}))

# Compute factorized SVD embeddings
cat("  Computing factorized SVD...\n")
svd_result <- model$embeddings$svd
svd_u <- svd_result$u  # J x K (left singular vectors, genes)
svd_v <- svd_result$v  # N x K (right singular vectors, cells)
svd_d <- svd_result$d  # K (singular values)

# Save results with all 4 required outputs
output_prefix <- sprintf("gedi_r_%dcells_%dthreads", n_cells, n_threads)

saveRDS(list(
  Z = Z,
  D = D,
  sigma2 = sigma2,
  DB = DB,
  svd_u = svd_u,
  svd_v = svd_v,
  svd_d = svd_d,
  tracking_sigma2 = model$tracking$sigma2
), file.path(output_dir, paste0(output_prefix, "_results.rds")))

# Save benchmark metrics
metrics <- list(
  implementation = "R (gedi2)",
  version = as.character(packageVersion("gedi")),
  n_cells = n_cells,
  n_genes = nrow(M),
  n_samples = n_samples,
  n_threads = n_threads,
  K = K,
  iterations = iterations,
  random_seed = random_seed,
  load_time_sec = as.numeric(difftime(t_load_end, t_load_start, units = "secs")),
  create_time_sec = create_time,
  training_time_sec = training_time,
  total_time_sec = as.numeric(difftime(Sys.time(), t_load_start, units = "secs")),
  mem_before_mb = mem_before,
  mem_after_mb = mem_after,
  peak_mem_mb = peak_mem,
  final_sigma2 = sigma2
)

saveRDS(metrics, file.path(output_dir, paste0(output_prefix, "_metrics.rds")))

# Also save as JSON for easier comparison
json_metrics <- jsonlite::toJSON(metrics, auto_unbox = TRUE, pretty = TRUE)
writeLines(json_metrics, file.path(output_dir, paste0(output_prefix, "_metrics.json")))

# Print summary
cat("\n", strrep("=", 60), "\n")
cat("BENCHMARK SUMMARY\n")
cat(strrep("=", 60), "\n")
cat("Implementation:    R (gedi2 v", as.character(packageVersion("gedi")), ")\n",
    sep = "")
cat("Dataset:           ", nrow(M), " genes x ", n_cells, " cells x ",
    n_samples, " samples\n", sep = "")
cat("Threads:           ", n_threads, "\n", sep = "")
cat("Training time:     ", round(training_time, 2), " seconds\n", sep = "")
cat("Peak memory:       ", round(peak_mem, 1), " MB\n", sep = "")
cat("Final sigma2:      ", round(sigma2, 6), "\n", sep = "")
cat("Results saved to:  ", output_dir, "\n", sep = "")
cat(strrep("=", 60), "\n")
