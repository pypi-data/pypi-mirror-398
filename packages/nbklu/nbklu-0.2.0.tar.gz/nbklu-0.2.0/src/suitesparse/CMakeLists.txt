project(suitesparse)

file(GLOB SUITESPARSE_CONFIG_SOURCES "${CMAKE_CURRENT_SOURCE_DIR}/suitesparse_config/src/*.c")
add_library(suitesparse_config ${SUITESPARSE_CONFIG_SOURCES})
target_compile_definitions(suitesparse_config PUBLIC NTIMER)
target_include_directories(suitesparse_config PUBLIC ${CMAKE_CURRENT_SOURCE_DIR}/suitesparse_config/include)

file(GLOB SUITESPARSE_AMD_SOURCES "${CMAKE_CURRENT_SOURCE_DIR}/amd/src/*.c")
add_library(amd ${SUITESPARSE_AMD_SOURCES})
target_include_directories(amd PUBLIC ${CMAKE_CURRENT_SOURCE_DIR}/amd/include)
target_link_libraries(amd PUBLIC suitesparse_config)

file(GLOB SUITESPARSE_COLAMD_SOURCES "${CMAKE_CURRENT_SOURCE_DIR}/colamd/src/*.c")
add_library(colamd ${SUITESPARSE_COLAMD_SOURCES})
target_include_directories(colamd PUBLIC ${CMAKE_CURRENT_SOURCE_DIR}/colamd/include)
target_link_libraries(colamd PUBLIC suitesparse_config)

file(GLOB SUITESPARSE_BTF_SOURCES "${CMAKE_CURRENT_SOURCE_DIR}/btf/src/*.c")
add_library(btf ${SUITESPARSE_BTF_SOURCES})
target_include_directories(btf PUBLIC ${CMAKE_CURRENT_SOURCE_DIR}/btf/include)
target_link_libraries(btf PUBLIC suitesparse_config)

file(GLOB SUITESPARSE_KLU_SOURCES "${CMAKE_CURRENT_SOURCE_DIR}/klu/src/*.c")
add_library(klu ${SUITESPARSE_KLU_SOURCES})
target_include_directories(klu PUBLIC ${CMAKE_CURRENT_SOURCE_DIR}/klu/include)
target_link_libraries(klu PUBLIC suitesparse_config amd colamd btf)

set_target_properties(amd btf colamd klu suitesparse_config 
  PROPERTIES POSITION_INDEPENDENT_CODE ON
)
