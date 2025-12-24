/**
 * GEDI Projections - Implementation
 *
 * Stateless auxiliary functions for computing manifold projections.
 * Ported from gedi2 R package (RcppEigen) to pybind11.
 */

#include "gedi_projections.hpp"
#include <iostream>

namespace gedi {

MatrixXd compute_ZDB_cpp(
    const MatrixXd& Z,
    const VectorXd& D,
    const std::vector<MatrixXd>& Bi_list,
    int verbose
) {
    // Dimension validation and setup
    int J = Z.rows();
    int K = Z.cols();
    int numSamples = static_cast<int>(Bi_list.size());

    if (D.size() != K) {
        throw std::runtime_error("Dimension mismatch: D must have length K");
    }

    if (numSamples == 0) {
        throw std::runtime_error("Bi_list cannot be empty");
    }

    // Count total cells across all samples
    int N = 0;
    std::vector<int> Ni(numSamples);

    for (int i = 0; i < numSamples; ++i) {
        const MatrixXd& Bi = Bi_list[i];

        if (Bi.rows() != K) {
            throw std::runtime_error("Dimension mismatch: Bi[" + std::to_string(i) +
                                     "] must have K rows");
        }

        Ni[i] = static_cast<int>(Bi.cols());
        N += Ni[i];
    }

    // Pre-compute ZD = Z * diag(D) for efficiency
    MatrixXd ZD = Z * D.asDiagonal();

    // Allocate output matrix
    MatrixXd ZDB(J, N);

    // Compute ZD * Bi for each sample and concatenate
    int col_offset = 0;

    for (int i = 0; i < numSamples; ++i) {
        const MatrixXd& Bi = Bi_list[i];
        int Ni_current = static_cast<int>(Bi.cols());

        // Compute ZD * Bi and store in appropriate block
        ZDB.block(0, col_offset, J, Ni_current) = ZD * Bi;

        col_offset += Ni_current;
    }

    return ZDB;
}

MatrixXd compute_DB_cpp(
    const VectorXd& D,
    const std::vector<MatrixXd>& Bi_list,
    int verbose
) {
    // Dimension validation and setup
    int K = static_cast<int>(D.size());
    int numSamples = static_cast<int>(Bi_list.size());

    if (numSamples == 0) {
        throw std::runtime_error("Bi_list cannot be empty");
    }

    // Count total cells
    int N = 0;
    std::vector<int> Ni(numSamples);

    for (int i = 0; i < numSamples; ++i) {
        const MatrixXd& Bi = Bi_list[i];

        if (Bi.rows() != K) {
            throw std::runtime_error("Dimension mismatch: Bi[" + std::to_string(i) +
                                     "] must have K rows");
        }

        Ni[i] = static_cast<int>(Bi.cols());
        N += Ni[i];
    }

    // Concatenate all Bi matrices
    MatrixXd B(K, N);
    int col_offset = 0;

    for (int i = 0; i < numSamples; ++i) {
        const MatrixXd& Bi = Bi_list[i];
        int Ni_current = static_cast<int>(Bi.cols());

        B.block(0, col_offset, K, Ni_current) = Bi;

        col_offset += Ni_current;
    }

    // Apply diagonal scaling: DB = diag(D) * B
    MatrixXd DB = D.asDiagonal() * B;

    return DB;
}

MatrixXd compute_ADB_cpp(
    const MatrixXd& C_rotation,
    const MatrixXd& A,
    const VectorXd& D,
    const std::vector<MatrixXd>& Bi_list,
    int verbose
) {
    // Dimension extraction - C_rotation is num_pathways x P, A is P x K
    int P = static_cast<int>(C_rotation.cols());
    int K = static_cast<int>(A.cols());
    int numSamples = static_cast<int>(Bi_list.size());

    // Dimension validation
    if (A.rows() != P) {
        throw std::runtime_error("Dimension mismatch: A must have P rows (got " +
                                 std::to_string(A.rows()) + ", expected " +
                                 std::to_string(P) + ")");
    }

    if (D.size() != K) {
        throw std::runtime_error("Dimension mismatch: D must have length K (got " +
                                 std::to_string(D.size()) + ", expected " +
                                 std::to_string(K) + ")");
    }

    if (numSamples == 0) {
        throw std::runtime_error("Bi_list cannot be empty");
    }

    if (P == 0) {
        throw std::runtime_error("Cannot compute ADB: no gene-level prior (C) was provided");
    }

    // Count total cells and validate Bi dimensions
    int N = 0;
    std::vector<int> Ni(numSamples);

    for (int i = 0; i < numSamples; ++i) {
        const MatrixXd& Bi = Bi_list[i];

        if (Bi.rows() != K) {
            throw std::runtime_error("Dimension mismatch: Bi[" + std::to_string(i) +
                                     "] must have K rows (got " + std::to_string(Bi.rows()) +
                                     ", expected " + std::to_string(K) + ")");
        }

        Ni[i] = static_cast<int>(Bi.cols());
        N += Ni[i];
    }

    // Concatenate all Bi matrices into B
    MatrixXd B(K, N);
    int col_offset = 0;

    for (int i = 0; i < numSamples; ++i) {
        const MatrixXd& Bi = Bi_list[i];
        int Ni_current = static_cast<int>(Bi.cols());

        B.block(0, col_offset, K, Ni_current) = Bi;

        col_offset += Ni_current;
    }

    // Compute ADB = C.rotation * A * diag(D) * B
    // Efficient computation order: (C.rotation * A) * (diag(D) * B)
    MatrixXd CA = C_rotation * A;     // num_pathways x K
    MatrixXd DB = D.asDiagonal() * B; // K x N
    MatrixXd ADB = CA * DB;           // num_pathways x N

    return ADB;
}

} // namespace gedi
