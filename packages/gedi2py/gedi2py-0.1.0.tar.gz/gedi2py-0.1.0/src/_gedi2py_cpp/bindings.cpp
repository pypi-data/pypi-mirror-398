/**
 * GEDI Python bindings using pybind11
 *
 * This file defines the Python module interface for the GEDI C++ backend.
 */

#include <pybind11/pybind11.h>
#include <pybind11/eigen.h>
#include <pybind11/stl.h>

#include "gedi_core.hpp"
#include "gedi_projections.hpp"
#include "gedi_imputation.hpp"
#include "gedi_differential.hpp"
#include "gedi_dimred.hpp"

namespace py = pybind11;
using namespace Eigen;
using namespace gedi;

PYBIND11_MODULE(_gedi2py_cpp, m) {
    m.doc() = R"pbdoc(
        GEDI C++ Backend
        ----------------

        This module provides the C++ implementation of the GEDI algorithm
        for single-cell RNA-seq data integration.

        .. currentmodule:: _gedi2py_cpp

        .. autosummary::
           :toctree: _generate

           GEDI
           compute_ZDB
           compute_DB
           compute_ADB
    )pbdoc";

    // ========================================================================
    // GEDI Class Binding
    // ========================================================================
    py::class_<GEDI>(m, "GEDI", R"pbdoc(
        Core GEDI model class.

        This class implements the latent variable model with block coordinate
        descent optimization for single-cell data integration.
    )pbdoc")
        .def(py::init<
            // Dimensions
            int, int, int, int, int, int,
            // Initial parameters
            const std::vector<MatrixXd>&,  // Bi
            const std::vector<MatrixXd>&,  // Qi
            const std::vector<VectorXd>&,  // si
            const std::vector<VectorXd>&,  // oi
            const VectorXd&,               // o
            const MatrixXd&,               // Z
            const MatrixXd&,               // U
            const VectorXd&,               // S
            const VectorXd&,               // D
            double,                        // sigma2
            // Target data
            const std::vector<MatrixXd>&,  // Yi
            // Options
            const std::string&,            // obs_type
            const std::string&,            // mode
            bool,                          // orthoZ
            bool,                          // adjustD
            bool,                          // is_si_fixed
            int,                           // verbose
            int                            // num_threads
        >(),
            py::arg("J"), py::arg("N"), py::arg("K"),
            py::arg("P"), py::arg("L"), py::arg("numSamples"),
            py::arg("Bi"), py::arg("Qi"), py::arg("si"), py::arg("oi"),
            py::arg("o"), py::arg("Z"), py::arg("U"), py::arg("S"), py::arg("D"),
            py::arg("sigma2"),
            py::arg("Yi"),
            py::arg("obs_type") = "M",
            py::arg("mode") = "Bsphere",
            py::arg("orthoZ") = true,
            py::arg("adjustD") = true,
            py::arg("is_si_fixed") = false,
            py::arg("verbose") = 1,
            py::arg("num_threads") = 0
        )

        // Core methods - release GIL for long computations
        .def("initialize", &GEDI::initialize,
             py::arg("multimodal") = false,
             py::call_guard<py::gil_scoped_release>(),
             "Initialize latent variables via randomized SVD")

        .def("optimize", &GEDI::optimize,
             py::arg("iterations"),
             py::arg("track_interval") = 5,
             py::call_guard<py::gil_scoped_release>(),
             "Run block coordinate descent optimization")

        .def("train", &GEDI::train,
             py::arg("iterations"),
             py::arg("track_interval") = 5,
             py::arg("multimodal") = false,
             py::call_guard<py::gil_scoped_release>(),
             "Initialize and optimize (combined method)")

        // Parameter getters
        .def("get_Z", &GEDI::get_Z, "Get shared metagenes matrix (J x K)")
        .def("get_D", &GEDI::get_D, "Get scaling factors (K)")
        .def("get_U", &GEDI::get_U, "Get SVD left vectors (J x K)")
        .def("get_S", &GEDI::get_S, "Get SVD singular values (K)")
        .def("get_o", &GEDI::get_o, "Get global gene offsets (J)")
        .def("get_sigma2", &GEDI::get_sigma2, "Get noise variance")
        .def("get_Bi", &GEDI::get_Bi, "Get cell loadings for all samples")
        .def("get_Qi", &GEDI::get_Qi, "Get sample-specific metagenes")
        .def("get_si", &GEDI::get_si, "Get cell size factors")
        .def("get_oi", &GEDI::get_oi, "Get sample gene offsets")

        // Optional parameter getters (for pathway/covariate models)
        .def("get_A", &GEDI::get_A, "Get pathway coefficients (P x K)")
        .def("get_Rk", &GEDI::get_Rk, "Get covariate effects on metagenes")
        .def("get_Ro", &GEDI::get_Ro, "Get covariate effects on offsets")

        // Auxiliary data getters
        .def("get_ZDBi", &GEDI::get_ZDBi, "Get cached ZDBi projections")
        .def("get_QiDBi", &GEDI::get_QiDBi, "Get cached QiDBi projections")

        // Tracking getters
        .def("get_tracking_sigma2", &GEDI::get_tracking_sigma2,
             "Get sigma2 values over iterations")
        .def("get_tracking_dZ", &GEDI::get_tracking_dZ,
             "Get Z change over iterations")
        .def("get_tracking_dA", &GEDI::get_tracking_dA,
             "Get A change over iterations")
        .def("get_tracking_do", &GEDI::get_tracking_do,
             "Get o change over iterations")

        // State queries
        .def("is_initialized", &GEDI::is_initialized,
             "Check if model is initialized")
        .def("set_initialized", &GEDI::set_initialized,
             py::arg("value"),
             "Set initialized flag (use with caution - for loading pre-initialized states)")
        .def("compute_initial_caches", &GEDI::compute_initial_caches,
             "Compute ZDBi and QiDBi caches from current parameters. "
             "Call this after loading pre-initialized parameters but before optimize()")
        .def("get_total_iterations", &GEDI::get_total_iterations,
             "Get total optimization iterations run")

        // Setters for optional parameters
        .def("set_C", &GEDI::set_C,
             py::arg("C"),
             "Set pathway prior matrix C")
        .def("set_H", &GEDI::set_H,
             py::arg("H"),
             "Set covariate matrix H")
        .def("set_hyperparams", &GEDI::set_hyperparams,
             py::arg("S_Qi"), py::arg("S_oi"), py::arg("S_Z"),
             py::arg("S_A"), py::arg("S_R"), py::arg("S_si"), py::arg("S_o"),
             py::arg("o_0"), py::arg("si_0"), py::arg("O"),
             "Set hyperparameters")
    ;

    // ========================================================================
    // Projection Functions
    // ========================================================================
    m.def("compute_ZDB", &compute_ZDB_cpp,
          py::arg("Z"), py::arg("D"), py::arg("Bi_list"), py::arg("verbose") = 0,
          R"pbdoc(
              Compute ZDB projection (shared manifold).

              Parameters
              ----------
              Z : numpy.ndarray
                  Shared metagenes matrix (J x K)
              D : numpy.ndarray
                  Scaling factors (K)
              Bi_list : list of numpy.ndarray
                  Cell loadings per sample [(K x Ni), ...]
              verbose : int
                  Verbosity level

              Returns
              -------
              numpy.ndarray
                  ZDB projection (J x N)
          )pbdoc");

    m.def("compute_DB", &compute_DB_cpp,
          py::arg("D"), py::arg("Bi_list"), py::arg("verbose") = 0,
          R"pbdoc(
              Compute DB projection (cell embeddings).

              Parameters
              ----------
              D : numpy.ndarray
                  Scaling factors (K)
              Bi_list : list of numpy.ndarray
                  Cell loadings per sample [(K x Ni), ...]
              verbose : int
                  Verbosity level

              Returns
              -------
              numpy.ndarray
                  DB projection (K x N)
          )pbdoc");

    m.def("compute_ADB", &compute_ADB_cpp,
          py::arg("C_rotation"), py::arg("A"), py::arg("D"), py::arg("Bi_list"), py::arg("verbose") = 0,
          R"pbdoc(
              Compute ADB projection (pathway activities).

              Parameters
              ----------
              C_rotation : numpy.ndarray
                  Rotation matrix (num_pathways x P)
              A : numpy.ndarray
                  Pathway coefficients (P x K)
              D : numpy.ndarray
                  Scaling factors (K)
              Bi_list : list of numpy.ndarray
                  Cell loadings per sample [(K x Ni), ...]
              verbose : int
                  Verbosity level

              Returns
              -------
              numpy.ndarray
                  ADB projection (num_pathways x N)
          )pbdoc");

    // ========================================================================
    // Imputation Functions
    // ========================================================================
    m.def("compute_Yi_imputed", &compute_Yi_imputed_cpp,
          py::arg("Yi"), py::arg("ZDBi"), py::arg("QiDBi"),
          py::arg("o"), py::arg("oi"), py::arg("si"),
          R"pbdoc(
              Compute imputed expression values.

              Parameters
              ----------
              Yi : list of numpy.ndarray
                  Expression matrices per sample
              ZDBi : list of numpy.ndarray
                  Shared projections per sample
              QiDBi : list of numpy.ndarray
                  Sample-specific projections
              o : numpy.ndarray
                  Global gene offsets
              oi : list of numpy.ndarray
                  Sample-specific gene offsets
              si : list of numpy.ndarray
                  Cell size factors per sample

              Returns
              -------
              list of numpy.ndarray
                  Imputed matrices per sample
          )pbdoc");

    // ========================================================================
    // Differential Expression Functions
    // ========================================================================
    m.def("get_diff_Q", &getDiffQ_cpp,
          py::arg("Rk_list"), py::arg("H_rotation"), py::arg("contrast"), py::arg("verbose") = 0,
          R"pbdoc(
              Compute differential Q in Z-space.

              Parameters
              ----------
              Rk_list : list of numpy.ndarray
                  List of K matrices (each J x L)
              H_rotation : numpy.ndarray
                  Rotation matrix (L x num_covariates)
              contrast : numpy.ndarray
                  Contrast vector (length L)
              verbose : int
                  Verbosity level

              Returns
              -------
              numpy.ndarray
                  diffQ matrix (J x K)
          )pbdoc");

    m.def("get_diff_O", &getDiffO_cpp,
          py::arg("Ro"), py::arg("H_rotation"), py::arg("contrast"), py::arg("verbose") = 0,
          R"pbdoc(
              Compute differential gene offsets.

              Parameters
              ----------
              Ro : numpy.ndarray
                  Matrix (J x L)
              H_rotation : numpy.ndarray
                  Rotation matrix (L x num_covariates)
              contrast : numpy.ndarray
                  Contrast vector (length L)
              verbose : int
                  Verbosity level

              Returns
              -------
              numpy.ndarray
                  diffO vector (length J)
          )pbdoc");

    m.def("get_diff_exp", &getDiffExp_cpp,
          py::arg("Rk_list"), py::arg("H_rotation"), py::arg("contrast"),
          py::arg("D"), py::arg("Bi_list"), py::arg("verbose") = 0,
          R"pbdoc(
              Compute cell-specific differential expression.

              Parameters
              ----------
              Rk_list : list of numpy.ndarray
                  List of K matrices (each J x L)
              H_rotation : numpy.ndarray
                  Rotation matrix (L x num_covariates)
              contrast : numpy.ndarray
                  Contrast vector (length L)
              D : numpy.ndarray
                  Scaling factors (K)
              Bi_list : list of numpy.ndarray
                  Cell loadings per sample
              verbose : int
                  Verbosity level

              Returns
              -------
              numpy.ndarray
                  diffExp matrix (J x N)
          )pbdoc");

    // ========================================================================
    // Dimensionality Reduction Functions
    // ========================================================================

    // Bind the SVDResult struct
    py::class_<SVDResult>(m, "SVDResult",
        "Result of factorized SVD containing singular values and vectors")
        .def_readonly("d", &SVDResult::d, "Singular values")
        .def_readonly("u", &SVDResult::u, "Left singular vectors")
        .def_readonly("v", &SVDResult::v, "Right singular vectors");

    m.def("compute_svd_factorized", &compute_svd_factorized_cpp,
          py::arg("Z"), py::arg("D"), py::arg("Bi_list"), py::arg("verbose") = 0,
          R"pbdoc(
              Compute factorized SVD.

              Parameters
              ----------
              Z : numpy.ndarray
                  Shared metagenes matrix (J x K)
              D : numpy.ndarray
                  Scaling factors (K)
              Bi_list : list of numpy.ndarray
                  Cell loadings per sample

              Returns
              -------
              SVDResult
                  SVD result with d, u, v components
          )pbdoc");

    m.def("run_factorized_svd", &run_factorized_svd_cpp,
          py::arg("Z"), py::arg("projDB"), py::arg("verbose") = 0,
          R"pbdoc(
              Run factorized SVD on custom projection.

              Parameters
              ----------
              Z : numpy.ndarray
                  Shared metagenes matrix (J x K)
              projDB : numpy.ndarray
                  Custom projection matrix (K x N_total)

              Returns
              -------
              SVDResult
                  SVD result with d, u, v components
          )pbdoc");

    m.def("compute_pca", &compute_pca_cpp,
          py::arg("svd_result"), py::arg("n_components"), py::arg("scale") = true,
          R"pbdoc(
              Compute PCA from factorized SVD.

              Parameters
              ----------
              svd_result : SVDResult
                  Result from compute_svd_factorized
              n_components : int
                  Number of components to return
              scale : bool
                  Whether to scale by singular values

              Returns
              -------
              numpy.ndarray
                  PCA coordinates (N x n_components)
          )pbdoc");

    // ========================================================================
    // Module Version
    // ========================================================================
    m.attr("__version__") = "0.1.0";
}
