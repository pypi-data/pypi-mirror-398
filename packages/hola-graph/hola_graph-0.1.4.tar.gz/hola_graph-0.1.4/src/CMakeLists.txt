set(ADAPTAGRAMS ${CMAKE_SOURCE_DIR}/thirdparty/adaptagrams)
set(HOLA_GRAPH_LIB ${ADAPTAGRAMS}/lib)
set(HOLA_GRAPH_INCLUDE ${ADAPTAGRAMS}/include)

# Disable LTO: adaptagrams static libs are built without LTO,
# and on Linux the linker may lack the LTO plugin, causing empty .so files
set(CMAKE_INTERPROCEDURAL_OPTIMIZATION OFF)

# Build the _core Python module
pybind11_add_module(_core hola_graph/_core.cpp)

target_compile_features(_core PRIVATE cxx_std_14)

target_include_directories(_core
    PRIVATE
    ${HOLA_GRAPH_INCLUDE}
)

# Link order matters on Linux: dependents before dependencies
# libdialect -> libcola, libtopology, libavoid
# libtopology -> libcola, libvpsc, libavoid
# libcola -> libvpsc, libproject
if(UNIX AND NOT APPLE)
    # Use linker group to handle circular dependencies
    target_link_libraries(_core
        PRIVATE
        -Wl,--start-group
        ${HOLA_GRAPH_LIB}/libdialect.a
        ${HOLA_GRAPH_LIB}/libtopology.a
        ${HOLA_GRAPH_LIB}/libcola.a
        ${HOLA_GRAPH_LIB}/libavoid.a
        ${HOLA_GRAPH_LIB}/libproject.a
        ${HOLA_GRAPH_LIB}/libvpsc.a
        -Wl,--end-group
    )
else()
    target_link_libraries(_core
        PRIVATE
        ${HOLA_GRAPH_LIB}/libdialect.a
        ${HOLA_GRAPH_LIB}/libtopology.a
        ${HOLA_GRAPH_LIB}/libcola.a
        ${HOLA_GRAPH_LIB}/libavoid.a
        ${HOLA_GRAPH_LIB}/libproject.a
        ${HOLA_GRAPH_LIB}/libvpsc.a
    )
endif()

# Install the extension module (scikit-build-core handles the destination)
install(TARGETS _core LIBRARY DESTINATION .)
