#!/bin/bash
# run_all_benchmarks.sh - Run all R vs Python GEDI benchmarks
#
# This script runs benchmarks for various cell counts and thread configurations,
# respecting the system limits (8 threads, 32GB RAM).

set -e  # Exit on error

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BENCHMARK_DIR="$(dirname "$SCRIPT_DIR")"
LOG_DIR="${BENCHMARK_DIR}/logs"
RESULTS_DIR="${BENCHMARK_DIR}/results"

# Create directories
mkdir -p "${LOG_DIR}/r" "${LOG_DIR}/python"
mkdir -p "${RESULTS_DIR}/r" "${RESULTS_DIR}/python" "${RESULTS_DIR}/comparison"

# Activate conda environment
echo "Activating conda environment 'gedi'..."
source ~/miniconda/etc/profile.d/conda.sh
conda activate gedi

# Check for psrecord
if ! command -v psrecord &> /dev/null; then
    echo "Installing psrecord..."
    pip install psrecord
fi

# Check for rpy2 (needed for Python to read RDS files)
if ! python -c "import rpy2" &> /dev/null; then
    echo "Installing rpy2..."
    pip install rpy2
fi

# Test configurations (within 8 threads, 32GB RAM limits)
# Format: "cells-threads"
TESTS=(
    "10000-1"
    "10000-4"
    "10000-8"
    "25000-1"
    "25000-4"
    "25000-8"
    "50000-1"
    "50000-4"
    "50000-8"
)

# Optional: larger tests if memory allows
# "100000-8"

echo "========================================"
echo "GEDI R vs Python Benchmark Suite"
echo "========================================"
echo "Log directory: ${LOG_DIR}"
echo "Results directory: ${RESULTS_DIR}"
echo "Tests to run: ${#TESTS[@]}"
echo ""

# Function to run a single benchmark
run_benchmark() {
    local n_cells=$1
    local n_threads=$2
    local test_name="${n_cells}cells_${n_threads}threads"

    echo "----------------------------------------"
    echo "Running benchmark: ${test_name}"
    echo "  Cells: ${n_cells}"
    echo "  Threads: ${n_threads}"
    echo "----------------------------------------"

    # Run R benchmark
    echo ""
    echo "[R] Starting benchmark..."
    local r_log="${LOG_DIR}/r/${test_name}.log"
    local r_psrecord="${LOG_DIR}/r/${test_name}_psrecord.txt"

    # Create wrapper script for psrecord
    local r_wrapper="/tmp/run_r_${test_name}.sh"
    cat > "${r_wrapper}" << EOF
#!/bin/bash
cd "${SCRIPT_DIR}"
Rscript benchmark_r.R ${n_threads} ${n_cells} "${RESULTS_DIR}/r"
EOF
    chmod +x "${r_wrapper}"

    # Run with psrecord
    psrecord --log "${r_psrecord}" --interval 1 --include-children \
        -- "${r_wrapper}" > "${r_log}" 2>&1 || {
        echo "[R] ERROR: Benchmark failed. Check ${r_log}"
        cat "${r_log}"
        rm -f "${r_wrapper}"
        return 1
    }
    rm -f "${r_wrapper}"
    echo "[R] Completed. Log: ${r_log}"

    # Run Python benchmark
    echo ""
    echo "[Python] Starting benchmark..."
    local py_log="${LOG_DIR}/python/${test_name}.log"
    local py_psrecord="${LOG_DIR}/python/${test_name}_psrecord.txt"

    # Create wrapper script for psrecord
    local py_wrapper="/tmp/run_python_${test_name}.sh"
    cat > "${py_wrapper}" << EOF
#!/bin/bash
cd "${SCRIPT_DIR}"
python benchmark_python.py ${n_threads} ${n_cells} "${RESULTS_DIR}/python"
EOF
    chmod +x "${py_wrapper}"

    # Run with psrecord
    psrecord --log "${py_psrecord}" --interval 1 --include-children \
        -- "${py_wrapper}" > "${py_log}" 2>&1 || {
        echo "[Python] ERROR: Benchmark failed. Check ${py_log}"
        cat "${py_log}"
        rm -f "${py_wrapper}"
        return 1
    }
    rm -f "${py_wrapper}"
    echo "[Python] Completed. Log: ${py_log}"

    # Compare results
    echo ""
    echo "[Compare] Comparing results..."
    local compare_log="${LOG_DIR}/${test_name}_comparison.log"
    python compare_results.py ${n_cells} ${n_threads} "${RESULTS_DIR}" > "${compare_log}" 2>&1 || {
        echo "[Compare] WARNING: Comparison had issues. Check ${compare_log}"
    }
    echo "[Compare] Completed. Log: ${compare_log}"

    echo ""
}

# Check if data exists
DATA_FILE="${SCRIPT_DIR}/../../gedi2_manuscript/data/WMB_ATLAS_10X_V3.rds"
if [ ! -f "${DATA_FILE}" ]; then
    echo "ERROR: Data file not found: ${DATA_FILE}"
    echo "Please run: bash download_data.sh"
    exit 1
fi

# Run all benchmarks
TOTAL_START=$(date +%s)

for test in "${TESTS[@]}"; do
    n_cells=$(echo "$test" | cut -d'-' -f1)
    n_threads=$(echo "$test" | cut -d'-' -f2)

    TEST_START=$(date +%s)
    run_benchmark "$n_cells" "$n_threads"
    TEST_END=$(date +%s)

    echo "Test ${test} completed in $((TEST_END - TEST_START)) seconds"
    echo ""
done

TOTAL_END=$(date +%s)
TOTAL_TIME=$((TOTAL_END - TOTAL_START))

echo "========================================"
echo "All benchmarks completed!"
echo "Total time: ${TOTAL_TIME} seconds ($(echo "scale=2; ${TOTAL_TIME}/60" | bc) minutes)"
echo "========================================"
echo ""
echo "Results saved to: ${RESULTS_DIR}"
echo "Logs saved to: ${LOG_DIR}"
echo ""
echo "To view comparison summaries:"
echo "  cat ${RESULTS_DIR}/comparison/*_summary.json"
