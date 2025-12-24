#!/bin/bash
#
# run_comparison.sh - Run R vs Python GEDI comparison benchmarks
#
# Usage: ./run_comparison.sh <threads> <n_cells> [iterations]
#
# Example:
#   ./run_comparison.sh 8 10000 100      # Small config
#   ./run_comparison.sh 16 200000 500    # Large config
#

set -e

# Default values
THREADS=${1:-8}
N_CELLS=${2:-10000}
ITERATIONS=${3:-100}
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RESULTS_DIR="${SCRIPT_DIR}/../results"

echo "============================================================"
echo "GEDI R vs Python Comparison Benchmark"
echo "============================================================"
echo "Configuration:"
echo "  Threads:    $THREADS"
echo "  Cells:      $N_CELLS"
echo "  Iterations: $ITERATIONS"
echo "  Results:    $RESULTS_DIR"
echo "============================================================"
echo

# Create results directories
mkdir -p "$RESULTS_DIR/r"
mkdir -p "$RESULTS_DIR/python"
mkdir -p "$RESULTS_DIR/comparison"

# Check if data exists
if [ ! -f "${SCRIPT_DIR}/../data/benchmark_data.h5ad" ]; then
    echo "ERROR: benchmark_data.h5ad not found!"
    echo "Please run: python preprocess_single_file.py"
    exit 1
fi

if [ ! -f "${SCRIPT_DIR}/../data/benchmark_data.rds" ]; then
    echo "ERROR: benchmark_data.rds not found!"
    echo "Please run: python preprocess_single_file.py"
    exit 1
fi

# Run R benchmark
echo "[1/3] Running R benchmark..."
echo "------------------------------------------------------------"
/usr/bin/time -v Rscript "${SCRIPT_DIR}/benchmark_r.R" \
    $THREADS $N_CELLS $ITERATIONS "$RESULTS_DIR/r" \
    2>&1 | tee "$RESULTS_DIR/r/gedi_r_${N_CELLS}cells_${THREADS}threads_time.log"
echo

# Run Python benchmark
echo "[2/3] Running Python benchmark..."
echo "------------------------------------------------------------"
/usr/bin/time -v python "${SCRIPT_DIR}/benchmark_python.py" \
    $THREADS $N_CELLS $ITERATIONS "$RESULTS_DIR/python" \
    2>&1 | tee "$RESULTS_DIR/python/gedi_python_${N_CELLS}cells_${THREADS}threads_time.log"
echo

# Run comparison
echo "[3/3] Running comparison..."
echo "------------------------------------------------------------"
python "${SCRIPT_DIR}/compare_results.py" $N_CELLS $THREADS "$RESULTS_DIR"
echo

echo "============================================================"
echo "COMPARISON COMPLETE"
echo "============================================================"
echo "Results saved to: $RESULTS_DIR"
echo
echo "Output files:"
echo "  R results:      $RESULTS_DIR/r/gedi_r_${N_CELLS}cells_${THREADS}threads_results.rds"
echo "  Python results: $RESULTS_DIR/python/gedi_python_${N_CELLS}cells_${THREADS}threads_results.npz"
echo "  Comparison:     $RESULTS_DIR/comparison/${N_CELLS}cells_${THREADS}threads_summary.json"
echo "  Plots:          $RESULTS_DIR/comparison/${N_CELLS}cells_${THREADS}threads_*.png"
echo "============================================================"
