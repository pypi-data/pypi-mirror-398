# C++ extension module for GEDI
pybind11_add_module(_gedi2py_cpp
    bindings.cpp
    gedi_core.cpp
    gedi_projections.cpp
    gedi_differential.cpp
    gedi_imputation.cpp
    gedi_dimred.cpp
)

# Link Eigen
target_link_libraries(_gedi2py_cpp PRIVATE Eigen3::Eigen)

# Link OpenMP if available
if(OpenMP_CXX_FOUND)
    target_link_libraries(_gedi2py_cpp PRIVATE OpenMP::OpenMP_CXX)
    target_compile_definitions(_gedi2py_cpp PRIVATE GEDI_USE_OPENMP)
endif()

# Compiler warnings and optimization flags
if(MSVC)
    target_compile_options(_gedi2py_cpp PRIVATE /W3)
else()
    target_compile_options(_gedi2py_cpp PRIVATE -Wall -Wextra -Wpedantic)
    # Match R's optimization flags for fair performance comparison
    # R uses: -march=nocona -mtune=haswell -ftree-vectorize
    target_compile_options(_gedi2py_cpp PRIVATE
        -march=nocona
        -mtune=haswell
        -ftree-vectorize
    )
endif()

# Install target
install(TARGETS _gedi2py_cpp DESTINATION gedi2py)
