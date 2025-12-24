/**
 * GEDI Differential Expression - Implementation
 *
 * Functions for computing differential expression effects.
 * Ported from gedi2 R package (RcppEigen) to pybind11.
 */

#include "gedi_differential.hpp"
#include <iostream>
#include <cmath>

namespace gedi {

VectorXd getDiffO_cpp(
    const MatrixXd& Ro,
    const MatrixXd& H_rotation,
    const VectorXd& contrast,
    int verbose
) {
    // Dimension validation
    int J = static_cast<int>(Ro.rows());
    int L = static_cast<int>(Ro.cols());

    if (H_rotation.rows() != L) {
        throw std::runtime_error("Dimension mismatch: H_rotation must have L rows");
    }

    if (contrast.size() != L) {
        throw std::runtime_error("Dimension mismatch: contrast must have length L");
    }

    if (L == 0) {
        throw std::runtime_error("Cannot compute diffO: no sample-level prior (H) was provided");
    }

    if (verbose >= 1) {
        std::cout << "Computing diffO: " << J << " genes" << std::endl;
    }

    // Compute: diffO = Ro * H.rotation * contrast
    VectorXd H_contrast = H_rotation * contrast;
    VectorXd diffO = Ro * H_contrast;

    if (verbose >= 1) {
        double mean_val = diffO.mean();
        double std_val = std::sqrt((diffO.array() - mean_val).square().mean());
        std::cout << "diffO computed: mean = " << mean_val
                  << ", std = " << std_val << std::endl;
    }

    return diffO;
}

MatrixXd getDiffQ_cpp(
    const std::vector<MatrixXd>& Rk_list,
    const MatrixXd& H_rotation,
    const VectorXd& contrast,
    int verbose
) {
    // Dimension validation
    int K = static_cast<int>(Rk_list.size());
    int L = static_cast<int>(H_rotation.rows());

    if (K == 0 || L == 0) {
        throw std::runtime_error("Cannot compute diffQ: no sample-level prior (H) was provided (K=0 or L=0)");
    }

    // Validate Rk dimensions and get J
    const MatrixXd& Rk_first = Rk_list[0];
    int J = static_cast<int>(Rk_first.rows());
    if (Rk_first.cols() != L) {
        throw std::runtime_error("Dimension mismatch: Rk[0] must have L columns");
    }

    if (contrast.size() != L) {
        throw std::runtime_error("Dimension mismatch: contrast must have length L");
    }

    if (verbose >= 1) {
        std::cout << "Computing diffQ (Z-space): " << J << " genes × " << K << " factors" << std::endl;
    }

    // Pre-compute H.rotation * contrast
    VectorXd H_contrast = H_rotation * contrast; // L × 1

    // Allocate result matrix
    MatrixXd diffQ_Z_space(J, K);

    // Compute effect for k=0 (already fetched)
    diffQ_Z_space.col(0) = Rk_first * H_contrast;

    // Loop for k = 1 to K-1
    for (int k = 1; k < K; ++k) {
        const MatrixXd& Rk = Rk_list[k]; // J × L

        // Validate dimensions for subsequent Rk
        if (Rk.rows() != J || Rk.cols() != L) {
            throw std::runtime_error("Dimension mismatch: all Rk matrices must have the same JxL dimensions");
        }

        // Compute effect for this factor: Rk * H_contrast (J × 1)
        diffQ_Z_space.col(k) = Rk * H_contrast;
    }

    if (verbose >= 1) {
        std::cout << "✓ diffQ (Z-space) computed" << std::endl;
    }

    return diffQ_Z_space;
}

MatrixXd getDiffExp_cpp(
    const std::vector<MatrixXd>& Rk_list,
    const MatrixXd& H_rotation,
    const VectorXd& contrast,
    const VectorXd& D,
    const std::vector<MatrixXd>& Bi_list,
    int verbose
) {
    // Dimension validation
    int K = static_cast<int>(Rk_list.size());
    int L = static_cast<int>(H_rotation.rows());
    int numSamples = static_cast<int>(Bi_list.size());

    if (contrast.size() != L) {
        throw std::runtime_error("Dimension mismatch: contrast must have length L");
    }

    if (D.size() != K) {
        throw std::runtime_error("Dimension mismatch: D must have length K");
    }

    if (K == 0 || L == 0) {
        throw std::runtime_error("Cannot compute diffExp: no sample-level prior (H) was provided");
    }

    // Validate Rk dimensions and get J
    const MatrixXd& Rk_first = Rk_list[0];
    int J = static_cast<int>(Rk_first.rows());
    if (Rk_first.cols() != L) {
        throw std::runtime_error("Dimension mismatch: Rk[0] must have L columns");
    }

    // Count total cells and validate Bi
    int N = 0;
    for (int i = 0; i < numSamples; ++i) {
        const MatrixXd& Bi = Bi_list[i];
        if (Bi.rows() != K) {
            throw std::runtime_error("Dimension mismatch: Bi[" + std::to_string(i) +
                                     "] must have K rows");
        }
        N += static_cast<int>(Bi.cols());
    }

    if (verbose >= 1) {
        std::cout << "Computing diffExp (Cell-space): " << J << " genes × " << N << " cells" << std::endl;
        if (verbose >= 2) {
            std::cout << "  Contrast dimension: " << L << ", Factors: " << K << std::endl;
        }
    }

    // === Concatenate B and compute DB ===
    if (verbose >= 2) std::cout << "  Concatenating B and computing DB..." << std::endl;
    MatrixXd B(K, N);
    int col_offset = 0;

    for (int i = 0; i < numSamples; ++i) {
        const MatrixXd& Bi = Bi_list[i];
        int Ni_current = static_cast<int>(Bi.cols());
        B.block(0, col_offset, K, Ni_current) = Bi;
        col_offset += Ni_current;
    }

    MatrixXd DB = D.asDiagonal() * B; // K × N

    // === Compute: diffExp = sum_k (Rk * H.rotation * contrast) * DB[k, :] ===
    if (verbose >= 2) std::cout << "  Computing sum of outer products..." << std::endl;

    // Pre-compute H.rotation * contrast (L × 1 vector)
    VectorXd H_contrast = H_rotation * contrast;

    MatrixXd diffExp = MatrixXd::Zero(J, N);

    // Add effect for k=0 (already fetched)
    VectorXd effect_0 = Rk_first * H_contrast;
    diffExp += effect_0 * DB.row(0);

    // Loop for k = 1 to K-1
    for (int k = 1; k < K; ++k) {
        if (verbose >= 2 && K <= 20) {
            std::cout << "    Factor " << (k + 1) << "/" << K << std::endl;
        }

        const MatrixXd& Rk = Rk_list[k]; // J × L

        // Compute effect for this factor: Rk * H_contrast (J × 1)
        VectorXd effect_k = Rk * H_contrast;

        // Add outer product: effect_k (J×1) with DB.row(k) (1×N)
        diffExp += effect_k * DB.row(k);
    }

    if (verbose >= 1) {
        double mean_val = diffExp.mean();
        double std_val = std::sqrt((diffExp.array() - mean_val).square().mean());
        std::cout << "✓ diffExp computed: mean = " << mean_val
                  << ", std = " << std_val << std::endl;
    }

    return diffExp;
}

} // namespace gedi
