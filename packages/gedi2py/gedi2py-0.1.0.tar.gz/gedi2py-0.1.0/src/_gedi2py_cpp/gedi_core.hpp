/**
 * GEDI Core - Header file
 *
 * Gene Expression Data Integration for single-cell RNA-seq
 * C++ implementation with pybind11 bindings
 *
 * Ported from gedi2 R package (RcppEigen) to pybind11
 */

#pragma once

#include <Eigen/Dense>
#include <Eigen/Sparse>
#include <vector>
#include <string>
#include <chrono>
#include <cmath>
#include <stdexcept>
#include <iostream>

#ifdef GEDI_USE_OPENMP
#include <omp.h>
#endif

namespace gedi {

using namespace Eigen;

// ============================================================================
// Helper Functions
// ============================================================================

/**
 * Compute log1p for sparse matrix -> dense result
 */
MatrixXd sparse_log1p(const SparseMatrix<double>& M);

/**
 * Compute log ratio for paired sparse matrices -> dense result
 */
MatrixXd sparse_log_ratio(const SparseMatrix<double>& M1,
                          const SparseMatrix<double>& M2);

// ============================================================================
// Timer Class for Performance Profiling
// ============================================================================

class FunctionTimer {
public:
    FunctionTimer(const std::string& name, int verbose_level);
    ~FunctionTimer();

private:
    std::string function_name;
    int verbose;
    std::chrono::time_point<std::chrono::high_resolution_clock> start_time;
};

// ============================================================================
// GEDI Class
// ============================================================================

class GEDI {
public:
    /**
     * Construct GEDI model with explicit parameters.
     *
     * @param J Number of genes
     * @param N Total number of cells
     * @param K Number of latent factors
     * @param P Number of pathway components (0 if no C matrix)
     * @param L Number of covariate components (0 if no H matrix)
     * @param numSamples Number of samples/batches
     * @param Bi Initial cell loadings per sample
     * @param Qi Initial sample-specific metagenes
     * @param si Initial cell size factors
     * @param oi Initial sample gene offsets
     * @param o Initial global gene offsets
     * @param Z Initial shared metagenes
     * @param U Initial SVD left vectors
     * @param S Initial SVD singular values
     * @param D Initial scaling factors
     * @param sigma2 Initial noise variance
     * @param Yi Expression data per sample (genes x cells)
     * @param obs_type Observation type: "M", "M_paired", "Y", or "X"
     * @param mode Normalization mode: "Bl2" or "Bsphere"
     * @param orthoZ Whether to orthogonalize Z
     * @param adjustD Whether to adjust D
     * @param is_si_fixed Whether si is fixed
     * @param verbose Verbosity level (0-4)
     * @param num_threads Number of OpenMP threads (0 = auto)
     */
    GEDI(
        int J, int N, int K, int P, int L, int numSamples,
        const std::vector<MatrixXd>& Bi,
        const std::vector<MatrixXd>& Qi,
        const std::vector<VectorXd>& si,
        const std::vector<VectorXd>& oi,
        const VectorXd& o,
        const MatrixXd& Z,
        const MatrixXd& U,
        const VectorXd& S,
        const VectorXd& D,
        double sigma2,
        const std::vector<MatrixXd>& Yi,
        const std::string& obs_type = "M",
        const std::string& mode = "Bsphere",
        bool orthoZ = true,
        bool adjustD = true,
        bool is_si_fixed = false,
        int verbose = 1,
        int num_threads = 0
    );

    // ========================================================================
    // Core Methods
    // ========================================================================

    /**
     * Initialize latent variables via randomized SVD.
     * @param multimodal Whether this is part of multimodal initialization
     */
    void initialize(bool multimodal = false);

    /**
     * Run block coordinate descent optimization.
     * @param iterations Number of iterations
     * @param track_interval Interval for tracking metrics
     */
    void optimize(int iterations, int track_interval = 5);

    /**
     * Combined initialize + optimize.
     * @param iterations Number of iterations
     * @param track_interval Interval for tracking metrics
     * @param multimodal Whether multimodal mode
     */
    void train(int iterations, int track_interval = 5, bool multimodal = false);

    // ========================================================================
    // Parameter Getters
    // ========================================================================

    MatrixXd get_Z() const { return params_Z; }
    VectorXd get_D() const { return params_D; }
    MatrixXd get_U() const { return params_U; }
    VectorXd get_S() const { return params_S; }
    VectorXd get_o() const { return params_o; }
    double get_sigma2() const { return params_sigma2; }

    std::vector<MatrixXd> get_Bi() const { return params_Bi; }
    std::vector<MatrixXd> get_Qi() const { return params_Qi; }
    std::vector<VectorXd> get_si() const { return params_si; }
    std::vector<VectorXd> get_oi() const { return params_oi; }

    // Optional parameters (for pathway/covariate models)
    MatrixXd get_A() const { return params_A; }
    std::vector<MatrixXd> get_Rk() const { return params_Rk; }
    MatrixXd get_Ro() const { return params_Ro; }

    // Auxiliary data
    std::vector<MatrixXd> get_ZDBi() const { return aux_ZDBi; }
    std::vector<MatrixXd> get_QiDBi() const { return aux_QiDBi; }

    // ========================================================================
    // Tracking Getters
    // ========================================================================

    std::vector<double> get_tracking_sigma2() const { return tracking_sigma2; }
    std::vector<double> get_tracking_dZ() const { return tracking_dZ; }
    std::vector<double> get_tracking_dA() const { return tracking_dA; }
    std::vector<double> get_tracking_do() const { return tracking_do; }

    // ========================================================================
    // State Queries
    // ========================================================================

    bool is_initialized() const { return is_initialized_; }
    void set_initialized(bool value) { is_initialized_ = value; }
    int get_total_iterations() const { return total_iterations; }

    // Compute ZDBi and QiDBi caches from current parameters
    // Call this after loading pre-initialized parameters but before optimize()
    void compute_initial_caches();

    // ========================================================================
    // Setters for Optional Parameters
    // ========================================================================

    void set_C(const MatrixXd& C);
    void set_H(const MatrixXd& H);
    void set_hyperparams(
        const VectorXd& S_Qi,
        const VectorXd& S_oi,
        double S_Z,
        double S_A,
        double S_R,
        double S_si,
        double S_o,
        const VectorXd& o_0,
        const std::vector<VectorXd>& si_0,
        const MatrixXd& O
    );

    // For sparse input data
    void set_Mi(const std::vector<SparseMatrix<double>>& Mi);
    void set_M1i_M2i(const std::vector<SparseMatrix<double>>& M1i,
                    const std::vector<SparseMatrix<double>>& M2i);
    void set_Xi(const std::vector<MatrixXd>& Xi);

private:
    // ========================================================================
    // Dimensions
    // ========================================================================
    int J_;          // Number of genes
    int N_;          // Total cells
    int K_;          // Latent factors
    int P_;          // Pathway components
    int L_;          // Covariate components
    int numSamples_; // Number of samples
    int num_threads_;

    // ========================================================================
    // Model Parameters
    // ========================================================================
    std::vector<MatrixXd> params_Bi;   // Cell loadings (K x Ni) per sample
    std::vector<MatrixXd> params_Qi;   // Sample metagenes (J x K)
    std::vector<VectorXd> params_si;   // Cell size factors (Ni)
    std::vector<VectorXd> params_oi;   // Sample gene offsets (J)
    VectorXd params_o;                 // Global gene offsets (J)
    MatrixXd params_Z;                 // Shared metagenes (J x K)
    MatrixXd params_U;                 // SVD left vectors (J x K)
    VectorXd params_S;                 // SVD singular values (K)
    VectorXd params_D;                 // Scaling factors (K)
    MatrixXd params_A;                 // Pathway coefficients (P x K)
    std::vector<MatrixXd> params_Rk;   // Covariate effects (J x L) per factor
    MatrixXd params_Ro;                // Covariate offset effects (J x L)
    double params_sigma2;              // Noise variance

    // ========================================================================
    // Auxiliary Data
    // ========================================================================
    std::vector<MatrixXd> aux_ZDBi;    // Cached Z*D*Bi
    std::vector<MatrixXd> aux_QiDBi;   // Cached Qi*D*Bi
    std::vector<MatrixXd> aux_Qi_hat;  // For covariate model
    std::vector<VectorXd> aux_oi_hat;  // For covariate model
    MatrixXd aux_C;                    // Pathway prior matrix
    MatrixXd aux_H;                    // Covariate matrix
    MatrixXd aux_diag_K;               // K x K identity
    VectorXd aux_J_vec;                // Vector of ones (J)
    std::vector<VectorXd> aux_Ni_vec;  // Vector of ones per sample
    VectorXd aux_Ni;                   // Number of cells per sample

    // ========================================================================
    // Target Data
    // ========================================================================
    std::vector<MatrixXd> target_Yi;              // Expression (J x Ni)
    std::vector<SparseMatrix<double>> target_Mi;  // Counts (sparse)
    std::vector<SparseMatrix<double>> target_M1i; // Paired counts 1
    std::vector<SparseMatrix<double>> target_M2i; // Paired counts 2
    std::vector<MatrixXd> target_Xi;              // Binary indicators

    // ========================================================================
    // Hyperparameters
    // ========================================================================
    VectorXd hyperparams_S_Qi;
    VectorXd hyperparams_S_oi;
    double hyperparams_S_Z;
    double hyperparams_S_A;
    double hyperparams_S_R;
    double hyperparams_S_Qi_mean;
    double hyperparams_S_oi_mean;
    double hyperparams_S_si;
    double hyperparams_S_o;
    VectorXd hyperparams_o_0;
    std::vector<VectorXd> hyperparams_si_0;
    MatrixXd hyperparams_O;

    // ========================================================================
    // Options
    // ========================================================================
    std::string obs_type_;
    std::string mode_;
    bool orthoZ_;
    bool adjustD_;
    bool is_si_fixed_;
    int verbose_;

    // ========================================================================
    // Workspace (Pre-allocated for Performance)
    // ========================================================================
    MatrixXd workspace_Y_res;
    MatrixXd workspace_B_concat;
    MatrixXd workspace_ZD;
    MatrixXd workspace_CtC_inv;
    MatrixXd workspace_HpHp_inv;
    MatrixXd workspace_Yp;

    // ========================================================================
    // Tracking Storage (Pre-allocated)
    // ========================================================================
    MatrixXd tracking_prev_Z;
    MatrixXd tracking_prev_A;
    MatrixXd tracking_prev_Ro;
    VectorXd tracking_prev_o;
    std::vector<MatrixXd> tracking_prev_Bi;
    std::vector<MatrixXd> tracking_prev_Qi;
    std::vector<MatrixXd> tracking_prev_Rk;
    std::vector<VectorXd> tracking_prev_si;
    std::vector<VectorXd> tracking_prev_oi;

    std::vector<double> tracking_sigma2;
    std::vector<double> tracking_dZ;
    std::vector<double> tracking_dA;
    std::vector<double> tracking_do;
    std::vector<double> tracking_dRo;
    std::vector<std::vector<double>> tracking_dsi;
    std::vector<std::vector<double>> tracking_doi;
    std::vector<std::vector<double>> tracking_dBi;
    std::vector<std::vector<double>> tracking_dQi;
    std::vector<std::vector<double>> tracking_dRk;

    // ========================================================================
    // State
    // ========================================================================
    bool is_initialized_;
    int total_iterations;

    // ========================================================================
    // Private Methods - Initialization
    // ========================================================================
    void solve_oi_all_init();
    void compute_residual_Yp();
    void perform_rsvd();
    void initialize_Z_U_S_from_svd();
    void initialize_Qi_from_Z();
    void solve_initial_Bi_all();

    // ========================================================================
    // Private Methods - Optimization Steps
    // ========================================================================
    void solve_Bi_all();
    void normalize_B(bool adjust_D);
    void update_QiDBi();
    void solve_Z_orthogonal();
    void solve_Z_regular();
    void update_ZDBi();
    void solve_Qi_all();
    void solve_oi_all();
    void solve_si_all();
    void solve_o();
    void solve_Yi_all();
    double solve_sigma2();
    void update_hyperpriors();
    void solve_A();
    void solve_Rk_all();
    void solve_Ro();

    // ========================================================================
    // Private Methods - Tracking
    // ========================================================================
    void calculate_tracking(int iteration);

    // ========================================================================
    // Private Methods - Utilities
    // ========================================================================
    void precompute_CtC_inverse();
    void precompute_HpHp_inverse();
};

} // namespace gedi
