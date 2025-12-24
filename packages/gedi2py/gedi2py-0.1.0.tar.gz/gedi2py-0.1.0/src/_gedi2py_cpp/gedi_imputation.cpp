/**
 * GEDI Imputation - Implementation
 *
 * Functions for imputation and variance computation.
 * Ported from gedi2 R package (RcppEigen) to pybind11.
 */

#include "gedi_imputation.hpp"
#include <random>
#include <algorithm>
#include <numeric>
#include <cmath>

namespace gedi {

MatrixXd Yi_resZ_cpp(
    const MatrixXd& Yi,
    const MatrixXd& QiDBi,
    const VectorXd& si,
    const VectorXd& o,
    const VectorXd& oi
) {
    // Yi - QiDBi
    MatrixXd result = Yi - QiDBi;

    // Subtract si from each row: rowwise() - si.transpose()
    result.rowwise() -= si.transpose();

    // Subtract (o + oi) from each column: colwise() - (o + oi)
    VectorXd gene_offset = o + oi;
    result.colwise() -= gene_offset;

    return result;
}

MatrixXd predict_Yhat_cpp(
    const MatrixXd& ZDBi,
    const MatrixXd& QiDBi,
    const VectorXd& si,
    const VectorXd& o,
    const VectorXd& oi
) {
    // ZDBi + QiDBi
    MatrixXd result = ZDBi + QiDBi;

    // Add si to each row: rowwise() + si.transpose()
    result.rowwise() += si.transpose();

    // Add (o + oi) to each column: colwise() + (o + oi)
    VectorXd gene_offset = o + oi;
    result.colwise() += gene_offset;

    return result;
}

std::vector<MatrixXd> compute_Yi_imputed_cpp(
    const std::vector<MatrixXd>& Yi,
    const std::vector<MatrixXd>& ZDBi,
    const std::vector<MatrixXd>& QiDBi,
    const VectorXd& o,
    const std::vector<VectorXd>& oi,
    const std::vector<VectorXd>& si
) {
    int numSamples = static_cast<int>(Yi.size());
    std::vector<MatrixXd> Yi_imputed(numSamples);

    for (int i = 0; i < numSamples; ++i) {
        Yi_imputed[i] = predict_Yhat_cpp(ZDBi[i], QiDBi[i], si[i], o, oi[i]);
    }

    return Yi_imputed;
}

MatrixXd Yi_var_M_cpp(
    const MatrixXd& Yi,
    double sigma2
) {
    // Convert to array for element-wise operations
    ArrayXXd Yi_array = Yi.array();

    // Variance = 1 / (exp(Yi) + 1/sigma2)
    ArrayXXd variance = 1.0 / (Yi_array.exp() + 1.0 / sigma2);

    return variance.matrix();
}

MatrixXd Yi_var_M_paired_cpp(
    const MatrixXd& Yi,
    const SparseMatrix<double>& M1i,
    const SparseMatrix<double>& M2i,
    double sigma2
) {
    // Compute exp(-|Yi|) efficiently
    ArrayXXd expYi = (-Yi.array().abs()).exp();

    // Sparse addition (stays sparse until converted)
    SparseMatrix<double> M_sum_sparse = M1i + M2i;

    // Convert sparse to dense, then to array
    MatrixXd M_sum_dense = MatrixXd(M_sum_sparse);
    ArrayXXd M_sum = M_sum_dense.array();

    // Compute (1 + exp(-|Yi|))^2
    ArrayXXd one_plus_expYi = 1.0 + expYi;
    ArrayXXd one_plus_expYi_sq = one_plus_expYi.square();

    // Variance denominator: M * exp(-|Yi|) / (1 + exp(-|Yi|))^2 + 1/sigma2
    ArrayXXd denominator = M_sum * expYi / one_plus_expYi_sq + (1.0 / sigma2);

    // Variance = 1 / denominator
    ArrayXXd variance = 1.0 / denominator;

    return variance.matrix();
}

std::tuple<VectorXd, VectorXd, int, int> compute_dispersion_sparse_cpp(
    const MatrixXd& Yi_fitted,
    const SparseMatrix<double>& Mi,
    int subsample
) {
    // Extract all nonzero positions from sparse Mi
    std::vector<int> nz_rows, nz_cols;
    std::vector<double> observed_vals;

    // Reserve space for efficiency
    nz_rows.reserve(Mi.nonZeros());
    nz_cols.reserve(Mi.nonZeros());
    observed_vals.reserve(Mi.nonZeros());

    // Iterate through nonzero elements (sparse iteration - very fast)
    for (int k = 0; k < Mi.outerSize(); ++k) {
        for (SparseMatrix<double>::InnerIterator it(Mi, k); it; ++it) {
            nz_rows.push_back(static_cast<int>(it.row()));
            nz_cols.push_back(static_cast<int>(it.col()));
            observed_vals.push_back(it.value());
        }
    }

    // Subsample if we have more nonzeros than requested
    int n_total = static_cast<int>(nz_rows.size());
    int n_sample = std::min(subsample, n_total);

    // Create random sample indices
    std::vector<int> sample_idx(n_total);
    std::iota(sample_idx.begin(), sample_idx.end(), 0);

    // Shuffle and take first n_sample elements
    std::random_device rd;
    std::mt19937 gen(rd());
    std::shuffle(sample_idx.begin(), sample_idx.end(), gen);
    sample_idx.resize(n_sample);

    // Extract predicted and observed values at sampled positions
    VectorXd predicted(n_sample);
    VectorXd observed(n_sample);

    for (int i = 0; i < n_sample; ++i) {
        int idx = sample_idx[i];
        int row = nz_rows[idx];
        int col = nz_cols[idx];

        // Predicted count: lambda = exp(Yi_fitted)
        predicted(i) = std::exp(Yi_fitted(row, col));

        // Observed count from Mi
        observed(i) = observed_vals[idx];
    }

    return std::make_tuple(predicted, observed, n_total, n_sample);
}

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
) {
    // Compute residual: Yi - Ŷi
    MatrixXd residual = Yi - ZDBi - QiDBi;
    residual.rowwise() -= si.transpose();
    residual.colwise() -= (o + oi);

    // SSE from residual
    double sse = residual.squaredNorm();

    // Add contribution from binomial variance term
    ArrayXXd expYi = (-Yi.array().abs()).exp();
    SparseMatrix<double> M_sum = M1i + M2i;
    MatrixXd M_dense = MatrixXd(M_sum);
    ArrayXXd M = M_dense.array();
    ArrayXXd one_plus_expYi = 1.0 + expYi;

    // Sum of 1 / (M * exp(-|Yi|) / (1+exp(-|Yi|))^2 + 1/sigma2)
    ArrayXXd variance_term = M * expYi / one_plus_expYi.square() + (1.0 / sigma2);
    sse += (1.0 / variance_term).sum();

    return sse;
}

} // namespace gedi
