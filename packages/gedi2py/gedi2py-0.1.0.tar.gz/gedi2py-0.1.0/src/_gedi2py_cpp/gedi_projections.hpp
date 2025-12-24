/**
 * GEDI Projections - Header file
 *
 * Stateless auxiliary functions for computing manifold projections.
 * Ported from gedi2 R package (RcppEigen) to pybind11.
 */

#pragma once

#include <Eigen/Dense>
#include <vector>
#include <stdexcept>

namespace gedi {

using namespace Eigen;

/**
 * Compute ZDB Projection
 *
 * Computes the shared manifold projection ZDB = Z * diag(D) * B, where B is
 * the concatenation of all sample-specific Bi matrices.
 *
 * @param Z Shared metagene matrix (J × K)
 * @param D Scaling vector (length K)
 * @param Bi_list List of sample-specific cell projection matrices (K × Ni each)
 * @param verbose Verbosity level (0 = silent)
 *
 * @return Dense matrix ZDB of dimensions J × N
 */
MatrixXd compute_ZDB_cpp(
    const MatrixXd& Z,
    const VectorXd& D,
    const std::vector<MatrixXd>& Bi_list,
    int verbose = 0
);

/**
 * Compute DB Projection
 *
 * Computes the latent factor embedding DB = diag(D) * B.
 *
 * @param D Scaling vector (length K)
 * @param Bi_list List of sample-specific cell projection matrices (K × Ni each)
 * @param verbose Verbosity level (0 = silent)
 *
 * @return Dense matrix DB of dimensions K × N
 */
MatrixXd compute_DB_cpp(
    const VectorXd& D,
    const std::vector<MatrixXd>& Bi_list,
    int verbose = 0
);

/**
 * Compute ADB Projection
 *
 * Computes the pathway activity projection ADB = C.rotation * A * diag(D) * B.
 *
 * @param C_rotation Rotation matrix (num_pathways × P)
 * @param A Pathway-factor connection matrix (P × K)
 * @param D Scaling vector (length K)
 * @param Bi_list List of sample-specific cell projection matrices (K × Ni each)
 * @param verbose Verbosity level (0 = silent)
 *
 * @return Dense matrix ADB of dimensions num_pathways × N
 */
MatrixXd compute_ADB_cpp(
    const MatrixXd& C_rotation,
    const MatrixXd& A,
    const VectorXd& D,
    const std::vector<MatrixXd>& Bi_list,
    int verbose = 0
);

} // namespace gedi
