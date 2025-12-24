#!/usr/bin/env Rscript
# convert_h5ad_to_rds.R - Convert benchmark h5ad file to RDS format for R

library(gedi)

h5ad_file <- "/home/saberi/projects/gedi/gedi-py/benchmarks/data/benchmark_data.h5ad"
rds_file <- "/home/saberi/projects/gedi/gedi-py/benchmarks/data/benchmark_data.rds"

cat("Converting h5ad to RDS...\n")
cat("Input:", h5ad_file, "\n")
cat("Output:", rds_file, "\n\n")

# Read h5ad
data <- gedi::read_h5ad(h5ad_file, return_metadata = TRUE)

# Get gene names and cell barcodes from anndata
gene_names <- rownames(data$var)
cell_barcodes <- rownames(data$obs)

# Get sample labels
if ("sample" %in% colnames(data$obs)) {
  sample_labels <- data$obs$sample
} else if ("library_label" %in% colnames(data$obs)) {
  sample_labels <- data$obs$library_label
} else {
  sample_labels <- rep("sample1", ncol(data$X))
}
names(sample_labels) <- cell_barcodes

# Set matrix dimnames (genes x cells)
dimnames(data$X) <- list(gene_names, cell_barcodes)

cat("Data dimensions:\n")
cat("  Genes:", nrow(data$X), "\n")
cat("  Cells:", ncol(data$X), "\n")
cat("  Samples:", length(unique(sample_labels)), "\n\n")

# Create output
output_data <- list(
  M = data$X,
  samples = sample_labels,
  hvg_names = gene_names,
  metadata = data$obs
)

# Save
cat("Saving RDS...\n")
saveRDS(output_data, rds_file)

file_size <- file.info(rds_file)$size / 1024^2
cat("Done! File size:", round(file_size, 1), "MB\n")
