set(src_containers
    containers/containers.cpp
)
nanobind_add_module(_containers ${src_containers})
set(src_containers_cuda
    containers/containers.cu
)
if (PyTNL_BUILD_CUDA)
    nanobind_add_module(_containers_cuda ${src_containers_cuda})
endif()
set(src_matrices
    matrices/matrices.cpp
)
nanobind_add_module(matrices ${src_matrices})
set(src_matrices_cuda
    matrices/matrices.cu
)
if (PyTNL_BUILD_CUDA)
    nanobind_add_module(matrices_cuda ${src_matrices_cuda})
endif()
set(src_meshes
    meshes/topologies.cpp
    meshes/VTKTraits.cpp
    meshes/Grid1D.cpp
    meshes/Grid2D.cpp
    meshes/Grid3D.cpp
    meshes/Mesh.cpp
    meshes/MeshReaders.cpp
    meshes/MeshWriters.cpp
    meshes/resolveMeshType.cpp
    meshes/DistributedMesh.cpp
    meshes/DistributedMeshReaders.cpp
    meshes/DistributedMeshWriters.cpp
    meshes/distributeSubentities.cpp
    meshes/meshes.cpp
)
set(src_meshes_cuda
    # VTKTraits has no GPU code
    meshes/Grid1D.cu
    meshes/Grid2D.cu
    meshes/Grid3D.cu
    meshes/Mesh.cu
    meshes/MeshReaders.cu
    meshes/MeshWriters.cu
    meshes/resolveMeshType.cu
    meshes/DistributedMesh.cu
    meshes/DistributedMeshReaders.cu
    meshes/DistributedMeshWriters.cu
    # distributeSubentities is host-only
    meshes/meshes.cu
)
nanobind_add_module(_meshes ${src_meshes})

# add dependencies
target_compile_definitions(_meshes PUBLIC "-DHAVE_ZLIB -DHAVE_TINYXML2")
target_link_libraries(_meshes PUBLIC ZLIB::ZLIB tinyxml2::tinyxml2)

# enable MPI
find_package(MPI COMPONENTS CXX REQUIRED)
target_compile_definitions(_meshes PUBLIC "-DHAVE_MPI")
target_link_libraries(_meshes PUBLIC MPI::MPI_CXX)

if (PyTNL_BUILD_CUDA)
    nanobind_add_module(_meshes_cuda ${src_meshes_cuda})

    # add dependencies
    target_compile_definitions(_meshes_cuda PUBLIC "-DHAVE_ZLIB -DHAVE_TINYXML2")
    target_link_libraries(_meshes_cuda PUBLIC ZLIB::ZLIB tinyxml2::tinyxml2)

    # enable MPI
    find_package(MPI COMPONENTS CXX REQUIRED)
    target_compile_definitions(_meshes_cuda PUBLIC "-DHAVE_MPI")
    target_link_libraries(_meshes_cuda PUBLIC MPI::MPI_CXX)
endif()

# define a list of modules
set(modules
    _containers
    matrices
    _meshes
)

# define a mapping for stub files
# (needed because the stubgen in recursive mode may generate multiple files
# when `.def_submodule` is used and cmake cannot automatically detect them)
set(module_stubs__containers _containers.pyi)
set(module_stubs__containers_cuda _containers_cuda.pyi)
set(module_stubs_matrices matrices.pyi)
set(module_stubs_matrices_cuda matrices_cuda.pyi)
set(module_stubs__meshes _meshes/__init__.pyi _meshes/topologies.pyi)
set(module_stubs__meshes_cuda _meshes_cuda.pyi)

# define a mapping for dependencies between the modules
set(module_depends__containers)
set(module_depends_matrices _containers)
set(module_depends__meshes _containers)

# add CUDA modules
if (PyTNL_BUILD_CUDA)
    list(APPEND modules
            _containers_cuda
            matrices_cuda
            _meshes_cuda
    )
    set(module_depends__containers_cuda _containers)
    set(module_depends_matrices_cuda _containers_cuda _containers)
    set(module_depends__meshes_cuda _containers_cuda _meshes _containers)
endif()

# set common properties
foreach(target IN ITEMS ${modules})
    # enable position-independent code
    set_target_properties(${target} PROPERTIES POSITION_INDEPENDENT_CODE TRUE)

    # enable link-time optimization
    set_target_properties(${target} PROPERTIES INTERPROCEDURAL_OPTIMIZATION ${PyTNL_ENABLE_INTERPROCEDURAL_OPTIMIZATION})

    # add TNL and PyTNL
    target_link_libraries(${target} PUBLIC PyTNL::PyTNL)

    # generate stub files for Python static type checking
    nanobind_add_stub(
        ${target}_stub
        MODULE ${target}
        RECURSIVE
        OUTPUT ${module_stubs_${target}}
        PYTHON_PATH $<TARGET_FILE_DIR:${target}> $<TARGET_FILE_DIR:${target}>/..
        DEPENDS ${target} ${module_depends_${target}}
    )

    # install the module
    install(TARGETS ${target} DESTINATION ${PyTNL_PYTHON_SITE_PACKAGES_DIR}/pytnl)

    # install the stub file(s)
    list(GET module_stubs_${target} 0 _first_stub)
    get_filename_component(_module_directory ${_first_stub} DIRECTORY)
    if (NOT _module_directory STREQUAL "")
        install(
            DIRECTORY ${CMAKE_CURRENT_BINARY_DIR}/${_module_directory}
            DESTINATION ${PyTNL_PYTHON_SITE_PACKAGES_DIR}/pytnl
        )
    else()
        install(
            FILES ${CMAKE_CURRENT_BINARY_DIR}/${module_stubs_${target}}
            DESTINATION ${PyTNL_PYTHON_SITE_PACKAGES_DIR}/pytnl
        )
    endif()
endforeach()

# make the modules importable from the build directory
# (needed for the stub generation due to binary modules importing themselves as `pytnl._containers` etc.)
file(TOUCH ${CMAKE_CURRENT_BINARY_DIR}/__init__.py)

# one marker per module directory
file(TOUCH ${CMAKE_CURRENT_BINARY_DIR}/py.typed)
install(FILES ${CMAKE_CURRENT_BINARY_DIR}/py.typed DESTINATION ${PyTNL_PYTHON_SITE_PACKAGES_DIR}/pytnl)
