cmake_minimum_required(VERSION 3.18...3.30)

project(hola-graph VERSION "${SKBUILD_PROJECT_VERSION}" LANGUAGES CXX)

# Build adaptagrams if not present
set(ADAPTAGRAMS_DIR "${CMAKE_SOURCE_DIR}/thirdparty/adaptagrams")
if(NOT EXISTS "${ADAPTAGRAMS_DIR}")
    message(STATUS "Adaptagrams not found, running setup script...")
    execute_process(
        COMMAND bash "${CMAKE_SOURCE_DIR}/scripts/setup.sh"
        WORKING_DIRECTORY "${CMAKE_SOURCE_DIR}"
        RESULT_VARIABLE SETUP_RESULT
    )
    if(NOT SETUP_RESULT EQUAL 0)
        message(FATAL_ERROR "Failed to setup adaptagrams dependency")
    endif()
endif()

# Set default build type
if(NOT CMAKE_BUILD_TYPE AND NOT CMAKE_CONFIGURATION_TYPES)
    set(CMAKE_BUILD_TYPE Release CACHE STRING "Choose the type of build." FORCE)
    set_property(CACHE CMAKE_BUILD_TYPE PROPERTY STRINGS "Debug" "Release" "MinSizeRel" "RelWithDebInfo")
endif()

# Find Python and pybind11
find_package(Python 3.9 COMPONENTS Interpreter Development.Module REQUIRED)
find_package(pybind11 CONFIG REQUIRED)

# Add source subdirectory
add_subdirectory(src)
