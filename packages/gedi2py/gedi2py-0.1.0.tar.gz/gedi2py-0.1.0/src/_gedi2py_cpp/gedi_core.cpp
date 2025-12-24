/**
 * GEDI Core - Implementation
 *
 * Core GEDI class with block coordinate descent optimization.
 * Ported from gedi2 R package (RcppEigen) to pybind11.
 */

#include "gedi_core.hpp"
#include <iostream>
#include <algorithm>
#include <numeric>

#ifdef GEDI_USE_OPENMP
#include <omp.h>
#endif

namespace gedi {

// ============================================================================
// Helper Functions
// ============================================================================

MatrixXd sparse_log1p(const SparseMatrix<double>& M) {
    MatrixXd result = MatrixXd::Zero(M.rows(), M.cols());

    for (int k = 0; k < M.outerSize(); ++k) {
        for (SparseMatrix<double>::InnerIterator it(M, k); it; ++it) {
            result(it.row(), it.col()) = std::log1p(it.value());
        }
    }

    return result;
}

MatrixXd sparse_log_ratio(const SparseMatrix<double>& M1, const SparseMatrix<double>& M2) {
    MatrixXd result = MatrixXd(M1.rows(), M1.cols());

    for (Index j = 0; j < M1.cols(); ++j) {
        for (Index i = 0; i < M1.rows(); ++i) {
            double m1_val = M1.coeff(i, j);
            double m2_val = M2.coeff(i, j);
            result(i, j) = std::log((m1_val + 1.0) / (m2_val + 1.0));
        }
    }

    return result;
}

// ============================================================================
// Timer Class
// ============================================================================

FunctionTimer::FunctionTimer(const std::string& name, int verbose_level)
    : function_name(name), verbose(verbose_level),
      start_time(std::chrono::high_resolution_clock::now()) {}

FunctionTimer::~FunctionTimer() {
    if (verbose >= 4) {
        auto end_time = std::chrono::high_resolution_clock::now();
        auto duration = std::chrono::duration_cast<std::chrono::microseconds>(end_time - start_time);
        std::cout << "      [TIMING] " << function_name << ": " << duration.count() << " us" << std::endl;
    }
}

// ============================================================================
// GEDI Class Implementation
// ============================================================================

GEDI::GEDI(
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
    const std::string& obs_type,
    const std::string& mode,
    bool orthoZ,
    bool adjustD,
    bool is_si_fixed,
    int verbose,
    int num_threads
) :
    J_(J), N_(N), K_(K), P_(P), L_(L), numSamples_(numSamples),
    num_threads_(num_threads),
    params_Bi(Bi), params_Qi(Qi), params_si(si), params_oi(oi),
    params_o(o), params_Z(Z), params_U(U), params_S(S), params_D(D),
    params_sigma2(sigma2),
    target_Yi(Yi),
    obs_type_(obs_type), mode_(mode),
    orthoZ_(orthoZ), adjustD_(adjustD), is_si_fixed_(is_si_fixed),
    verbose_(verbose),
    is_initialized_(false),
    total_iterations(0)
{
    // Initialize auxiliary data structures
    aux_ZDBi.resize(numSamples_);
    aux_QiDBi.resize(numSamples_);
    aux_Ni_vec.resize(numSamples_);
    aux_Ni = VectorXd(numSamples_);

    for (int i = 0; i < numSamples_; ++i) {
        int Ni = static_cast<int>(Bi[i].cols());
        aux_Ni(i) = Ni;
        aux_Ni_vec[i] = VectorXd::Ones(Ni);
        aux_ZDBi[i] = MatrixXd::Zero(J_, Ni);
        aux_QiDBi[i] = MatrixXd::Zero(J_, Ni);
    }

    aux_diag_K = MatrixXd::Identity(K_, K_);
    aux_J_vec = VectorXd::Ones(J_);

    // Initialize hyperparameters with defaults
    hyperparams_S_Qi = VectorXd::Ones(numSamples_);
    hyperparams_S_oi = VectorXd::Ones(numSamples_);
    hyperparams_S_Z = 1.0;
    hyperparams_S_A = 1.0;
    hyperparams_S_R = 1.0;
    hyperparams_S_Qi_mean = 1.0;
    hyperparams_S_oi_mean = 1.0;
    hyperparams_S_si = 1.0;
    hyperparams_S_o = 1.0;
    hyperparams_o_0 = VectorXd::Zero(J_);

    hyperparams_si_0.resize(numSamples_);
    for (int i = 0; i < numSamples_; ++i) {
        hyperparams_si_0[i] = VectorXd::Zero(static_cast<int>(aux_Ni(i)));
    }

    // Initialize random projection matrix for rSVD
    hyperparams_O = MatrixXd::Random(N_, K_ + 5);

    // Pre-allocate workspace
    workspace_Y_res = MatrixXd(J_, N_);
    workspace_B_concat = MatrixXd(K_, N_);
    workspace_ZD = MatrixXd(J_, K_);
    workspace_Yp = MatrixXd(J_, N_);

    // Pre-allocate tracking storage
    tracking_prev_Z.resize(J_, K_);
    tracking_prev_o.resize(J_);
    if (P_ > 0) {
        params_A = MatrixXd::Zero(P_, K_);
        tracking_prev_A.resize(P_, K_);
    }
    if (L_ > 0) {
        params_Rk.resize(K_);
        for (int k = 0; k < K_; ++k) {
            params_Rk[k] = MatrixXd::Zero(J_, L_);
        }
        params_Ro = MatrixXd::Zero(J_, L_);
        tracking_prev_Ro.resize(J_, L_);
        aux_Qi_hat.resize(numSamples_);
        aux_oi_hat.resize(numSamples_);
        for (int i = 0; i < numSamples_; ++i) {
            aux_Qi_hat[i] = MatrixXd::Zero(J_, K_);
            aux_oi_hat[i] = VectorXd::Zero(J_);
        }
    }

    tracking_prev_Bi.resize(numSamples_);
    tracking_prev_Qi.resize(numSamples_);
    tracking_prev_si.resize(numSamples_);
    tracking_prev_oi.resize(numSamples_);

    for (int i = 0; i < numSamples_; ++i) {
        int Ni = static_cast<int>(aux_Ni(i));
        tracking_prev_Bi[i].resize(K_, Ni);
        tracking_prev_Qi[i].resize(J_, K_);
        tracking_prev_si[i].resize(Ni);
        tracking_prev_oi[i].resize(J_);
    }

    if (L_ > 0) {
        tracking_prev_Rk.resize(K_);
        for (int k = 0; k < K_; ++k) {
            tracking_prev_Rk[k].resize(J_, L_);
        }
    }

    // Initialize tracking vectors
    tracking_dsi.resize(numSamples_);
    tracking_doi.resize(numSamples_);
    tracking_dBi.resize(numSamples_);
    tracking_dQi.resize(numSamples_);
    tracking_dRk.resize(K_);

#ifdef GEDI_USE_OPENMP
    if (num_threads_ > 0) {
        omp_set_num_threads(num_threads_);
    }
#endif

    if (verbose_ >= 1) {
        std::cout << "[GEDI] Model created: " << J_ << " genes × " << N_ << " cells"
                  << " × " << K_ << " factors × " << numSamples_ << " samples" << std::endl;
    }
}

void GEDI::initialize(bool multimodal) {
    if (verbose_ >= 1 && !multimodal) {
        std::cout << "Initializing latent variables..." << std::endl;
    }

    {
        FunctionTimer timer("solve_oi_all", verbose_);
        solve_oi_all_init();
    }

    {
        FunctionTimer timer("compute_residual_Yp", verbose_);
        compute_residual_Yp();
    }

    {
        FunctionTimer timer("perform_rsvd", verbose_);
        perform_rsvd();
    }

    {
        FunctionTimer timer("initialize_from_svd", verbose_);
        initialize_Z_U_S_from_svd();
        initialize_Qi_from_Z();
        solve_initial_Bi_all();
    }

    if (!multimodal) {
        {
            FunctionTimer timer("normalize_B", verbose_);
            normalize_B(false);
        }
        {
            FunctionTimer timer("update_ZDBi", verbose_);
            update_ZDBi();
        }
        {
            FunctionTimer timer("update_QiDBi", verbose_);
            update_QiDBi();
        }
    }

    is_initialized_ = true;

    if (verbose_ >= 1 && !multimodal) {
        std::cout << "Initialization complete." << std::endl;
    }
}

void GEDI::optimize(int iterations, int track_interval) {
    if (!is_initialized_) {
        throw std::runtime_error("Model must be initialized before optimization. Call initialize() first.");
    }

#ifdef GEDI_USE_OPENMP
    int original_threads = omp_get_max_threads();
    if (num_threads_ > 0) {
        omp_set_num_threads(num_threads_);
    }
    int actual_threads = omp_get_max_threads();
    if (verbose_ >= 1) {
        std::cout << "OpenMP enabled: Using " << actual_threads << " threads" << std::endl;
    }
#else
    if (verbose_ >= 1 && num_threads_ > 0) {
        std::cout << "OpenMP not available - using single-threaded execution" << std::endl;
    }
#endif

    auto start_time = std::chrono::high_resolution_clock::now();

    // Resize tracking vectors
    int current_size = static_cast<int>(tracking_sigma2.size());
    tracking_sigma2.resize(current_size + iterations);
    tracking_dZ.resize(current_size + iterations, std::nan(""));
    tracking_dA.resize(current_size + iterations, std::nan(""));
    tracking_do.resize(current_size + iterations, std::nan(""));
    tracking_dRo.resize(current_size + iterations, std::nan(""));

    for (int i = 0; i < numSamples_; ++i) {
        tracking_dsi[i].resize(current_size + iterations, std::nan(""));
        tracking_doi[i].resize(current_size + iterations, std::nan(""));
        tracking_dBi[i].resize(current_size + iterations, std::nan(""));
        tracking_dQi[i].resize(current_size + iterations, std::nan(""));
    }
    for (int k = 0; k < K_; ++k) {
        tracking_dRk[k].resize(current_size + iterations, std::nan(""));
    }

    if (verbose_ >= 1) {
        std::cout << "Starting block coordinate descent optimization..." << std::endl;
        std::cout << "Parameters: " << iterations << " iterations, " << numSamples_
                  << " samples, " << J_ << " genes, " << K_ << " factors" << std::endl;
    }

    for (int ite = 0; ite < iterations; ++ite) {
        int tracking_idx = current_size + ite;
        bool do_tracking = (ite % track_interval == 0) || (track_interval == 1);

        if (do_tracking) {
            // Store current values for tracking
            tracking_prev_Z.noalias() = params_Z;
            tracking_prev_o.noalias() = params_o;
            if (P_ > 0) tracking_prev_A.noalias() = params_A;
            if (L_ > 0) tracking_prev_Ro.noalias() = params_Ro;

            for (int i = 0; i < numSamples_; ++i) {
                tracking_prev_Bi[i].noalias() = params_Bi[i];
                tracking_prev_Qi[i].noalias() = params_Qi[i];
                tracking_prev_si[i].noalias() = params_si[i];
                tracking_prev_oi[i].noalias() = params_oi[i];
            }

            if (L_ > 0) {
                for (int k = 0; k < K_; ++k) {
                    tracking_prev_Rk[k].noalias() = params_Rk[k];
                }
            }
        }

        if (verbose_ >= 1) {
            std::cout << "  Iteration " << (ite + 1) << "/" << iterations << std::endl;
        }

        {
            FunctionTimer timer("solve_Bi_all", verbose_);
            solve_Bi_all();
        }

        {
            FunctionTimer timer("normalize_B", verbose_);
            normalize_B(false);
        }

        {
            FunctionTimer timer("update_QiDBi (1)", verbose_);
            update_QiDBi();
        }

        if (orthoZ_) {
            FunctionTimer timer("solve_Z_orthogonal", verbose_);
            solve_Z_orthogonal();
        } else {
            FunctionTimer timer("solve_Z_regular", verbose_);
            solve_Z_regular();
        }

        {
            FunctionTimer timer("update_ZDBi", verbose_);
            update_ZDBi();
        }

        {
            FunctionTimer timer("solve_Qi_all", verbose_);
            solve_Qi_all();
        }

        {
            FunctionTimer timer("update_QiDBi (2)", verbose_);
            update_QiDBi();
        }

        {
            FunctionTimer timer("solve_oi_all", verbose_);
            solve_oi_all();
        }

        if (!is_si_fixed_) {
            FunctionTimer timer("solve_si_all", verbose_);
            solve_si_all();
        }

        {
            FunctionTimer timer("solve_o", verbose_);
            solve_o();
        }

        {
            FunctionTimer timer("solve_Yi_all", verbose_);
            solve_Yi_all();
        }

        {
            FunctionTimer timer("solve_sigma2", verbose_);
            params_sigma2 = solve_sigma2();
        }
        tracking_sigma2[tracking_idx] = params_sigma2;

        if (verbose_ >= 1) {
            std::cout << "    sigma2: " << params_sigma2 << std::endl;
        }

        {
            FunctionTimer timer("update_hyperpriors", verbose_);
            update_hyperpriors();
        }

        if (verbose_ >= 2) {
            std::cout << "    Mean(o): " << hyperparams_o_0[0]
                      << "; Var(o): " << hyperparams_S_o
                      << "; Var(si): " << hyperparams_S_si << std::endl;
        }

        if (P_ > 0) {
            FunctionTimer timer("solve_A", verbose_);
            solve_A();
        }

        if (L_ > 0) {
            {
                FunctionTimer timer("solve_Rk_all", verbose_);
                solve_Rk_all();
            }
            {
                FunctionTimer timer("solve_Ro", verbose_);
                solve_Ro();
            }
        }

        if (do_tracking) {
            FunctionTimer timer("calculate_tracking", verbose_);
            calculate_tracking(tracking_idx);
        }
    }

    auto end_time = std::chrono::high_resolution_clock::now();
    auto duration = std::chrono::duration_cast<std::chrono::milliseconds>(end_time - start_time);

#ifdef GEDI_USE_OPENMP
    omp_set_num_threads(original_threads);
#endif

    total_iterations += iterations;

    if (verbose_ >= 1) {
        std::cout << "Optimization completed in " << duration.count() << " ms" << std::endl;
        std::cout << "Final sigma2: " << params_sigma2 << std::endl;
    }
}

void GEDI::train(int iterations, int track_interval, bool multimodal) {
    if (verbose_ >= 1) {
        std::cout << "Starting GEDI training (initialization + optimization)..." << std::endl;
    }

    initialize(multimodal);
    optimize(iterations, track_interval);

    if (verbose_ >= 1) {
        std::cout << "Training complete." << std::endl;
    }
}

// ============================================================================
// Setter Methods
// ============================================================================

void GEDI::set_C(const MatrixXd& C) {
    aux_C = C;
    precompute_CtC_inverse();
}

void GEDI::set_H(const MatrixXd& H) {
    aux_H = H;
}

void GEDI::set_hyperparams(
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
) {
    hyperparams_S_Qi = S_Qi;
    hyperparams_S_oi = S_oi;
    hyperparams_S_Z = S_Z;
    hyperparams_S_A = S_A;
    hyperparams_S_R = S_R;
    hyperparams_S_si = S_si;
    hyperparams_S_o = S_o;
    hyperparams_o_0 = o_0;
    hyperparams_si_0 = si_0;
    hyperparams_O = O;
}

void GEDI::set_Mi(const std::vector<SparseMatrix<double>>& Mi) {
    target_Mi = Mi;
    // Compute Yi = log1p(Mi)
    for (int i = 0; i < numSamples_; ++i) {
        target_Yi[i] = sparse_log1p(target_Mi[i]);
    }
}

void GEDI::set_M1i_M2i(const std::vector<SparseMatrix<double>>& M1i,
                       const std::vector<SparseMatrix<double>>& M2i) {
    target_M1i = M1i;
    target_M2i = M2i;
    // Compute Yi = log((M1+1)/(M2+1))
    for (int i = 0; i < numSamples_; ++i) {
        target_Yi[i] = sparse_log_ratio(target_M1i[i], target_M2i[i]);
    }
}

void GEDI::set_Xi(const std::vector<MatrixXd>& Xi) {
    target_Xi = Xi;
    // Convert: 1 -> 1, 0 -> -1, NA -> 0
    for (int i = 0; i < numSamples_; ++i) {
        target_Yi[i] = target_Xi[i];
        for (Index j = 0; j < target_Yi[i].rows(); ++j) {
            for (Index k = 0; k < target_Yi[i].cols(); ++k) {
                double val = target_Xi[i](j, k);
                if (std::isnan(val)) {
                    target_Yi[i](j, k) = 0.0;
                } else if (val == 0.0) {
                    target_Yi[i](j, k) = -1.0;
                } else {
                    target_Yi[i](j, k) = 1.0;
                }
            }
        }
    }
}

// ============================================================================
// Private Methods - Initialization
// ============================================================================

void GEDI::solve_oi_all_init() {
    for (int i = 0; i < numSamples_; ++i) {
        double lambda = 1.0 / hyperparams_S_oi(i);
        double Ni_val = aux_Ni(i);

        MatrixXd residual = target_Yi[i] - aux_ZDBi[i] - aux_QiDBi[i];
        residual.rowwise() -= params_si[i].transpose();
        residual.colwise() -= params_o;

        VectorXd row_sums = residual * aux_Ni_vec[i];

        if (L_ == 0) {
            params_oi[i] = row_sums / (Ni_val + lambda);
        } else {
            params_oi[i] = (row_sums + lambda * aux_oi_hat[i]) / (Ni_val + lambda);
        }
    }
}

void GEDI::compute_residual_Yp() {
    int current_col_offset = 0;
    for (int i = 0; i < numSamples_; ++i) {
        int Ni = static_cast<int>(aux_Ni(i));
        VectorXd gene_offset = params_o + params_oi[i];

        MatrixXd sample_residual = target_Yi[i];
        sample_residual.colwise() -= gene_offset;
        sample_residual.rowwise() -= params_si[i].transpose();

        workspace_Yp.block(0, current_col_offset, J_, Ni) = sample_residual;
        current_col_offset += Ni;
    }
}

void GEDI::perform_rsvd() {
    // Randomized SVD implementation
    int m = workspace_Yp.rows();
    int n = workspace_Yp.cols();
    int k = K_;
    int q = 2;  // Power iterations

    MatrixXd A = workspace_Yp;
    bool flipped = false;

    if (m < n) {
        A = A.transpose().eval();
        std::swap(m, n);
        flipped = true;
    }

    // Y = A * O
    MatrixXd Y = A * hyperparams_O.topRows(n);

    MatrixXd Q(m, Y.cols());
    if (q > 0) {
        for (int i = 0; i < q; ++i) {
            HouseholderQR<MatrixXd> qr_y(Y);
            Q = qr_y.householderQ() * MatrixXd::Identity(m, Y.cols());

            MatrixXd Z_temp = A.transpose() * Q;

            HouseholderQR<MatrixXd> qr_z(Z_temp);
            MatrixXd Q_z = qr_z.householderQ() * MatrixXd::Identity(n, Z_temp.cols());

            Y = A * Q_z;
        }
    }

    HouseholderQR<MatrixXd> qr_final(Y);
    Q = qr_final.householderQ() * MatrixXd::Identity(m, Y.cols());

    MatrixXd B = Q.transpose() * A;

    JacobiSVD<MatrixXd> svd(B, ComputeThinU | ComputeThinV);
    VectorXd singular_values = svd.singularValues();
    MatrixXd matrix_u = svd.matrixU();

    MatrixXd final_u = Q * matrix_u.leftCols(k);

    if (flipped) {
        // If we flipped, the result needs adjustment
        params_Z = final_u * singular_values.head(k).asDiagonal() / 2.0;
    } else {
        params_Z = final_u * singular_values.head(k).asDiagonal() / 2.0;
    }

    params_U = final_u;
    params_S = singular_values.head(k) / 2.0;
}

void GEDI::initialize_Z_U_S_from_svd() {
    // Already done in perform_rsvd
}

void GEDI::initialize_Qi_from_Z() {
    for (int i = 0; i < numSamples_; ++i) {
        params_Qi[i] = params_Z;
    }
}

void GEDI::solve_initial_Bi_all() {
    for (int i = 0; i < numSamples_; ++i) {
        MatrixXd Wi(J_, K_);
        for (int k = 0; k < K_; ++k) {
            Wi.col(k) = (params_Z.col(k) + params_Qi[i].col(k)) * params_D(k);
        }

        VectorXd gene_offset = params_o + params_oi[i];
        MatrixXd residual = target_Yi[i];
        residual.colwise() -= gene_offset;
        residual.rowwise() -= params_si[i].transpose();

        MatrixXd WtW = Wi.transpose() * Wi;
        MatrixXd WtY = Wi.transpose() * residual;
        LDLT<MatrixXd> solver(WtW);
        params_Bi[i] = solver.solve(aux_diag_K * WtY);
    }
}

// ============================================================================
// Private Methods - Optimization Steps
// ============================================================================

void GEDI::solve_Bi_all() {
#ifdef GEDI_USE_OPENMP
#pragma omp parallel for schedule(guided) if(numSamples_ > 1)
#endif
    for (int i = 0; i < numSamples_; ++i) {
        MatrixXd Wi(J_, K_);
        for (int k = 0; k < K_; ++k) {
            Wi.col(k) = (params_Z.col(k) + params_Qi[i].col(k)) * params_D(k);
        }

        VectorXd gene_offset = params_o + params_oi[i];
        MatrixXd residual = target_Yi[i];
        residual.colwise() -= gene_offset;
        residual.rowwise() -= params_si[i].transpose();

        MatrixXd WtW = Wi.transpose() * Wi;
        MatrixXd WtY = Wi.transpose() * residual;

        LDLT<MatrixXd> solver(WtW);
        params_Bi[i] = solver.solve(aux_diag_K * WtY);
    }
}

void GEDI::normalize_B(bool multimodal) {
    if (!multimodal && mode_ == "Bsphere") {
        for (int i = 0; i < numSamples_; ++i) {
            VectorXd col_norms = params_Bi[i].colwise().norm();
            for (Index j = 0; j < params_Bi[i].cols(); ++j) {
                if (col_norms(j) > 1e-10) {
                    double scale = 1.0 / col_norms(j);
                    params_Bi[i].col(j) *= scale;
                }
            }
        }
    }

    VectorXd total_row_norms = VectorXd::Zero(K_);
    for (int i = 0; i < numSamples_; ++i) {
        total_row_norms += params_Bi[i].rowwise().squaredNorm();
    }
    total_row_norms = total_row_norms.cwiseSqrt();

    VectorXd row_scaling = VectorXd::Ones(K_);
    for (int k = 0; k < K_; ++k) {
        if (total_row_norms(k) > 1e-10) {
            row_scaling(k) = 1.0 / total_row_norms(k);
        }
    }

    if (!multimodal && mode_ == "Bl2") {
        for (int i = 0; i < numSamples_; ++i) {
            for (int k = 0; k < K_; ++k) {
                params_Bi[i].row(k) *= row_scaling(k);
            }
        }
    } else if (adjustD_) {
        params_D = row_scaling;
    }
}

void GEDI::update_QiDBi() {
#ifdef GEDI_USE_OPENMP
#pragma omp parallel for schedule(static) if(numSamples_ > 2)
#endif
    for (int i = 0; i < numSamples_; ++i) {
        MatrixXd QiD = params_Qi[i] * params_D.asDiagonal();
        aux_QiDBi[i].noalias() = QiD * params_Bi[i];
    }
}

void GEDI::update_ZDBi() {
    workspace_ZD.noalias() = params_Z * params_D.asDiagonal();

#ifdef GEDI_USE_OPENMP
#pragma omp parallel for schedule(static) if(numSamples_ > 2)
#endif
    for (int i = 0; i < numSamples_; ++i) {
        aux_ZDBi[i].noalias() = workspace_ZD * params_Bi[i];
    }
}

void GEDI::solve_Z_orthogonal() {
    int total_cells = N_;

    std::vector<int> col_offsets(numSamples_ + 1);
    col_offsets[0] = 0;
    for (int i = 0; i < numSamples_; ++i) {
        col_offsets[i + 1] = col_offsets[i] + static_cast<int>(aux_Ni(i));
    }

#ifdef GEDI_USE_OPENMP
#pragma omp parallel for schedule(static) if(numSamples_ > 2)
#endif
    for (int i = 0; i < numSamples_; ++i) {
        int Ni = static_cast<int>(aux_Ni(i));
        int offset = col_offsets[i];
        VectorXd gene_offset = params_o + params_oi[i];

        MatrixXd Yi_res = target_Yi[i] - aux_QiDBi[i];
        Yi_res.colwise() -= gene_offset;
        Yi_res.rowwise() -= params_si[i].transpose();
        workspace_Y_res.block(0, offset, J_, Ni) = Yi_res;

        workspace_B_concat.block(0, offset, K_, Ni) = params_Bi[i];
    }

    MatrixXd B = params_D.asDiagonal() * workspace_B_concat.leftCols(total_cells);

    double lambda = 1.0 / hyperparams_S_Z;

    MatrixXd Y_final, B_final;

    if (P_ > 0) {
        double sqrt_lambda = std::sqrt(lambda);
        MatrixXd CA_term = sqrt_lambda * aux_C * params_A;
        MatrixXd diagK_term = sqrt_lambda * aux_diag_K;

        Y_final = MatrixXd(J_, total_cells + K_);
        Y_final.leftCols(total_cells) = workspace_Y_res.leftCols(total_cells);
        Y_final.rightCols(K_) = CA_term;

        B_final = MatrixXd(K_, total_cells + K_);
        B_final.leftCols(total_cells) = B;
        B_final.rightCols(K_) = diagK_term;
    } else {
        Y_final = workspace_Y_res.leftCols(total_cells);
        B_final = B;
    }

    MatrixXd SB = params_S.asDiagonal() * B_final;
    MatrixXd Y_SB_T = Y_final * SB.transpose();

    JacobiSVD<MatrixXd> svd(Y_SB_T, ComputeThinU | ComputeThinV);
    params_U = svd.matrixU() * svd.matrixV().transpose();

    MatrixXd YBt = Y_final * B_final.transpose();
    MatrixXd YBtU = YBt.cwiseProduct(params_U);

    params_S = YBtU.transpose() * aux_J_vec / (1.0 + lambda);
    params_Z.noalias() = params_U * params_S.asDiagonal();
}

void GEDI::solve_Z_regular() {
    int total_cells = N_;

    std::vector<int> col_offsets(numSamples_ + 1);
    col_offsets[0] = 0;
    for (int i = 0; i < numSamples_; ++i) {
        col_offsets[i + 1] = col_offsets[i] + static_cast<int>(aux_Ni(i));
    }

#ifdef GEDI_USE_OPENMP
#pragma omp parallel for schedule(static) if(numSamples_ > 2)
#endif
    for (int i = 0; i < numSamples_; ++i) {
        int Ni = static_cast<int>(aux_Ni(i));
        int offset = col_offsets[i];
        VectorXd gene_offset = params_o + params_oi[i];

        MatrixXd Yi_res = target_Yi[i] - aux_QiDBi[i];
        Yi_res.colwise() -= gene_offset;
        Yi_res.rowwise() -= params_si[i].transpose();
        workspace_Y_res.block(0, offset, J_, Ni) = Yi_res;

        workspace_B_concat.block(0, offset, K_, Ni) = params_Bi[i];
    }

    double lambda = 1.0 / hyperparams_S_Z;

    MatrixXd B = workspace_B_concat.leftCols(total_cells);
    MatrixXd DB = params_D.asDiagonal() * B;
    MatrixXd Y_DB_T = workspace_Y_res.leftCols(total_cells) * DB.transpose();

    if (P_ == 0) {
        MatrixXd gram = DB * DB.transpose() + lambda * aux_diag_K;
        LDLT<MatrixXd> solver(gram);
        params_Z = Y_DB_T * solver.solve(aux_diag_K);
    } else {
        MatrixXd CA_term = lambda * aux_C * params_A;
        MatrixXd gram = DB * DB.transpose() + lambda * aux_diag_K;
        LDLT<MatrixXd> solver(gram);
        params_Z = (Y_DB_T + CA_term) * solver.solve(aux_diag_K);
    }
}

void GEDI::solve_Qi_all() {
#ifdef GEDI_USE_OPENMP
#pragma omp parallel for schedule(guided) if(numSamples_ > 1)
#endif
    for (int i = 0; i < numSamples_; ++i) {
        double lambda = 1.0 / hyperparams_S_Qi(i);

        VectorXd gene_offset = params_o + params_oi[i];
        MatrixXd residual = target_Yi[i] - aux_ZDBi[i];
        residual.colwise() -= gene_offset;
        residual.rowwise() -= params_si[i].transpose();

        MatrixXd DBi = params_D.asDiagonal() * params_Bi[i];

        MatrixXd gram = DBi * DBi.transpose() + lambda * aux_diag_K;
        LDLT<MatrixXd> solver(gram);

        if (L_ == 0) {
            params_Qi[i] = (residual * DBi.transpose()) * solver.solve(aux_diag_K);
        } else {
            MatrixXd lhs = residual * DBi.transpose() + lambda * aux_Qi_hat[i];
            params_Qi[i] = lhs * solver.solve(aux_diag_K);
        }
    }
}

void GEDI::solve_oi_all() {
#ifdef GEDI_USE_OPENMP
#pragma omp parallel for schedule(static) if(numSamples_ > 2)
#endif
    for (int i = 0; i < numSamples_; ++i) {
        double lambda = 1.0 / hyperparams_S_oi(i);
        double Ni_val = aux_Ni(i);

        MatrixXd residual = target_Yi[i] - aux_ZDBi[i] - aux_QiDBi[i];
        residual.rowwise() -= params_si[i].transpose();
        residual.colwise() -= params_o;

        VectorXd row_sums = residual * aux_Ni_vec[i];

        if (L_ == 0) {
            params_oi[i] = row_sums / (Ni_val + lambda);
        } else {
            params_oi[i] = (row_sums + lambda * aux_oi_hat[i]) / (Ni_val + lambda);
        }
    }
}

void GEDI::solve_si_all() {
    double lambda = 1.0 / hyperparams_S_si;

#ifdef GEDI_USE_OPENMP
#pragma omp parallel for schedule(static) if(numSamples_ > 2)
#endif
    for (int i = 0; i < numSamples_; ++i) {
        VectorXd gene_offset = params_o + params_oi[i];
        MatrixXd residual = target_Yi[i] - aux_ZDBi[i] - aux_QiDBi[i];
        residual.colwise() -= gene_offset;

        VectorXd col_sums = residual.transpose() * aux_J_vec;
        params_si[i] = (col_sums + lambda * hyperparams_si_0[i]) / (J_ + lambda);
    }
}

void GEDI::solve_o() {
    VectorXd o_sum = VectorXd::Zero(J_);

    for (int i = 0; i < numSamples_; ++i) {
        MatrixXd residual = target_Yi[i] - aux_ZDBi[i] - aux_QiDBi[i];
        residual.rowwise() -= params_si[i].transpose();
        residual.colwise() -= params_oi[i];

        o_sum += residual * aux_Ni_vec[i];
    }

    double lambda = 1.0 / hyperparams_S_o;
    params_o = (o_sum + hyperparams_o_0 * lambda) / (N_ + lambda);
}

void GEDI::solve_Yi_all() {
    if (obs_type_ == "Y") {
        return;
    }

#ifdef GEDI_USE_OPENMP
#pragma omp parallel for schedule(guided) if(numSamples_ > 1)
#endif
    for (int i = 0; i < numSamples_; ++i) {
        if (obs_type_ == "M") {
            // Check if target_Mi is available
            if (target_Mi.empty() || i >= static_cast<int>(target_Mi.size())) {
                // Skip Yi update if Mi is not available
                continue;
            }
            ArrayXXd Yi = target_Yi[i].array();
            ArrayXXd ZDBi = aux_ZDBi[i].array();
            ArrayXXd QiDBi = aux_QiDBi[i].array();
            ArrayXd si = params_si[i].array();
            ArrayXd oi = params_oi[i].array();

            ArrayXXd Yi_hat = ((ZDBi + QiDBi).rowwise() + si.transpose()).colwise() +
                (params_o.array() + oi);
            ArrayXXd logMi = (ArrayXXd(MatrixXd(target_Mi[i])) + 1e-10).log();
            ArrayXXd solution = Yi;
            ArrayXXd alpha = Yi - Yi_hat - ArrayXXd(params_sigma2 * MatrixXd(target_Mi[i]));

            const Index total_elements = solution.size();

            for (Index j = 0; j < total_elements; ++j) {
                double exp_Yi, f, fp, fpp, upper, lower;

                if (Yi(j) > 0) {
                    exp_Yi = std::exp(-Yi(j));
                    fpp = params_sigma2;
                    fp = params_sigma2 + exp_Yi;
                    f = params_sigma2 + exp_Yi * alpha(j);
                } else {
                    exp_Yi = std::exp(Yi(j));
                    fpp = params_sigma2 * exp_Yi;
                    fp = fpp + 1.0;
                    f = fpp + alpha(j);
                }

                solution(j) -= 2.0 * f * fp / (2.0 * fp * fp - f * fpp);

                if (logMi(j) < Yi_hat(j)) {
                    upper = Yi_hat(j);
                    lower = logMi(j);
                } else {
                    upper = logMi(j);
                    lower = Yi_hat(j);
                }

                if (solution(j) < lower) {
                    solution(j) = lower;
                } else if (solution(j) > upper) {
                    solution(j) = upper;
                }
            }

            target_Yi[i] = solution.matrix();

        } else if (obs_type_ == "M_paired") {
            ArrayXXd Yi = target_Yi[i].array();
            ArrayXXd ZDBi = aux_ZDBi[i].array();
            ArrayXXd QiDBi = aux_QiDBi[i].array();
            ArrayXd si = params_si[i].array();
            ArrayXd oi = params_oi[i].array();

            ArrayXXd Yi_hat = ((ZDBi + QiDBi).rowwise() + si.transpose()).colwise() +
                (params_o.array() + oi);
            ArrayXXd solution = Yi;
            ArrayXXd alpha = Yi_hat - ArrayXXd(params_sigma2 * MatrixXd(target_M2i[i]));
            ArrayXXd beta = Yi_hat + ArrayXXd(params_sigma2 * MatrixXd(target_M1i[i]));

            const Index total_elements = solution.size();

            for (Index j = 0; j < total_elements; ++j) {
                double exp_Yi, f, fp, fpp;

                if (Yi(j) > 0) {
                    exp_Yi = std::exp(-Yi(j));
                    f = Yi(j) - alpha(j) + (Yi(j) - beta(j)) * exp_Yi;
                    fp = 1.0 + exp_Yi * (beta(j) - Yi(j) + 1.0);
                    fpp = exp_Yi * (Yi(j) - beta(j) - 2.0);
                } else {
                    exp_Yi = std::exp(Yi(j));
                    f = exp_Yi * (Yi(j) - alpha(j)) + Yi(j) - beta(j);
                    fp = exp_Yi + beta(j) - Yi(j) + 1.0;
                    fpp = Yi(j) - beta(j) - 2.0;
                }

                solution(j) -= 2.0 * f * fp / (2.0 * fp * fp - f * fpp);

                if (solution(j) < alpha(j)) {
                    solution(j) = alpha(j);
                } else if (solution(j) > beta(j)) {
                    solution(j) = beta(j);
                }
            }

            target_Yi[i] = solution.matrix();

        } else if (obs_type_ == "X") {
            MatrixXd Yi_pred = (aux_ZDBi[i] + aux_QiDBi[i]).rowwise() + params_si[i].transpose();
            Yi_pred = Yi_pred.colwise() + (params_o + params_oi[i]);

            const Index J_local = Yi_pred.rows();
            const Index Ni = Yi_pred.cols();

            for (Index j = 0; j < J_local; ++j) {
                for (Index n = 0; n < Ni; ++n) {
                    double X_val = target_Xi[i](j, n);

                    if (X_val == 1.0) {
                        double Yi_val = Yi_pred(j, n);
                        double dnorm_val = -0.5 * std::log(2.0 * M_PI) - 0.5 * Yi_val * Yi_val;
                        double pnorm_val = std::log(0.5 * (1.0 + std::erf(Yi_val / std::sqrt(2.0))));
                        target_Yi[i](j, n) = Yi_val + std::exp(dnorm_val - pnorm_val);

                    } else if (X_val == 0.0) {
                        double Yi_val = Yi_pred(j, n);
                        double dnorm_val = -0.5 * std::log(2.0 * M_PI) - 0.5 * Yi_val * Yi_val;
                        double pnorm_val = std::log(0.5 * (1.0 + std::erf(-Yi_val / std::sqrt(2.0))));
                        target_Yi[i](j, n) = Yi_val - std::exp(dnorm_val - pnorm_val);
                    } else {
                        target_Yi[i](j, n) = Yi_pred(j, n);
                    }
                }
            }
        }
    }
}

double GEDI::solve_sigma2() {
    int denom_N = J_ * (N_ + numSamples_) +
        numSamples_ * J_ * K_ +
        (K_ + 1) * J_ * L_ +
        K_ * (J_ + P_);

    double S = 0.0;

    if (P_ == 0) {
        S += params_Z.squaredNorm() / hyperparams_S_Z;
    } else {
        MatrixXd Z_residual = params_Z - aux_C * params_A;
        S += Z_residual.squaredNorm() / hyperparams_S_Z;
        S += params_A.squaredNorm() / hyperparams_S_Z / hyperparams_S_A;
    }

    for (int i = 0; i < numSamples_; ++i) {
        if (L_ == 0) {
            S += params_oi[i].squaredNorm() / hyperparams_S_oi(i);
        } else {
            VectorXd oi_diff = params_oi[i] - aux_oi_hat[i];
            S += oi_diff.squaredNorm() / hyperparams_S_oi(i);
        }

        if (L_ == 0) {
            S += params_Qi[i].squaredNorm() / hyperparams_S_Qi(i);
        } else {
            MatrixXd Qi_diff = params_Qi[i] - aux_Qi_hat[i];
            S += Qi_diff.squaredNorm() / hyperparams_S_Qi(i);
        }

        VectorXd gene_offset = params_o + params_oi[i];
        MatrixXd residual = target_Yi[i] - aux_ZDBi[i] - aux_QiDBi[i];
        residual.colwise() -= gene_offset;
        residual.rowwise() -= params_si[i].transpose();

        if (obs_type_ == "Y") {
            S += residual.squaredNorm();
        } else if (obs_type_ == "M") {
            S += residual.squaredNorm();
            ArrayXXd Yi_exp = target_Yi[i].array().exp();
            ArrayXXd denominator = Yi_exp + (1.0 / params_sigma2);
            S += (1.0 / denominator).sum();
        } else if (obs_type_ == "M_paired") {
            S += residual.squaredNorm();
            ArrayXXd expYi = (-target_Yi[i].array().abs()).exp();
            ArrayXXd M_sum = ArrayXXd(MatrixXd(target_M1i[i] + target_M2i[i]));
            ArrayXXd one_plus_expYi = 1.0 + expYi;
            ArrayXXd denominator = M_sum * expYi / one_plus_expYi.square() +
                (1.0 / params_sigma2);
            S += (1.0 / denominator).sum();
        }
    }

    if (L_ > 0) {
        for (int k = 0; k < K_; ++k) {
            S += params_Rk[k].squaredNorm() / hyperparams_S_Qi_mean / hyperparams_S_R;
        }
        S += params_Ro.squaredNorm() / hyperparams_S_oi_mean / hyperparams_S_R;
    }

    if (obs_type_ != "X") {
        return S / denom_N;
    } else {
        return 1.0;
    }
}

void GEDI::update_hyperpriors() {
    double o_mean = params_o.mean();
    hyperparams_o_0.setConstant(o_mean);
    VectorXd o_diff = params_o - hyperparams_o_0;
    hyperparams_S_o = (o_diff.squaredNorm() + 2.0) / params_sigma2 / (J_ + 2.0);

    double si_sum = 0.0;
    for (int i = 0; i < numSamples_; ++i) {
        VectorXd si_diff = params_si[i] - hyperparams_si_0[i];
        si_sum += si_diff.squaredNorm();
    }
    hyperparams_S_si = (si_sum / params_sigma2 + 2.0) / (N_ + 2.0);
}

void GEDI::solve_A() {
    MatrixXd CtZ = aux_C.transpose() * params_Z;
    params_A = workspace_CtC_inv * CtZ;
}

void GEDI::solve_Rk_all() {
    MatrixXd Hp(L_, numSamples_);
    for (int i = 0; i < numSamples_; ++i) {
        double scaling = 1.0 / std::sqrt(hyperparams_S_Qi(i));
        Hp.col(i) = aux_H.col(i) * scaling;
    }

    double lambda = 1.0 / hyperparams_S_Qi_mean / hyperparams_S_R;
    MatrixXd HpHp_T = Hp * Hp.transpose() + lambda * MatrixXd::Identity(L_, L_);
    LDLT<MatrixXd> solver(HpHp_T);
    workspace_HpHp_inv = solver.solve(MatrixXd::Identity(L_, L_));

    for (int k = 0; k < K_; ++k) {
        MatrixXd Qk(J_, numSamples_);
        for (int i = 0; i < numSamples_; ++i) {
            double scaling = 1.0 / std::sqrt(hyperparams_S_Qi(i));
            Qk.col(i) = params_Qi[i].col(k) * scaling;
        }

        MatrixXd QkHp_T = Qk * Hp.transpose();
        params_Rk[k] = QkHp_T * workspace_HpHp_inv;

        MatrixXd RkH = params_Rk[k] * aux_H;
        for (int i = 0; i < numSamples_; ++i) {
            aux_Qi_hat[i].col(k) = RkH.col(i);
        }
    }
}

void GEDI::solve_Ro() {
    MatrixXd O(J_, numSamples_);
    MatrixXd Hp(L_, numSamples_);

    for (int i = 0; i < numSamples_; ++i) {
        double scaling = 1.0 / std::sqrt(hyperparams_S_oi(i));
        O.col(i) = params_oi[i] * scaling;
        Hp.col(i) = aux_H.col(i) * scaling;
    }

    double lambda = 1.0 / hyperparams_S_oi_mean / hyperparams_S_R;
    MatrixXd HpHp_T = Hp * Hp.transpose() + lambda * MatrixXd::Identity(L_, L_);
    LDLT<MatrixXd> solver(HpHp_T);
    MatrixXd HpHp_inv = solver.solve(MatrixXd::Identity(L_, L_));

    MatrixXd OHp_T = O * Hp.transpose();
    params_Ro = OHp_T * HpHp_inv;

    MatrixXd RoH = params_Ro * aux_H;
    for (int i = 0; i < numSamples_; ++i) {
        aux_oi_hat[i] = RoH.col(i);
    }
}

void GEDI::precompute_CtC_inverse() {
    double lambda = 1.0 / hyperparams_S_A;
    MatrixXd CtC = aux_C.transpose() * aux_C + lambda * MatrixXd::Identity(P_, P_);
    LDLT<MatrixXd> solver(CtC);
    workspace_CtC_inv = solver.solve(MatrixXd::Identity(P_, P_));
}

void GEDI::precompute_HpHp_inverse() {
    // Called when H is set
}

void GEDI::calculate_tracking(int iteration) {
    tracking_do[iteration] = std::sqrt((params_o - tracking_prev_o).squaredNorm() / params_o.size());
    tracking_dZ[iteration] = std::sqrt((params_Z - tracking_prev_Z).squaredNorm() / params_Z.size());

    if (P_ > 0) {
        tracking_dA[iteration] = std::sqrt((params_A - tracking_prev_A).squaredNorm() / params_A.size());
    }

    if (L_ > 0) {
        tracking_dRo[iteration] = std::sqrt((params_Ro - tracking_prev_Ro).squaredNorm() / params_Ro.size());
    }

    for (int i = 0; i < numSamples_; ++i) {
        tracking_dsi[i][iteration] = std::sqrt((params_si[i] - tracking_prev_si[i]).squaredNorm() /
            params_si[i].size());
        tracking_doi[i][iteration] = std::sqrt((params_oi[i] - tracking_prev_oi[i]).squaredNorm() /
            params_oi[i].size());
        tracking_dBi[i][iteration] = std::sqrt((params_Bi[i] - tracking_prev_Bi[i]).squaredNorm() /
            params_Bi[i].size());
        tracking_dQi[i][iteration] = std::sqrt((params_Qi[i] - tracking_prev_Qi[i]).squaredNorm() /
            params_Qi[i].size());
    }

    if (L_ > 0) {
        for (int k = 0; k < K_; ++k) {
            tracking_dRk[k][iteration] = std::sqrt((params_Rk[k] - tracking_prev_Rk[k]).squaredNorm() /
                params_Rk[k].size());
        }
    }
}

// ============================================================================
// compute_initial_caches - Compute ZDBi and QiDBi from current parameters
// ============================================================================
// Call this after loading pre-initialized parameters but before optimize()
// This ensures the cached projections match the loaded parameters

void GEDI::compute_initial_caches() {
    if (verbose_ >= 1) {
        std::cout << "  Computing initial caches (ZDBi, QiDBi)..." << std::endl;
        std::flush(std::cout);
    }

    // Compute ZDBi = Z * D * Bi for all samples
    update_ZDBi();

    // Compute QiDBi = Qi * D * Bi for all samples
    update_QiDBi();

    if (verbose_ >= 1) {
        std::cout << "  Initial caches computed." << std::endl;
        std::flush(std::cout);
    }
}

} // namespace gedi
