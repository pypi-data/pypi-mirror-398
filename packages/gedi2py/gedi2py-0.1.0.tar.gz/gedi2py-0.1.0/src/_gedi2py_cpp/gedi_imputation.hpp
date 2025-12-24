/**
 * GEDI Imputation - Header file
 *
 * Functions for imputation and variance computation.
 * Ported from gedi2 R package (RcppEigen) to pybind11.
 */

#pragma once

#include <Eigen/Dense>
#include <Eigen/Sparse>
#include <vector>
#include <tuple>

namespace gedi {

using namespace Eigen;

/**
 * Compute Residual After Removing Sample Effects
 *
 * Removes sample-specific effects (QiDBi, si, oi) and global offset (o) from Yi.
 * Used to extract the shared biological signal (ZDBi component).
 *
 * Computes: Yi - QiDBi - (si ⊗ 1ᵀ) - (o + oi) ⊗ 1ᵀ
 *
 * @param Yi Dense matrix (J × Ni) - fitted log-expression for sample i
 * @param QiDBi Dense matrix (J × Ni) - sample-specific metagene projections
 * @param si Vector (Ni) - cell-specific library size offsets
 * @param o Vector (J) - global gene-specific offsets
 * @param oi Vector (J) - sample-specific gene offsets
 *
 * @return Dense matrix (J × Ni) - residual Yi
 */
MatrixXd Yi_resZ_cpp(
    const MatrixXd& Yi,
    const MatrixXd& QiDBi,
    const VectorXd& si,
    const VectorXd& o,
    const VectorXd& oi
);

/**
 * Predict Yi from Model Parameters
 *
 * Reconstructs the model's prediction of Yi from all components.
 * Computes: Ŷi = ZDBi + QiDBi + (si ⊗ 1ᵀ) + (o + oi) ⊗ 1ᵀ
 *
 * @param ZDBi Dense matrix (J × Ni) - shared metagene projections
 * @param QiDBi Dense matrix (J × Ni) - sample-specific metagene projections
 * @param si Vector (Ni) - cell-specific library size offsets
 * @param o Vector (J) - global gene-specific offsets
 * @param oi Vector (J) - sample-specific gene offsets
 *
 * @return Dense matrix (J × Ni) - predicted Yi
 */
MatrixXd predict_Yhat_cpp(
    const MatrixXd& ZDBi,
    const MatrixXd& QiDBi,
    const VectorXd& si,
    const VectorXd& o,
    const VectorXd& oi
);

/**
 * Compute imputed expression for all samples
 *
 * @param Yi List of expression matrices per sample
 * @param ZDBi List of shared projections per sample
 * @param QiDBi List of sample-specific projections
 * @param o Global gene offsets
 * @param oi List of sample-specific gene offsets
 * @param si List of cell size factors per sample
 *
 * @return List of imputed matrices per sample
 */
std::vector<MatrixXd> compute_Yi_imputed_cpp(
    const std::vector<MatrixXd>& Yi,
    const std::vector<MatrixXd>& ZDBi,
    const std::vector<MatrixXd>& QiDBi,
    const VectorXd& o,
    const std::vector<VectorXd>& oi,
    const std::vector<VectorXd>& si
);

/**
 * Variance of Yi for Single Count Matrix
 *
 * Computes posterior variance: Var(Yi | Mi, model) = 1 / (exp(Yi) + 1/sigma2)
 *
 * @param Yi Dense matrix (J × Ni) - fitted log-expression
 * @param sigma2 Scalar - model variance parameter
 *
 * @return Dense matrix (J × Ni) - posterior variance
 */
MatrixXd Yi_var_M_cpp(
    const MatrixXd& Yi,
    double sigma2
);

/**
 * Variance of Yi for Paired Count Matrices
 *
 * For observation type "M_paired" (e.g., CITE-seq).
 *
 * @param Yi Dense matrix (J × Ni) - fitted log-ratio
 * @param M1i Sparse matrix (J × Ni) - first count matrix
 * @param M2i Sparse matrix (J × Ni) - second count matrix
 * @param sigma2 Scalar - model variance parameter
 *
 * @return Dense matrix (J × Ni) - posterior variance
 */
MatrixXd Yi_var_M_paired_cpp(
    const MatrixXd& Yi,
    const SparseMatrix<double>& M1i,
    const SparseMatrix<double>& M2i,
    double sigma2
);

/**
 * Compute Dispersion Statistics
 *
 * Analyzes the relationship between predicted and observed variance.
 * Only samples nonzero positions from sparse count matrix.
 *
 * @param Yi_fitted Dense matrix (J × Ni) - model prediction
 * @param Mi Sparse matrix (J × Ni) - observed counts
 * @param subsample Maximum number of nonzero positions to sample
 *
 * @return Tuple of (predicted counts, observed counts, n_total, n_sampled)
 */
std::tuple<VectorXd, VectorXd, int, int> compute_dispersion_sparse_cpp(
    const MatrixXd& Yi_fitted,
    const SparseMatrix<double>& Mi,
    int subsample
);

/**
 * Sum of Squared Errors for Paired Data
 *
 * Computes the SSE term for sigma2 optimization with M_paired observation type.
 *
 * @return Scalar SSE contribution
 */
double Yi_SSE_M_paired_cpp(
    const MatrixXd& Yi,
    const SparseMatrix<double>& M1i,
    const SparseMatrix<double>& M2i,
    const MatrixXd& ZDBi,
    const MatrixXd& QiDBi,
    const VectorXd& si,
    const VectorXd& o,
    const VectorXd& oi,
    double sigma2
);

} // namespace gedi
