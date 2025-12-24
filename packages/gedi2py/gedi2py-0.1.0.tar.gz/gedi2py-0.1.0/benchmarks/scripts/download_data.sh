#!/bin/bash
# download_data.sh - Download Allen Brain Atlas data for benchmarking
#
# This script downloads and preprocesses the data needed for benchmarking.
# Data source: Allen Brain Atlas 10X Chromium v3

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MANUSCRIPT_DIR="${SCRIPT_DIR}/../../gedi2_manuscript"
DATA_DIR="${MANUSCRIPT_DIR}/data"

echo "========================================"
echo "GEDI Benchmark Data Download"
echo "========================================"
echo "Data directory: ${DATA_DIR}"
echo ""

# Check if data already exists
if [ -f "${DATA_DIR}/WMB_ATLAS_10X_V3.rds" ]; then
    echo "Data file already exists: ${DATA_DIR}/WMB_ATLAS_10X_V3.rds"
    echo "Skipping download."
    exit 0
fi

# Create data directory if needed
mkdir -p "${DATA_DIR}"
cd "${DATA_DIR}"

# Check for download script in manuscript repo
if [ -f "1.download_via_wget.sh" ]; then
    echo "Running download script from manuscript repo..."
    bash 1.download_via_wget.sh
else
    echo "Download script not found. Downloading manually..."

    # Download URLs from manuscript repo
    if [ -f "download_urls.txt" ]; then
        echo "Downloading files from download_urls.txt..."
        mkdir -p Allen-brain-10X-V3
        cd Allen-brain-10X-V3

        while IFS= read -r url; do
            if [ -n "$url" ]; then
                echo "Downloading: $url"
                wget -q --show-progress "$url" || {
                    echo "Failed to download: $url"
                    exit 1
                }
            fi
        done < ../download_urls.txt

        cd ..
    else
        echo "ERROR: No download URLs found."
        echo "Please manually download the Allen Brain Atlas 10X V3 data."
        exit 1
    fi
fi

# Preprocess data
echo ""
echo "Preprocessing data..."

if [ -f "2.input_pre_proccess.R" ]; then
    # Activate conda environment
    source ~/miniconda/etc/profile.d/conda.sh
    conda activate gedi

    Rscript 2.input_pre_proccess.R || {
        echo "ERROR: Preprocessing failed."
        exit 1
    }
else
    echo "WARNING: Preprocessing script not found."
    echo "You may need to run preprocessing manually."
fi

# Verify output
if [ -f "WMB_ATLAS_10X_V3.rds" ]; then
    echo ""
    echo "========================================"
    echo "Data download and preprocessing complete!"
    echo "========================================"
    echo "File: ${DATA_DIR}/WMB_ATLAS_10X_V3.rds"
    ls -lh WMB_ATLAS_10X_V3.rds
else
    echo ""
    echo "ERROR: Output file not found after preprocessing."
    exit 1
fi
