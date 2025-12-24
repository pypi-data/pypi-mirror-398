cmake_minimum_required(VERSION 3.15)
project(${SKBUILD_PROJECT_NAME} LANGUAGES CXX)

add_subdirectory(${CMAKE_CURRENT_SOURCE_DIR}/src/suitesparse)

find_package(Python 3.10 REQUIRED
  COMPONENTS Interpreter Development.Module
  OPTIONAL_COMPONENTS Development.SABIModule
)
find_package(nanobind CONFIG REQUIRED)

nanobind_add_module(_ext NB_STATIC STABLE_ABI src/_ext/main.cc)
target_link_libraries(_ext PRIVATE klu)
install(TARGETS _ext LIBRARY DESTINATION nbklu)