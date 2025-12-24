# gedi-py vs gedi2 (R) Benchmark Comparison

This directory contains scripts for comparing the Python (gedi-py) and R (gedi2) implementations of GEDI.

## Objective

Compare the two implementations for:
1. **Numerical accuracy**: Results should be identical given the same input and random seed
2. **Performance**: CPU time, wall-clock time, and memory usage
3. **Scalability**: Performance across different dataset sizes and thread counts

## System Requirements

- 8 threads
- 32 GB RAM
- Conda environment: `gedi`

## Test Matrix

Based on available resources (8 threads, 32GB RAM), we'll run the following tests:

| Test ID | Cells  | Threads | Est. Memory | Skip |
|---------|--------|---------|-------------|------|
| 1       | 10,000 | 1       | ~4GB        | No   |
| 2       | 10,000 | 4       | ~4GB        | No   |
| 3       | 10,000 | 8       | ~4GB        | No   |
| 4       | 25,000 | 1       | ~8GB        | No   |
| 5       | 25,000 | 4       | ~8GB        | No   |
| 6       | 25,000 | 8       | ~8GB        | No   |
| 7       | 50,000 | 1       | ~16GB       | No   |
| 8       | 50,000 | 4       | ~16GB       | No   |
| 9       | 50,000 | 8       | ~16GB       | No   |
| 10      | 100,000| 8       | ~32GB       | No   |
| 11      | 200,000| 16      | ~64GB       | YES  |
| 12      | 500,000| 32      | ~150GB      | YES  |

## Directory Structure

```
benchmarks/
├── README.md                  # This file
├── scripts/
│   ├── download_data.sh       # Download Allen Brain Atlas data
│   ├── preprocess_data.R      # Preprocess data for benchmarking
│   ├── benchmark_r.R          # R benchmark script
│   ├── benchmark_python.py    # Python benchmark script
│   ├── run_all_benchmarks.sh  # Run all benchmarks
│   └── compare_results.py     # Compare numerical results
├── logs/
│   ├── r/                     # R console output and psrecord logs
│   └── python/                # Python console output and psrecord logs
└── results/
    ├── r/                     # R model outputs
    ├── python/                # Python model outputs
    └── comparison/            # Comparison plots and tables
```

## Running Benchmarks

### 1. Setup Environment

```bash
conda activate gedi
```

### 2. Download Data

```bash
cd scripts
bash download_data.sh
```

### 3. Preprocess Data

```bash
Rscript preprocess_data.R
```

### 4. Run Benchmarks

```bash
# Run all benchmarks
bash run_all_benchmarks.sh

# Or run individual benchmarks
psrecord --log ../logs/r/test_10k_8t.txt --interval 1 --include-children \
    -- Rscript benchmark_r.R 8 10000

psrecord --log ../logs/python/test_10k_8t.txt --interval 1 --include-children \
    -- python benchmark_python.py 8 10000
```

### 5. Compare Results

```bash
python compare_results.py
```

## Metrics Collected

### Performance Metrics (via psrecord)
- CPU usage (%)
- Memory usage (MB/GB)
- Wall-clock time (seconds)

### Numerical Accuracy Metrics
- Correlation of Z matrices (shared metagenes)
- Correlation of cell embeddings (DB)
- Sigma2 (noise variance) comparison
- Frobenius norm of differences

## Expected Outcomes

1. **Numerical accuracy**: R² > 0.99 for Z and DB matrices (with same random seed)
2. **Performance**: Python should be comparable to R (both use C++ backends)
3. **Memory**: Similar memory footprint (both use Eigen)
