/**
 * GEDI Dimensionality Reduction - Header file
 *
 * Functions for factorized SVD and PCA computation.
 * Ported from gedi2 R package (RcppEigen) to pybind11.
 */

#pragma once

#include <Eigen/Dense>
#include <vector>
#include <tuple>

namespace gedi {

using namespace Eigen;

/**
 * SVD Result structure
 *
 * Contains the three components of a singular value decomposition.
 */
struct SVDResult {
    VectorXd d;  // Singular values (K)
    MatrixXd u;  // Left singular vectors (J × K or rows × K)
    MatrixXd v;  // Right singular vectors (N × K or cols × K)
};

/**
 * Compute Factorized SVD
 *
 * Performs factorized SVD preserving GEDI structure: SVD(Z) × SVD(middle) × SVD(DB).
 * This is the standard, cached SVD computation.
 *
 * @param Z Shared metagene matrix (J × K)
 * @param D Scaling vector (length K)
 * @param Bi_list List of cell projection matrices (K × Ni each)
 * @param verbose Verbosity level
 *
 * @return SVDResult with d, u, v components
 */
SVDResult compute_svd_factorized_cpp(
    const MatrixXd& Z,
    const VectorXd& D,
    const std::vector<MatrixXd>& Bi_list,
    int verbose = 0
);

/**
 * Run Factorized SVD on Custom Projection
 *
 * General-purpose 3-stage factorized SVD for dynamics analysis.
 * Takes a pre-computed projDB matrix as input.
 *
 * @param Z Shared metagene matrix (J × K)
 * @param projDB Custom projected cell matrix (K × N_total)
 * @param verbose Verbosity level
 *
 * @return SVDResult with d, u, v components
 */
SVDResult run_factorized_svd_cpp(
    const MatrixXd& Z,
    const MatrixXd& projDB,
    int verbose = 0
);

/**
 * Compute PCA from Factorized SVD
 *
 * Derives PCA coordinates from SVD results.
 *
 * @param svd_result The SVD result from compute_svd_factorized_cpp
 * @param n_components Number of principal components to return
 * @param scale Whether to scale by singular values
 *
 * @return Matrix of PCA coordinates (N × n_components)
 */
MatrixXd compute_pca_cpp(
    const SVDResult& svd_result,
    int n_components,
    bool scale = true
);

} // namespace gedi
