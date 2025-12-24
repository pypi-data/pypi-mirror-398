#!/usr/bin/env Rscript
# preprocess_single_file.R - Preprocess single h5ad file for benchmarking
#
# This script processes a single h5ad file from Allen Brain Atlas
# and prepares it for R vs Python benchmarking.

library(gedi)

# Configuration
h5ad_file <- "/home/saberi/projects/gedi/gedi2_manuscript/data/Allen-brain-10X-V3/WMB-10Xv3-CB-raw.h5ad"
output_file <- "/home/saberi/projects/gedi/gedi-py/benchmarks/data/benchmark_data.rds"
n_hvg <- 2000  # Number of highly variable genes to select

cat("========================================\n")
cat("GEDI Benchmark Data Preprocessing\n")
cat("========================================\n")
cat("Input file:", h5ad_file, "\n")
cat("Output file:", output_file, "\n")
cat("Number of HVGs:", n_hvg, "\n\n")

# Create output directory
dir.create(dirname(output_file), showWarnings = FALSE, recursive = TRUE)

# Read h5ad file
cat("Reading h5ad file...\n")
data <- gedi::read_h5ad(h5ad_file, return_metadata = TRUE)

cat("Raw data dimensions:\n")
cat("  Genes:", nrow(data$X), "\n")
cat("  Cells:", ncol(data$X), "\n\n")

# Get gene names and cell barcodes
gene_names <- data$var$gene_identifier
if (is.null(gene_names)) {
  gene_names <- rownames(data$var)
}

cell_barcodes <- data$obs$cell_barcode
if (is.null(cell_barcodes)) {
  cell_barcodes <- rownames(data$obs)
}

# Add library label to make barcodes unique
if (!is.null(data$obs$library_label)) {
  cell_barcodes <- paste0(cell_barcodes, "-", data$obs$library_label)
}

# Set dimnames
dimnames(data$X) <- list(gene_names, cell_barcodes)

cat("Selecting highly variable genes...\n")

# Calculate gene statistics for HVG selection
gene_means <- Matrix::rowMeans(data$X)
gene_vars <- Matrix::rowMeans(data$X^2) - gene_means^2
gene_cv2 <- gene_vars / (gene_means^2 + 1e-10)

# Filter genes with at least some expression
min_cells <- ncol(data$X) * 0.001  # At least 0.1% of cells
gene_detection <- Matrix::rowSums(data$X > 0)
expressed_genes <- gene_detection >= min_cells

cat("  Genes detected in >=", min_cells, "cells:", sum(expressed_genes), "\n")

# Select top HVGs by CV2 among expressed genes
cv2_filtered <- gene_cv2
cv2_filtered[!expressed_genes] <- -Inf

hvg_idx <- order(cv2_filtered, decreasing = TRUE)[1:min(n_hvg, sum(expressed_genes))]
hvg_names <- gene_names[hvg_idx]

cat("  Selected", length(hvg_names), "highly variable genes\n\n")

# Subset to HVGs
M_expression <- data$X[hvg_names, , drop = FALSE]

cat("Final data dimensions:\n")
cat("  Genes:", nrow(M_expression), "\n")
cat("  Cells:", ncol(M_expression), "\n\n")

# Get sample labels (library_label is the batch identifier)
sample_labels <- data$obs$library_label
if (is.null(sample_labels)) {
  # Use a single sample if no batch info
  sample_labels <- rep("sample1", ncol(M_expression))
}
names(sample_labels) <- cell_barcodes

cat("Sample distribution:\n")
print(table(sample_labels))
cat("\n")

# Prepare output
output_data <- list(
  M = M_expression,
  samples = sample_labels,
  hvg_names = hvg_names,
  metadata = data$obs
)

# Save
cat("Saving preprocessed data...\n")
saveRDS(output_data, output_file)

# Verify
file_size <- file.info(output_file)$size / 1024^2
cat("Done! Output file size:", round(file_size, 1), "MB\n")

cat("\n========================================\n")
cat("Preprocessing complete!\n")
cat("========================================\n")
