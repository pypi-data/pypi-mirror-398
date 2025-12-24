#!/usr/bin/env Rscript
# compare_results.R - Compare R and Python GEDI results
# This script loads results from both implementations and compares them

suppressPackageStartupMessages({
  library(reticulate)
})

# Use the gedi conda environment
use_condaenv("gedi", required = TRUE)
np <- import("numpy")

results_dir <- "/home/saberi/projects/gedi/gedi-py/benchmarks/results"

# Compare 10k cells, 1 thread results
cat("=" , rep("=", 59), "\n", sep = "")
cat("Comparing R vs Python results (10000 cells, 1 thread)\n")
cat("=" , rep("=", 59), "\n\n", sep = "")

# Load R results
r_results <- readRDS(file.path(results_dir, "r", "gedi_r_10000cells_1threads_results.rds"))
cat("R results loaded:\n")
cat("  Z:", dim(r_results$Z), "\n")
cat("  D:", length(r_results$D), "\n")
cat("  sigma2:", r_results$sigma2, "\n")
cat("  DB:", dim(r_results$DB), "\n\n")

# Load Python results
py_results <- np$load(file.path(results_dir, "python", "gedi_python_10000cells_1threads_results.npz"))
py_Z <- py_results$f[["Z"]]
py_D <- py_results$f[["D"]]
py_sigma2 <- as.numeric(py_results$f[["sigma2"]])
py_DB <- py_results$f[["DB"]]

cat("Python results loaded:\n")
cat("  Z:", dim(py_Z), "\n")
cat("  D:", length(py_D), "\n")
cat("  sigma2:", py_sigma2, "\n")
cat("  DB:", dim(py_DB), "\n\n")

# Compare sigma2
cat("-" , rep("-", 59), "\n", sep = "")
cat("Sigma2 comparison:\n")
cat("  R sigma2:      ", r_results$sigma2, "\n")
cat("  Python sigma2: ", py_sigma2, "\n")
cat("  Difference:    ", abs(r_results$sigma2 - py_sigma2), "\n")
cat("  Rel. diff:     ", abs(r_results$sigma2 - py_sigma2) / r_results$sigma2 * 100, "%\n\n")

# Compare D
cat("-" , rep("-", 59), "\n", sep = "")
cat("D comparison:\n")
cat("  R D:      ", head(r_results$D), "...\n")
cat("  Python D: ", head(as.vector(py_D)), "...\n")
d_diff <- r_results$D - as.vector(py_D)
cat("  Max abs diff: ", max(abs(d_diff)), "\n")
cat("  Mean abs diff:", mean(abs(d_diff)), "\n")
cat("  Correlation:  ", cor(r_results$D, as.vector(py_D)), "\n\n")

# Compare Z (shared metagenes)
cat("-" , rep("-", 59), "\n", sep = "")
cat("Z comparison (J x K matrix):\n")
cat("  R Z range:      [", min(r_results$Z), ", ", max(r_results$Z), "]\n")
cat("  Python Z range: [", min(py_Z), ", ", max(py_Z), "]\n")
z_diff <- r_results$Z - py_Z
cat("  Max abs diff:   ", max(abs(z_diff)), "\n")
cat("  Mean abs diff:  ", mean(abs(z_diff)), "\n")

# Column-wise correlation (each latent factor)
z_cors <- sapply(1:ncol(r_results$Z), function(k) {
  cor(r_results$Z[, k], py_Z[, k])
})
cat("  Column correlations: ", paste(round(z_cors, 4), collapse = ", "), "\n\n")

# Compare DB projection
cat("-" , rep("-", 59), "\n", sep = "")
cat("DB comparison (K x N matrix):\n")
cat("  R DB range:      [", min(r_results$DB), ", ", max(r_results$DB), "]\n")
cat("  Python DB range: [", min(py_DB), ", ", max(py_DB), "]\n")

# Note: DB matrices may have different cell ordering due to subsampling
# Let's check dimensions first
if (all(dim(r_results$DB) == dim(py_DB))) {
  db_diff <- r_results$DB - py_DB
  cat("  Max abs diff:    ", max(abs(db_diff)), "\n")
  cat("  Mean abs diff:   ", mean(abs(db_diff)), "\n")

  # Row-wise correlation (each latent factor across cells)
  db_cors <- sapply(1:nrow(r_results$DB), function(k) {
    cor(r_results$DB[k, ], py_DB[k, ])
  })
  cat("  Row correlations: ", paste(round(db_cors, 4), collapse = ", "), "\n")
} else {
  cat("  Dimensions differ! R:", dim(r_results$DB), "Python:", dim(py_DB), "\n")
}

cat("\n")
cat("=" , rep("=", 59), "\n", sep = "")
