# Copyright (c) Microsoft Corporation.
# SPDX-License-Identifier: Apache-2.0 WITH LLVM-exception

set(STL_BUILD_ROOT "${PROJECT_BINARY_DIR}/out")
set(STL_SOURCE_DIR "${PROJECT_SOURCE_DIR}")
set(STL_TEST_OUTPUT_DIR "${CMAKE_CURRENT_BINARY_DIR}")
set(STL_TEST_UTILS_DIR "${CMAKE_CURRENT_SOURCE_DIR}/utils")
set(STL_TESTED_HEADERS_DIR "${STL_BUILD_ROOT}/inc")

set(LLVM_PROJECT_SOURCE_DIR "${STL_SOURCE_DIR}/llvm-project" CACHE PATH
    "Location of the llvm-project source tree")
set(LIBCXX_SOURCE_DIR "${LLVM_PROJECT_SOURCE_DIR}/libcxx" CACHE PATH
    "Location of the libcxx source tree")
set(LLVM_SOURCE_DIR "${LLVM_PROJECT_SOURCE_DIR}/llvm" CACHE PATH
    "Location of the llvm source tree")

set(STL_LIT ${CMAKE_CURRENT_BINARY_DIR}/stl-lit.$<CONFIG>.py)

set(Python_FIND_STRATEGY VERSION)
find_package(Python3)

add_subdirectory(libcxx)
add_subdirectory(std)
add_subdirectory(tr1)

get_property(STL_LIT_CONFIG_MAP GLOBAL PROPERTY STL_LIT_CONFIG_MAP)
configure_file(
    ${CMAKE_CURRENT_SOURCE_DIR}/utils/stl/stl-lit.in
    ${CMAKE_CURRENT_BINARY_DIR}/stl-lit.in)
file(GENERATE OUTPUT ${STL_LIT} INPUT ${CMAKE_CURRENT_BINARY_DIR}/stl-lit.in)
