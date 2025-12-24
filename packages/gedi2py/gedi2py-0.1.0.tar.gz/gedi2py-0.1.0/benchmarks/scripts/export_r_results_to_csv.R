#!/usr/bin/env Rscript
# Export R benchmark results to CSV for comparison without rpy2
#
# Usage: Rscript export_r_results_to_csv.R <n_cells> <threads> <results_dir>

suppressPackageStartupMessages({
  library(Matrix)
})

args <- commandArgs(trailingOnly = TRUE)
n_cells <- as.integer(args[1])
threads <- as.integer(args[2])
results_dir <- args[3]

cat("============================================================\n")
cat("Exporting R Results to CSV\n")
cat("============================================================\n")
cat("Cells:", n_cells, "\n")
cat("Threads:", threads, "\n")
cat("Results dir:", results_dir, "\n")

# Load R results
rds_file <- file.path(results_dir, "r",
                      sprintf("gedi_r_%dcells_%dthreads_results.rds", n_cells, threads))

if (!file.exists(rds_file)) {
  stop("RDS file not found: ", rds_file)
}

cat("Loading:", rds_file, "\n")
results <- readRDS(rds_file)

# Create CSV export directory
csv_dir <- file.path(results_dir, "r_csv")
dir.create(csv_dir, showWarnings = FALSE, recursive = TRUE)

# Export each component
cat("Exporting Z...\n")
write.csv(results$Z, file.path(csv_dir, sprintf("Z_%d_%d.csv", n_cells, threads)), row.names = FALSE)

cat("Exporting D...\n")
write.csv(results$D, file.path(csv_dir, sprintf("D_%d_%d.csv", n_cells, threads)), row.names = FALSE)

cat("Exporting sigma2...\n")
write.csv(results$sigma2, file.path(csv_dir, sprintf("sigma2_%d_%d.csv", n_cells, threads)), row.names = FALSE)

cat("Exporting DB...\n")
write.csv(results$DB, file.path(csv_dir, sprintf("DB_%d_%d.csv", n_cells, threads)), row.names = FALSE)

# Export SVD components if present
if (!is.null(results$svd_u)) {
  cat("Exporting svd_u...\n")
  write.csv(results$svd_u, file.path(csv_dir, sprintf("svd_u_%d_%d.csv", n_cells, threads)), row.names = FALSE)
}

if (!is.null(results$svd_v)) {
  cat("Exporting svd_v...\n")
  write.csv(results$svd_v, file.path(csv_dir, sprintf("svd_v_%d_%d.csv", n_cells, threads)), row.names = FALSE)
}

if (!is.null(results$svd_d)) {
  cat("Exporting svd_d...\n")
  write.csv(results$svd_d, file.path(csv_dir, sprintf("svd_d_%d_%d.csv", n_cells, threads)), row.names = FALSE)
}

# Export tracking_sigma2 if present
if (!is.null(results$tracking_sigma2)) {
  cat("Exporting tracking_sigma2...\n")
  write.csv(results$tracking_sigma2, file.path(csv_dir, sprintf("tracking_sigma2_%d_%d.csv", n_cells, threads)), row.names = FALSE)
}

cat("============================================================\n")
cat("Export complete! Files saved to:", csv_dir, "\n")
cat("============================================================\n")
