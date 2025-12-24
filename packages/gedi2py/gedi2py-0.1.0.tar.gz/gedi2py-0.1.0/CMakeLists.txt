cmake_minimum_required(VERSION 3.15...3.27)
project(gedi2py VERSION 0.1.0 LANGUAGES CXX)

# C++ standard
set(CMAKE_CXX_STANDARD 14)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# Position independent code (required for shared libraries)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)

# Find Python
find_package(Python REQUIRED COMPONENTS Interpreter Development.Module)

# Find pybind11
find_package(pybind11 CONFIG REQUIRED)

# Find Eigen3
find_package(Eigen3 3.3 REQUIRED NO_MODULE)

# Find OpenMP (optional)
find_package(OpenMP)

# Add the C++ source directory
add_subdirectory(src/_gedi2py_cpp)
