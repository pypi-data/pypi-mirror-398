#!/usr/bin/env Rscript
# preprocess_200k.R - Create 200K cell benchmark dataset from Allen Brain data
#
# This R script loads the 380K cells Allen Brain dataset and exports it
# as an intermediate format that Python can then convert to h5ad.

library(Matrix)

# Configuration
INPUT_RDS <- "/home/saberi/projects/gedi/gedi2-test/380K_cells_allen_brain_institure.rds"
OUTPUT_DIR <- "/home/saberi/projects/gedi/gedipy/benchmarks/data"
N_HVG <- 2000  # Number of highly variable genes
MAX_CELLS <- 200000  # 200K cells

cat("==================================================\n")
cat("GEDI 200K Cell Benchmark Data Preprocessing (R)\n")
cat("==================================================\n")
cat(sprintf("Input file: %s\n", INPUT_RDS))
cat(sprintf("Output dir: %s\n", OUTPUT_DIR))
cat(sprintf("Number of HVGs: %d\n", N_HVG))
cat(sprintf("Max cells: %d\n", MAX_CELLS))
cat("\n")

# Create output directory
dir.create(OUTPUT_DIR, showWarnings = FALSE, recursive = TRUE)

# Load RDS file
cat("Loading RDS file...\n")
rds_data <- readRDS(INPUT_RDS)

# Check structure
if (is.list(rds_data)) {
  cat("RDS contains a list with elements:\n")
  print(names(rds_data))
  M <- rds_data$M
  samples <- if ("samples" %in% names(rds_data)) as.character(rds_data$samples) else NULL
} else {
  M <- rds_data
  samples <- NULL
}

n_genes <- nrow(M)
n_cells <- ncol(M)

cat(sprintf("\nRaw data dimensions:\n"))
cat(sprintf("  Genes: %d\n", n_genes))
cat(sprintf("  Cells: %d\n", n_cells))

# Get gene and cell names
gene_names <- rownames(M)
if (is.null(gene_names)) gene_names <- paste0("gene_", seq_len(n_genes))
cell_names <- colnames(M)
if (is.null(cell_names)) cell_names <- paste0("cell_", seq_len(n_cells))

# Get sample labels from cell names if not provided
if (is.null(samples)) {
  samples <- sapply(strsplit(cell_names, "-"), function(x) tail(x, 1))
}

# Show sample distribution
sample_table <- table(samples)
cat("\nSample distribution:\n")
for (i in seq_len(min(10, length(sample_table)))) {
  cat(sprintf("  %s: %d\n", names(sample_table)[i], sample_table[i]))
}
if (length(sample_table) > 10) {
  cat(sprintf("  ... and %d more samples\n", length(sample_table) - 10))
}

# Subsample cells (stratified by sample)
if (n_cells > MAX_CELLS) {
  cat(sprintf("\nSubsampling to %d cells (stratified by sample)...\n", MAX_CELLS))
  set.seed(42)

  unique_samples <- names(sample_table)
  sample_props <- as.numeric(sample_table) / sum(sample_table)
  cells_per_sample <- floor(sample_props * MAX_CELLS)

  # Adjust to get exactly MAX_CELLS
  diff <- MAX_CELLS - sum(cells_per_sample)
  cells_per_sample[1] <- cells_per_sample[1] + diff

  selected_indices <- c()
  for (i in seq_along(unique_samples)) {
    s <- unique_samples[i]
    n <- cells_per_sample[i]
    sample_idx <- which(samples == s)
    if (length(sample_idx) > n) {
      selected <- sample(sample_idx, n)
    } else {
      selected <- sample_idx
    }
    selected_indices <- c(selected_indices, selected)
  }
  selected_indices <- sort(selected_indices)
  cat(sprintf("  Selected %d cells\n", length(selected_indices)))
} else {
  selected_indices <- seq_len(n_cells)
}

# Subset data
M_sub <- M[, selected_indices, drop = FALSE]
samples_sub <- samples[selected_indices]
cell_names_sub <- cell_names[selected_indices]

# Calculate HVG statistics
cat("\nSelecting highly variable genes...\n")

# Gene means and variances
gene_means <- rowMeans(M_sub)
gene_vars <- apply(M_sub, 1, var)
gene_cv2 <- gene_vars / (gene_means^2 + 1e-10)

# Filter genes with at least some expression
min_cells <- ncol(M_sub) * 0.001
gene_detection <- rowSums(M_sub > 0)
expressed_genes <- gene_detection >= min_cells

cat(sprintf("  Genes detected in >= %.0f cells: %d\n", min_cells, sum(expressed_genes)))

# Select top HVGs by CV2
cv2_filtered <- gene_cv2
cv2_filtered[!expressed_genes] <- -Inf

hvg_idx <- order(cv2_filtered, decreasing = TRUE)[1:min(N_HVG, sum(expressed_genes))]
hvg_idx <- sort(hvg_idx)  # Keep original order

hvg_names <- gene_names[hvg_idx]
cat(sprintf("  Selected %d highly variable genes\n", length(hvg_names)))

# Subset to HVGs
M_hvg <- M_sub[hvg_idx, , drop = FALSE]

cat(sprintf("\nFinal data dimensions:\n"))
cat(sprintf("  Genes: %d\n", nrow(M_hvg)))
cat(sprintf("  Cells: %d\n", ncol(M_hvg)))

# Save as RDS (for R benchmarks)
cat("\nSaving as RDS (for R)...\n")
output_list <- list(
  M = M_hvg,
  samples = samples_sub,
  hvg_names = hvg_names,
  cell_names = cell_names_sub
)
rds_out <- file.path(OUTPUT_DIR, "benchmark_data_200k.rds")
saveRDS(output_list, rds_out)
cat(sprintf("  Saved: %s\n", rds_out))

# Save components as CSV/MTX for Python to read
cat("\nExporting for Python conversion...\n")

# Save matrix as Matrix Market format
mtx_out <- file.path(OUTPUT_DIR, "benchmark_data_200k_matrix.mtx")
writeMM(M_hvg, mtx_out)
cat(sprintf("  Matrix: %s\n", mtx_out))

# Save gene names
genes_out <- file.path(OUTPUT_DIR, "benchmark_data_200k_genes.csv")
write.csv(data.frame(gene = hvg_names), genes_out, row.names = FALSE)
cat(sprintf("  Genes: %s\n", genes_out))

# Save cell metadata
cells_out <- file.path(OUTPUT_DIR, "benchmark_data_200k_cells.csv")
write.csv(data.frame(
  cell = cell_names_sub,
  sample = samples_sub
), cells_out, row.names = FALSE)
cat(sprintf("  Cells: %s\n", cells_out))

# Save selected indices for reproducibility
indices_out <- file.path(OUTPUT_DIR, "200k_cell_indices_r.csv")
write.csv(data.frame(
  original_index = selected_indices,
  cell_name = cell_names_sub,
  sample = samples_sub
), indices_out, row.names = FALSE)
cat(sprintf("  Indices: %s\n", indices_out))

# Print summary
cat("\n")
cat("==================================================\n")
cat("Preprocessing complete!\n")
cat("==================================================\n")

# File sizes
rds_size <- file.info(rds_out)$size / 1024^2
mtx_size <- file.info(mtx_out)$size / 1024^2
cat(sprintf("\nFile sizes:\n"))
cat(sprintf("  RDS: %.1f MB\n", rds_size))
cat(sprintf("  MTX: %.1f MB\n", mtx_size))

cat(sprintf("\nVerification:\n"))
cat(sprintf("  Cells: %d\n", length(samples_sub)))
cat(sprintf("  Genes: %d\n", length(hvg_names)))
cat(sprintf("  Samples: %d\n", length(unique(samples_sub))))
