cmake_minimum_required(VERSION 4.0)
project(GraphLayout)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)

option(GRAPH_LAYOUT_ENABLE_TESTS "Build tests" OFF)
option(GRAPH_LAYOUT_ENABLE_RANDOM_TESTS "Build random tests" OFF)
option(GRAPH_LAYOUT_ENABLE_STRICT "Use strict compile options" OFF)
option(GRAPH_LAYOUT_ENABLE_COVERAGE "Enable coverage reporting" OFF)
option(GRAPH_LAYOUT_BIND_PYTHON "Enable python binding" OFF)
option(GRAPH_LAYOUT_BIND_ES "Enable ECMAScript binding" OFF)

if(APPLE)
    set(ENV{PKG_CONFIG_PATH} "/opt/homebrew/lib/pkgconfig:$ENV{PKG_CONFIG_PATH}")
endif()

include(FetchContent)

FetchContent_Declare(
        SVGDiagram
        GIT_REPOSITORY https://github.com/CyberZHG/SVGDiagram.git
        GIT_TAG v1.3.0
)

FetchContent_MakeAvailable(SVGDiagram)

if(GRAPH_LAYOUT_ENABLE_STRICT)
    if (CMAKE_CXX_COMPILER_ID MATCHES "Clang|GNU")
        add_compile_options(
                -Wall
                -Wextra
                -Werror
                -Wpedantic
                -Wmissing-include-dirs
                -Wundef
                -Wredundant-decls
        )
    endif()
endif()

if(GRAPH_LAYOUT_ENABLE_COVERAGE)
    if(CMAKE_CXX_COMPILER_ID MATCHES "GNU|Clang")
        add_compile_options(--coverage -O0 -g)
        add_link_options(--coverage)
    endif()
endif()

add_library(GraphLayout STATIC
        include/graph_layout.h
        src/graph_layout.cpp
        include/directed/feedback_arcs.h
        src/directed/feedback_arcs.cpp
        include/common/graph_def.h
        src/common/graph_def.cpp
        include/directed/layer_assignment.h
        src/directed/layer_assignment.cpp
        src/common/graph_def_splitter.cpp
        include/directed/cross_minimization.h
        src/directed/cross_minimization.cpp
        include/common/binary_indexed_tree.h
        src/common/binary_indexed_tree.cpp
        include/directed/vertex_positioning.h
        src/directed/vertex_positioning.cpp
        include/common/graph_attributes.h
        src/common/graph_attributes.cpp
        include/common/compare_svg.h
        src/common/compare_svg.cpp
)

target_include_directories(GraphLayout
        PUBLIC ${CMAKE_CURRENT_SOURCE_DIR}/include
)

target_link_libraries(GraphLayout
        PRIVATE SVGDiagram
)

if(GRAPH_LAYOUT_ENABLE_TESTS)
    enable_testing()

    FetchContent_Declare(
            googletest
            GIT_REPOSITORY https://github.com/google/googletest.git
            GIT_TAG v1.17.0
    )

    FetchContent_MakeAvailable(googletest)

    add_executable(runTests
            tests/test_main.cpp
            tests/feedback_arcs/test_eades_93.cpp
            tests/layer_assignment/test_topological.cpp
            tests/graph_def/test_component_splitter.cpp
            tests/layer_assignment/test_gansner_93.cpp
            tests/cross_minimization/test_cross_minimization.cpp
            tests/cross_minimization/test_barycenter.cpp
            tests/cross_minimization/test_median.cpp
            tests/cross_minimization/test_pairwise_switch.cpp
            tests/vertex_positioning/test_brandes_kopf.cpp
            tests/graph_layout/test_directed_graph_hierarchical_layout.cpp
            tests/feedback_arcs/test_min_id.cpp
            tests/docs/test_basic.cpp
            tests/docs/test_graph_attr.cpp
            tests/docs/test_vertex_attr.cpp
            tests/docs/test_edge_attr.cpp
    )

    target_link_libraries(runTests
            PRIVATE GraphLayout
            PRIVATE gtest gtest_main
    )

    if (GRAPH_LAYOUT_ENABLE_RANDOM_TESTS)
        target_compile_definitions(runTests
                PRIVATE GRAPH_LAYOUT_ENABLE_RANDOM_TESTS=ON
        )
    endif ()

    add_test(NAME GraphLayoutTests COMMAND runTests)
endif ()

if(GRAPH_LAYOUT_BIND_PYTHON)
    include(FetchContent)
    FetchContent_Declare(
            pybind11
            GIT_REPOSITORY https://github.com/pybind/pybind11.git
            GIT_TAG v3.0
    )
    FetchContent_MakeAvailable(pybind11)

    pybind11_add_module(_core
            python/bindings.cpp
    )
    target_link_libraries(_core
            PRIVATE GraphLayout
    )
    install(TARGETS _core
            LIBRARY DESTINATION sp_graph_layout)
    install(FILES python/wrapper/__init__.py DESTINATION sp_graph_layout)
endif()

if (GRAPH_LAYOUT_BIND_ES)

    add_executable(GraphLayoutWASM
            wasm/graph_layout_wasm.cpp)

    target_link_libraries(GraphLayoutWASM
            PRIVATE GraphLayout
    )

    target_compile_options(GraphLayoutWASM PRIVATE "-O3")

    set_target_properties(GraphLayoutWASM PROPERTIES SUFFIX ".js")

    target_link_options(GraphLayoutWASM PRIVATE
            "--bind"
            "-sMODULARIZE=1"
            "-sEXPORT_ES6=1"
            "-sEXPORT_NAME=GraphLayoutWASMModule"
    )
endif ()
