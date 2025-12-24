#!/bin/bash
# GEDI R vs Python Validation Benchmark Runner
# This script runs both R and Python implementations and validates identical results.

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
RESULTS_DIR="$SCRIPT_DIR/../results"
DATA_DIR="$SCRIPT_DIR/../data"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "============================================================"
echo "GEDI R vs Python Validation Benchmark"
echo "============================================================"
echo ""
echo "Script directory: $SCRIPT_DIR"
echo "Results directory: $RESULTS_DIR"
echo "Data directory: $DATA_DIR"
echo ""

# Check for required data files
if [ ! -f "$DATA_DIR/benchmark_data.h5ad" ]; then
    echo -e "${RED}ERROR: benchmark_data.h5ad not found${NC}"
    echo "Please run preprocessing first."
    exit 1
fi

if [ ! -f "$DATA_DIR/benchmark_data.rds" ]; then
    echo -e "${RED}ERROR: benchmark_data.rds not found${NC}"
    echo "Please run preprocessing first."
    exit 1
fi

# Create output directories
mkdir -p "$RESULTS_DIR/small/r"
mkdir -p "$RESULTS_DIR/small/python"
mkdir -p "$RESULTS_DIR/large/r"
mkdir -p "$RESULTS_DIR/large/python"

# Function to run a configuration
run_config() {
    local config_name="$1"
    local threads="$2"
    local n_cells="$3"
    local iterations="$4"
    local output_base="$5"

    echo ""
    echo "============================================================"
    echo "Running: $config_name"
    echo "============================================================"
    echo "  Threads:    $threads"
    echo "  Cells:      $n_cells"
    echo "  Iterations: $iterations"
    echo ""

    # Run R benchmark
    echo -e "${YELLOW}>>> Running R benchmark...${NC}"
    Rscript "$SCRIPT_DIR/benchmark_validation_r.R" \
        "$threads" "$n_cells" "$iterations" "$output_base/r"

    if [ $? -ne 0 ]; then
        echo -e "${RED}R benchmark failed${NC}"
        return 1
    fi
    echo -e "${GREEN}R benchmark complete${NC}"

    # Run Python benchmark
    echo ""
    echo -e "${YELLOW}>>> Running Python benchmark...${NC}"
    python "$SCRIPT_DIR/benchmark_validation_python.py" \
        "$threads" "$n_cells" "$iterations" "$output_base/python"

    if [ $? -ne 0 ]; then
        echo -e "${RED}Python benchmark failed${NC}"
        return 1
    fi
    echo -e "${GREEN}Python benchmark complete${NC}"

    # Validate results
    echo ""
    echo -e "${YELLOW}>>> Validating results...${NC}"
    python "$SCRIPT_DIR/validate_identical.py" "$output_base" "$config_name"

    if [ $? -ne 0 ]; then
        echo -e "${RED}Validation FAILED for $config_name${NC}"
        return 1
    fi
    echo -e "${GREEN}Validation PASSED for $config_name${NC}"

    return 0
}

# Parse command line arguments
RUN_SMALL=true
RUN_LARGE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --small-only)
            RUN_SMALL=true
            RUN_LARGE=false
            shift
            ;;
        --large-only)
            RUN_SMALL=false
            RUN_LARGE=true
            shift
            ;;
        --both)
            RUN_SMALL=true
            RUN_LARGE=true
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [options]"
            echo ""
            echo "Options:"
            echo "  --small-only   Run only small configuration (10K cells)"
            echo "  --large-only   Run only large configuration (200K cells)"
            echo "  --both         Run both configurations"
            echo "  -h, --help     Show this help message"
            echo ""
            echo "Default: Run small configuration only"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Track overall success
OVERALL_SUCCESS=true

# Run small configuration (10K cells, 100 iterations, 8 threads)
if [ "$RUN_SMALL" = true ]; then
    if ! run_config "Small Configuration (10K cells)" 8 10000 100 "$RESULTS_DIR/small"; then
        OVERALL_SUCCESS=false
    fi
fi

# Run large configuration (200K cells, 500 iterations, 16 threads)
if [ "$RUN_LARGE" = true ]; then
    # Check for 200K data
    if [ ! -f "$DATA_DIR/benchmark_data_200k.h5ad" ] || [ ! -f "$DATA_DIR/benchmark_data_200k.rds" ]; then
        echo ""
        echo -e "${YELLOW}WARNING: 200K benchmark data not found${NC}"
        echo "Large configuration requires benchmark_data_200k.h5ad and benchmark_data_200k.rds"
        echo "Please run preprocess_200k.R and convert_mtx_to_h5ad.py first."
        echo "Skipping large configuration..."
    else
        if ! run_config "Large Configuration (200K cells)" 16 200000 500 "$RESULTS_DIR/large"; then
            OVERALL_SUCCESS=false
        fi
    fi
fi

# Generate final report
echo ""
echo "============================================================"
echo "Generating Final Report"
echo "============================================================"

python "$SCRIPT_DIR/generate_report.py" "$RESULTS_DIR" "$RESULTS_DIR/validation_report.md"

echo ""
echo "============================================================"
echo "BENCHMARK COMPLETE"
echo "============================================================"
echo ""
echo "Report: $RESULTS_DIR/validation_report.md"
echo ""

if [ "$OVERALL_SUCCESS" = true ]; then
    echo -e "${GREEN}Overall Status: ALL VALIDATIONS PASSED${NC}"
    exit 0
else
    echo -e "${RED}Overall Status: SOME VALIDATIONS FAILED${NC}"
    exit 1
fi
