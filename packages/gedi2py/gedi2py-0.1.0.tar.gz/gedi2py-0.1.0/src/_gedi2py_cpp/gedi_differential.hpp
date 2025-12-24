/**
 * GEDI Differential Expression - Header file
 *
 * Functions for computing differential expression effects.
 * Ported from gedi2 R package (RcppEigen) to pybind11.
 */

#pragma once

#include <Eigen/Dense>
#include <vector>

namespace gedi {

using namespace Eigen;

/**
 * Compute Differential O (Gene Offset) Effect
 *
 * Computes the differential effect of sample-level variables on gene-specific
 * offsets: diffO = Ro * H.rotation * contrast.
 *
 * @param Ro Matrix (J × L) - effect of sample variables on gene offsets
 * @param H_rotation Rotation matrix (L × num_covariates)
 * @param contrast Vector (length L) - the contrast to compute
 * @param verbose Verbosity level (0 = silent)
 *
 * @return Vector (length J) - differential offset effect per gene
 */
VectorXd getDiffO_cpp(
    const MatrixXd& Ro,
    const MatrixXd& H_rotation,
    const VectorXd& contrast,
    int verbose = 0
);

/**
 * Compute Differential Q in Z-space
 *
 * Computes sample-variable effects on Qi, returning a J × K matrix.
 *
 * @param Rk_list List of K matrices (each J × L)
 * @param H_rotation Rotation matrix (L × num_covariates)
 * @param contrast Vector (length L) - the contrast
 * @param verbose Verbosity level
 *
 * @return Dense matrix diffQ (J × K) - differential effect in Z-space
 */
MatrixXd getDiffQ_cpp(
    const std::vector<MatrixXd>& Rk_list,
    const MatrixXd& H_rotation,
    const VectorXd& contrast,
    int verbose = 0
);

/**
 * Compute Differential Expression
 *
 * Computes the cell-specific differential expression effect (J × N).
 *
 * @param Rk_list List of K matrices (each J × L)
 * @param H_rotation Rotation matrix (L × num_covariates)
 * @param contrast Vector (length L) - the contrast
 * @param D Scaling vector (length K)
 * @param Bi_list List of cell projection matrices (K × Ni each)
 * @param verbose Verbosity level
 *
 * @return Dense matrix diffExp (J × N) - differential expression per gene per cell
 */
MatrixXd getDiffExp_cpp(
    const std::vector<MatrixXd>& Rk_list,
    const MatrixXd& H_rotation,
    const VectorXd& contrast,
    const VectorXd& D,
    const std::vector<MatrixXd>& Bi_list,
    int verbose = 0
);

} // namespace gedi
