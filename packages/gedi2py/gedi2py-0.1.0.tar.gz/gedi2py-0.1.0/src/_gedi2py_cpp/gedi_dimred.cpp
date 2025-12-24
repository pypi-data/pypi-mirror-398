/**
 * GEDI Dimensionality Reduction - Implementation
 *
 * Functions for factorized SVD and PCA computation.
 * Ported from gedi2 R package (RcppEigen) to pybind11.
 */

#include "gedi_dimred.hpp"
#include <iostream>

namespace gedi {

SVDResult compute_svd_factorized_cpp(
    const MatrixXd& Z,
    const VectorXd& D,
    const std::vector<MatrixXd>& Bi_list,
    int verbose
) {
    // ========================================================================
    // Dimension validation and setup
    // ========================================================================

    int K = static_cast<int>(Z.cols());
    int numSamples = static_cast<int>(Bi_list.size());

    if (D.size() != K) {
        throw std::runtime_error("Dimension mismatch: D must have length K");
    }

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

    // ========================================================================
    // Step 1: SVD of Z
    // ========================================================================

    JacobiSVD<MatrixXd> svd_Z(Z, ComputeThinU | ComputeThinV);
    MatrixXd U_Z = svd_Z.matrixU();        // J × K
    VectorXd S_Z = svd_Z.singularValues(); // K
    MatrixXd V_Z = svd_Z.matrixV();        // K × K

    // ========================================================================
    // Step 2: Concatenate B and compute DB
    // ========================================================================

    MatrixXd B(K, N);
    int col_offset = 0;

    for (int i = 0; i < numSamples; ++i) {
        const MatrixXd& Bi = Bi_list[i];
        int Ni_current = static_cast<int>(Bi.cols());
        B.block(0, col_offset, K, Ni_current) = Bi;
        col_offset += Ni_current;
    }

    // Apply diagonal scaling: DB = diag(D) * B
    MatrixXd DB = D.asDiagonal() * B;  // K × N

    // ========================================================================
    // Step 3: SVD of DB
    // ========================================================================

    JacobiSVD<MatrixXd> svd_DB(DB, ComputeThinU | ComputeThinV);
    MatrixXd U_DB = svd_DB.matrixU();        // K × K
    VectorXd S_DB = svd_DB.singularValues(); // K
    MatrixXd V_DB = svd_DB.matrixV();        // N × K

    // ========================================================================
    // Step 4: Form and decompose middle matrix
    // ========================================================================

    // Middle = diag(S_Z) * V_Z^T * U_DB * diag(S_DB)
    MatrixXd middle = S_Z.asDiagonal() * V_Z.transpose() * U_DB * S_DB.asDiagonal();

    // ========================================================================
    // Step 5: SVD of middle matrix
    // ========================================================================

    JacobiSVD<MatrixXd> svd_middle(middle, ComputeThinU | ComputeThinV);
    MatrixXd U_middle = svd_middle.matrixU();        // K × K
    VectorXd S_middle = svd_middle.singularValues(); // K
    MatrixXd V_middle = svd_middle.matrixV();        // K × K

    // ========================================================================
    // Reconstruct final SVD and return
    // ========================================================================

    SVDResult result;
    result.u = U_Z * U_middle;      // J × K
    result.v = V_DB * V_middle;     // N × K
    result.d = S_middle;            // K

    return result;
}

SVDResult run_factorized_svd_cpp(
    const MatrixXd& Z,
    const MatrixXd& projDB,
    int verbose
) {
    // ========================================================================
    // Dimension validation
    // ========================================================================

    int K = static_cast<int>(Z.cols());
    int K_proj = static_cast<int>(projDB.rows());

    if (K != K_proj) {
        throw std::runtime_error("Dimension mismatch: Z columns (" + std::to_string(K) +
                                 ") must equal projDB rows (" + std::to_string(K_proj) + ")");
    }

    // ========================================================================
    // Step 1: SVD of Z
    // ========================================================================

    JacobiSVD<MatrixXd> svd_Z(Z, ComputeThinU | ComputeThinV);
    MatrixXd U_Z = svd_Z.matrixU();        // J × K
    VectorXd S_Z = svd_Z.singularValues(); // K
    MatrixXd V_Z = svd_Z.matrixV();        // K × K

    // ========================================================================
    // Step 2: SVD of projDB (Input matrix)
    // ========================================================================

    JacobiSVD<MatrixXd> svd_projDB(projDB, ComputeThinU | ComputeThinV);
    MatrixXd U_DB = svd_projDB.matrixU();        // K × K
    VectorXd S_DB = svd_projDB.singularValues(); // K
    MatrixXd V_DB = svd_projDB.matrixV();        // N_total × K

    // ========================================================================
    // Step 3: Form and decompose middle matrix
    // ========================================================================

    // Middle = diag(S_Z) * V_Z^T * U_DB * diag(S_DB)
    MatrixXd middle = S_Z.asDiagonal() * V_Z.transpose() * U_DB * S_DB.asDiagonal();

    // ========================================================================
    // Step 4: SVD of middle matrix
    // ========================================================================

    JacobiSVD<MatrixXd> svd_middle(middle, ComputeThinU | ComputeThinV);
    MatrixXd U_middle = svd_middle.matrixU();        // K × K
    VectorXd S_middle = svd_middle.singularValues(); // K
    MatrixXd V_middle = svd_middle.matrixV();        // K × K

    // ========================================================================
    // Reconstruct final SVD and return
    // ========================================================================

    SVDResult result;
    result.u = U_Z * U_middle;      // J × K
    result.v = V_DB * V_middle;     // N_total × K
    result.d = S_middle;            // K

    return result;
}

MatrixXd compute_pca_cpp(
    const SVDResult& svd_result,
    int n_components,
    bool scale
) {
    int N = static_cast<int>(svd_result.v.rows());
    int K = static_cast<int>(svd_result.v.cols());

    // Clamp n_components to available dimensions
    n_components = std::min(n_components, K);

    MatrixXd pca(N, n_components);

    if (scale) {
        // PCA = V * diag(d) (first n_components)
        for (int i = 0; i < n_components; ++i) {
            pca.col(i) = svd_result.v.col(i) * svd_result.d(i);
        }
    } else {
        // PCA = V (first n_components)
        pca = svd_result.v.leftCols(n_components);
    }

    return pca;
}

} // namespace gedi
