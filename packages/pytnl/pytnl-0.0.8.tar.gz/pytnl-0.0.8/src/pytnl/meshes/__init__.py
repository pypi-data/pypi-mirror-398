from __future__ import annotations  # noqa: I001

import importlib
from typing import TYPE_CHECKING, Any, Literal, overload

import pytnl._meshes
import pytnl._meta
import pytnl.devices
from pytnl._meshes import topologies

# Import objects where Pythonizations are not needed
from pytnl._meshes import (
    XMLVTK,
    MeshReader,
    PVTUReader,
    VTIReader,
    VTKCellGhostTypes,
    VTKDataType,
    VTKEntityShape,
    VTKFileFormat,
    VTKPointGhostTypes,
    VTKReader,
    VTKTypesArrayType,
    VTUReader,
    distributeFaces,  # Note: host-only function
    getMeshReader,
)

# Import type aliases/variables
from pytnl._meta import DIMS, DT

if TYPE_CHECKING:
    # This is an optional module - at runtime it is lazy-imported in
    # `CPPClassTemplate`, for type checking there must be the import statement.
    import pytnl._meshes_cuda as _meshes_cuda  # type: ignore[import-not-found, unused-ignore]

__all__ = [
    "XMLVTK",
    "DistributedMesh",
    "Grid",
    "Mesh",
    "MeshReader",
    "PVTUReader",
    "PVTUWriter",
    "VTIReader",
    "VTIWriter",
    "VTKCellGhostTypes",
    "VTKDataType",
    "VTKEntityShape",
    "VTKFileFormat",
    "VTKPointGhostTypes",
    "VTKReader",
    "VTKTypesArrayType",
    "VTKWriter",
    "VTUReader",
    "VTUWriter",
    "distributeFaces",
    "getMeshReader",
    "resolveAndLoadMesh",
    "resolveMeshType",
    "topologies",
]

type TopologiesType = (
    topologies.Edge | topologies.Hexahedron | topologies.Polygon | topologies.Polyhedron | topologies.Quadrangle | topologies.Tetrahedron | topologies.Triangle
)


class _GridMeta(pytnl._meta.CPPClassTemplate):
    _cpp_module = pytnl._meshes
    _class_prefix = "Grid"
    _template_parameters = (
        ("dimension", int),
        ("device_type", type),
    )
    _device_parameter = "device_type"

    @overload
    def __getitem__(
        self,
        key: Literal[1] | tuple[Literal[1], type[pytnl.devices.Host]],
        /,
    ) -> type[pytnl._meshes.Grid_1]: ...

    @overload
    def __getitem__(
        self,
        key: Literal[2] | tuple[Literal[2], type[pytnl.devices.Host]],
        /,
    ) -> type[pytnl._meshes.Grid_2]: ...

    @overload
    def __getitem__(
        self,
        key: Literal[3] | tuple[Literal[3], type[pytnl.devices.Host]],
        /,
    ) -> type[pytnl._meshes.Grid_3]: ...

    @overload
    def __getitem__(  # type: ignore[no-any-unimported, unused-ignore]
        self,
        key: tuple[Literal[1], type[pytnl.devices.Cuda]],
        /,
    ) -> type[_meshes_cuda.Grid_1]: ...  # pyright: ignore[reportUnknownMemberType]

    @overload
    def __getitem__(  # type: ignore[no-any-unimported, unused-ignore]
        self,
        key: tuple[Literal[2], type[pytnl.devices.Cuda]],
        /,
    ) -> type[_meshes_cuda.Grid_2]: ...  # pyright: ignore[reportUnknownMemberType]

    @overload
    def __getitem__(  # type: ignore[no-any-unimported, unused-ignore]
        self,
        key: tuple[Literal[3], type[pytnl.devices.Cuda]],
        /,
    ) -> type[_meshes_cuda.Grid_3]: ...  # pyright: ignore[reportUnknownMemberType]

    def __getitem__(
        self,
        key: DIMS | tuple[DIMS, type[DT]],
        /,
    ) -> type[Any]:
        if isinstance(key, tuple):
            items = key
        else:
            # make a tuple of arguments, use host as the default device
            items = (key, pytnl.devices.Host)
        return self._get_cpp_class(items)


class Grid(metaclass=_GridMeta):
    """
    Allows `Grid[dimension, device_type]` syntax to resolve to
    the appropriate C++ `Grid` class.

    This class provides a Python interface to C++ orthogonal grids.

    The `device_type` argument is optional and defaults to `pytnl.devices.Host`.

    Examples:
    - `Grid[1]` → `_meshes.Grid_1`
    - `Grid[2, devices.Cuda]` → `_meshes_cuda.Grid_2`
    - `Grid[3, devices.Host]` → `_meshes.Grid_3`
    """


class _MeshMeta(pytnl._meta.CPPClassTemplate):
    _cpp_module = pytnl._meshes
    _class_prefix = "Mesh"
    _template_parameters = (
        ("topology", type),
        ("device_type", type),
    )
    _device_parameter = "device_type"

    @overload
    def __getitem__(
        self,
        key: type[topologies.Edge] | tuple[type[topologies.Edge], type[pytnl.devices.Host]],
        /,
    ) -> type[pytnl._meshes.Mesh_Edge]: ...

    @overload
    def __getitem__(
        self,
        key: type[topologies.Hexahedron] | tuple[type[topologies.Hexahedron], type[pytnl.devices.Host]],
        /,
    ) -> type[pytnl._meshes.Mesh_Hexahedron]: ...

    @overload
    def __getitem__(
        self,
        key: type[topologies.Polygon] | tuple[type[topologies.Polygon], type[pytnl.devices.Host]],
        /,
    ) -> type[pytnl._meshes.Mesh_Polygon]: ...

    @overload
    def __getitem__(
        self,
        key: type[topologies.Polyhedron] | tuple[type[topologies.Polyhedron], type[pytnl.devices.Host]],
        /,
    ) -> type[pytnl._meshes.Mesh_Polyhedron]: ...

    @overload
    def __getitem__(
        self,
        key: type[topologies.Quadrangle] | tuple[type[topologies.Quadrangle], type[pytnl.devices.Host]],
        /,
    ) -> type[pytnl._meshes.Mesh_Quadrangle]: ...

    @overload
    def __getitem__(
        self,
        key: type[topologies.Tetrahedron] | tuple[type[topologies.Tetrahedron], type[pytnl.devices.Host]],
        /,
    ) -> type[pytnl._meshes.Mesh_Tetrahedron]: ...

    @overload
    def __getitem__(
        self,
        key: type[topologies.Triangle] | tuple[type[topologies.Triangle], type[pytnl.devices.Host]],
        /,
    ) -> type[pytnl._meshes.Mesh_Triangle]: ...

    @overload
    def __getitem__(  # type: ignore[no-any-unimported, unused-ignore]
        self,
        key: tuple[type[topologies.Edge], type[pytnl.devices.Cuda]],
        /,
    ) -> type[_meshes_cuda.Mesh_Edge]: ...  # pyright: ignore

    @overload
    def __getitem__(  # type: ignore[no-any-unimported, unused-ignore]
        self,
        key: tuple[type[topologies.Hexahedron], type[pytnl.devices.Cuda]],
        /,
    ) -> type[_meshes_cuda.Mesh_Hexahedron]: ...  # pyright: ignore

    @overload
    def __getitem__(  # type: ignore[no-any-unimported, unused-ignore]
        self,
        key: tuple[type[topologies.Polygon], type[pytnl.devices.Cuda]],
        /,
    ) -> type[_meshes_cuda.Mesh_Polygon]: ...  # pyright: ignore

    @overload
    def __getitem__(  # type: ignore[no-any-unimported, unused-ignore]
        self,
        key: tuple[type[topologies.Polyhedron], type[pytnl.devices.Cuda]],
        /,
    ) -> type[_meshes_cuda.Mesh_Polyhedron]: ...  # pyright: ignore

    @overload
    def __getitem__(  # type: ignore[no-any-unimported, unused-ignore]
        self,
        key: tuple[type[topologies.Quadrangle], type[pytnl.devices.Cuda]],
        /,
    ) -> type[_meshes_cuda.Mesh_Quadrangle]: ...  # pyright: ignore

    @overload
    def __getitem__(  # type: ignore[no-any-unimported, unused-ignore]
        self,
        key: tuple[type[topologies.Tetrahedron], type[pytnl.devices.Cuda]],
        /,
    ) -> type[_meshes_cuda.Mesh_Tetrahedron]: ...  # pyright: ignore

    @overload
    def __getitem__(  # type: ignore[no-any-unimported, unused-ignore]
        self,
        key: tuple[type[topologies.Triangle], type[pytnl.devices.Cuda]],
        /,
    ) -> type[_meshes_cuda.Mesh_Triangle]: ...  # pyright: ignore

    def __getitem__(
        self,
        key: type[TopologiesType] | tuple[type[TopologiesType], type[DT]],
        /,
    ) -> type[Any]:
        if isinstance(key, tuple):
            items = key
        else:
            # make a tuple of arguments, use host as the default device
            items = (key, pytnl.devices.Host)
        return self._get_cpp_class(items)


class Mesh(metaclass=_MeshMeta):
    """
    Allows `Mesh[topology_type, device_type]` syntax to resolve to
    the appropriate C++ `Mesh` class.

    This class provides a Python interface to C++ unstructured meshes.

    The `device_type` argument is optional and defaults to `pytnl.devices.Host`.

    Examples:
    - `Mesh[topologies.Edge]` → `_meshes.Mesh_Edge`
    - `Grid[topologies.Triangle, devices.Cuda]` → `_meshes_cuda.Mesh_Triangle`
    - `Grid[topologies.Tetrahedron, devices.Host]` → `_meshes.Mesh_Tetrahedron`
    """


class _DistributedMeshMeta(pytnl._meta.CPPClassTemplate):
    _cpp_module = pytnl._meshes
    _class_prefix = "DistributedMesh"
    _template_parameters = (("mesh_type", type),)
    _dispatch_same_module_parameter = "mesh_type"

    @overload
    def __getitem__(
        self,
        key: type[pytnl._meshes.Mesh_Edge],
        /,
    ) -> type[pytnl._meshes.DistributedMesh_Edge]: ...

    @overload
    def __getitem__(
        self,
        key: type[pytnl._meshes.Mesh_Hexahedron],
        /,
    ) -> type[pytnl._meshes.DistributedMesh_Hexahedron]: ...

    @overload
    def __getitem__(
        self,
        key: type[pytnl._meshes.Mesh_Quadrangle],
        /,
    ) -> type[pytnl._meshes.DistributedMesh_Quadrangle]: ...

    @overload
    def __getitem__(
        self,
        key: type[pytnl._meshes.Mesh_Tetrahedron],
        /,
    ) -> type[pytnl._meshes.DistributedMesh_Tetrahedron]: ...

    @overload
    def __getitem__(
        self,
        key: type[pytnl._meshes.Mesh_Triangle],
        /,
    ) -> type[pytnl._meshes.DistributedMesh_Triangle]: ...

    @overload
    def __getitem__(  # type: ignore[overload-cannot-match, no-any-unimported, unused-ignore]
        self,
        key: type[_meshes_cuda.Mesh_Edge],  # pyright: ignore
        /,
    ) -> type[_meshes_cuda.DistributedMesh_Edge]: ...  # pyright: ignore

    @overload
    def __getitem__(  # type: ignore[overload-cannot-match, no-any-unimported, unused-ignore]
        self,
        key: type[_meshes_cuda.Mesh_Hexahedron],  # pyright: ignore
        /,
    ) -> type[_meshes_cuda.DistributedMesh_Hexahedron]: ...  # pyright: ignore

    @overload
    def __getitem__(  # type: ignore[overload-cannot-match, no-any-unimported, unused-ignore]
        self,
        key: type[_meshes_cuda.Mesh_Quadrangle],  # pyright: ignore
        /,
    ) -> type[_meshes_cuda.DistributedMesh_Quadrangle]: ...  # pyright: ignore

    @overload
    def __getitem__(  # type: ignore[overload-cannot-match, no-any-unimported, unused-ignore]
        self,
        key: type[_meshes_cuda.Mesh_Tetrahedron],  # pyright: ignore
        /,
    ) -> type[_meshes_cuda.DistributedMesh_Tetrahedron]: ...  # pyright: ignore

    @overload
    def __getitem__(  # type: ignore[overload-cannot-match, no-any-unimported, unused-ignore]
        self,
        key: type[_meshes_cuda.Mesh_Triangle],  # pyright: ignore
        /,
    ) -> type[_meshes_cuda.DistributedMesh_Triangle]: ...  # pyright: ignore

    def __getitem__(  # type: ignore[no-any-unimported, unused-ignore]
        self,
        key: type[  # pyright: ignore
            pytnl._meshes.Mesh_Edge
            | pytnl._meshes.Mesh_Hexahedron
            | pytnl._meshes.Mesh_Quadrangle
            | pytnl._meshes.Mesh_Tetrahedron
            | pytnl._meshes.Mesh_Triangle
            | _meshes_cuda.Mesh_Edge  # pyright: ignore
            | _meshes_cuda.Mesh_Hexahedron  # pyright: ignore
            | _meshes_cuda.Mesh_Quadrangle  # pyright: ignore
            | _meshes_cuda.Mesh_Tetrahedron  # pyright: ignore
            | _meshes_cuda.Mesh_Triangle  # pyright: ignore
        ],
        /,
    ) -> type[Any]:
        items = (key,)  # pyright: ignore
        return self._get_cpp_class(items)  # pyright: ignore


class DistributedMesh(metaclass=_DistributedMeshMeta):
    """
    Allows `DistributedMesh[mesh_type]` syntax to resolve to
    the appropriate C++ `DistributedMesh` class.

    This class provides a Python interface to C++ distributed unstructured meshes.

    Example:
    - `DistributedMesh[Mesh[topologies.Edge]]` → `DistributedMesh_Edge`
    - `DistributedMesh[Mesh[topologies.Polygon]]` → `DistributedMesh_Polygon`
    """


class _VTIWriterMeta(pytnl._meta.CPPClassTemplate):
    _cpp_module = pytnl._meshes
    _class_prefix = "VTIWriter"
    _template_parameters = (("grid_type", type),)
    _dispatch_same_module_parameter = "grid_type"

    @overload
    def __getitem__(
        self,
        key: type[pytnl._meshes.Grid_1],
        /,
    ) -> type[pytnl._meshes.VTIWriter_Grid_1]: ...

    @overload
    def __getitem__(
        self,
        key: type[pytnl._meshes.Grid_2],
        /,
    ) -> type[pytnl._meshes.VTIWriter_Grid_2]: ...

    @overload
    def __getitem__(
        self,
        key: type[pytnl._meshes.Grid_3],
        /,
    ) -> type[pytnl._meshes.VTIWriter_Grid_3]: ...

    @overload
    def __getitem__(  # type: ignore[no-any-unimported, unused-ignore]
        self,
        key: type[_meshes_cuda.Grid_1],  # pyright: ignore
        /,
    ) -> type[_meshes_cuda.VTIWriter_Grid_1]: ...  # pyright: ignore

    @overload
    def __getitem__(  # type: ignore[no-any-unimported, overload-cannot-match, unused-ignore]
        self,
        key: type[_meshes_cuda.Grid_2],  # pyright: ignore
        /,
    ) -> type[_meshes_cuda.VTIWriter_Grid_2]: ...  # pyright: ignore

    @overload
    def __getitem__(  # type: ignore[no-any-unimported, overload-cannot-match, unused-ignore]
        self,
        key: type[_meshes_cuda.Grid_3],  # pyright: ignore
        /,
    ) -> type[_meshes_cuda.VTIWriter_Grid_3]: ...  # pyright: ignore

    def __getitem__(  # type: ignore[no-any-unimported, unused-ignore]
        self,
        key: type[  # pyright: ignore
            pytnl._meshes.Grid_1
            | pytnl._meshes.Grid_2
            | pytnl._meshes.Grid_3
            | _meshes_cuda.Grid_1  # pyright: ignore
            | _meshes_cuda.Grid_2  # pyright: ignore
            | _meshes_cuda.Grid_3,  # pyright: ignore
        ],
        /,
    ) -> type[Any]:
        items = (key,)  # pyright: ignore
        return self._get_cpp_class(items)  # pyright: ignore


class VTIWriter(metaclass=_VTIWriterMeta):
    """
    Allows `VTIWriter[grid_type]` syntax to resolve to
    the appropriate C++ `VTIWriter` class.

    This class provides a Python interface to C++ writers for orthogonal grids.

    Example:
    - `VTIWriter[Grid[1]]` → `VTIWriter_Grid_1`
    - `VTIWriter[Grid[2]]` → `VTIWriter_Grid_2`
    - `VTIWriter[Grid[3]]` → `VTIWriter_Grid_3`
    """


class _VTUWriterMeta(pytnl._meta.CPPClassTemplate):
    _cpp_module = pytnl._meshes
    _class_prefix = "VTUWriter"
    _template_parameters = (("mesh_type", type),)
    _dispatch_same_module_parameter = "mesh_type"

    @overload
    def __getitem__(
        self,
        key: type[pytnl._meshes.Grid_1],
        /,
    ) -> type[pytnl._meshes.VTUWriter_Grid_1]: ...

    @overload
    def __getitem__(
        self,
        key: type[pytnl._meshes.Grid_2],
        /,
    ) -> type[pytnl._meshes.VTUWriter_Grid_2]: ...

    @overload
    def __getitem__(
        self,
        key: type[pytnl._meshes.Grid_3],
        /,
    ) -> type[pytnl._meshes.VTUWriter_Grid_3]: ...

    @overload
    def __getitem__(
        self,
        key: type[pytnl._meshes.Mesh_Edge],
        /,
    ) -> type[pytnl._meshes.VTUWriter_Mesh_Edge]: ...

    @overload
    def __getitem__(
        self,
        key: type[pytnl._meshes.Mesh_Hexahedron],
        /,
    ) -> type[pytnl._meshes.VTUWriter_Mesh_Hexahedron]: ...

    @overload
    def __getitem__(
        self,
        key: type[pytnl._meshes.Mesh_Polygon],
        /,
    ) -> type[pytnl._meshes.VTUWriter_Mesh_Polygon]: ...

    @overload
    def __getitem__(
        self,
        key: type[pytnl._meshes.Mesh_Polyhedron],
        /,
    ) -> type[pytnl._meshes.VTUWriter_Mesh_Polyhedron]: ...

    @overload
    def __getitem__(
        self,
        key: type[pytnl._meshes.Mesh_Quadrangle],
        /,
    ) -> type[pytnl._meshes.VTUWriter_Mesh_Quadrangle]: ...

    @overload
    def __getitem__(
        self,
        key: type[pytnl._meshes.Mesh_Tetrahedron],
        /,
    ) -> type[pytnl._meshes.VTUWriter_Mesh_Tetrahedron]: ...

    @overload
    def __getitem__(
        self,
        key: type[pytnl._meshes.Mesh_Triangle],
        /,
    ) -> type[pytnl._meshes.VTUWriter_Mesh_Triangle]: ...

    @overload
    def __getitem__(  # type: ignore[no-any-unimported, unused-ignore]
        self,
        key: type[_meshes_cuda.Grid_1],  # pyright: ignore
        /,
    ) -> type[_meshes_cuda.VTUWriter_Grid_1]: ...  # pyright: ignore

    @overload
    def __getitem__(  # type: ignore[no-any-unimported, overload-cannot-match, unused-ignore]
        self,
        key: type[_meshes_cuda.Grid_2],  # pyright: ignore
        /,
    ) -> type[_meshes_cuda.VTUWriter_Grid_2]: ...  # pyright: ignore

    @overload
    def __getitem__(  # type: ignore[no-any-unimported, overload-cannot-match, unused-ignore]
        self,
        key: type[_meshes_cuda.Grid_3],  # pyright: ignore
        /,
    ) -> type[_meshes_cuda.VTUWriter_Grid_3]: ...  # pyright: ignore

    def __getitem__(  # type: ignore[no-any-unimported, unused-ignore]
        self,
        key: type[  # pyright: ignore
            pytnl._meshes.Grid_1
            | pytnl._meshes.Grid_2
            | pytnl._meshes.Grid_3
            | pytnl._meshes.Mesh_Edge
            | pytnl._meshes.Mesh_Hexahedron
            | pytnl._meshes.Mesh_Polygon
            | pytnl._meshes.Mesh_Polyhedron
            | pytnl._meshes.Mesh_Quadrangle
            | pytnl._meshes.Mesh_Tetrahedron
            | pytnl._meshes.Mesh_Triangle
            | _meshes_cuda.Grid_1  # pyright: ignore
            | _meshes_cuda.Grid_2  # pyright: ignore
            | _meshes_cuda.Grid_3  # pyright: ignore
        ],
        /,
    ) -> type[Any]:
        items = (key,)  # pyright: ignore
        return self._get_cpp_class(items)  # pyright: ignore


class VTUWriter(metaclass=_VTUWriterMeta):
    """
    Allows `VTUWriter[mesh_type]` syntax to resolve to
    the appropriate C++ `VTUWriter` class.

    This class provides a Python interface to C++ mesh writers.

    Examples:
    - `VTUWriter[Mesh[topologies.Edge]` → `VTUWriter_Mesh_Edge`
    - `VTUWriter[Mesh[topologies.Polygon]` → `VTUWriter_Mesh_Polygon`
    """


class _VTKWriterMeta(pytnl._meta.CPPClassTemplate):
    _cpp_module = pytnl._meshes
    _class_prefix = "VTKWriter"
    _template_parameters = (("mesh_type", type),)
    _dispatch_same_module_parameter = "mesh_type"

    @overload
    def __getitem__(
        self,
        key: type[pytnl._meshes.Grid_1],
        /,
    ) -> type[pytnl._meshes.VTKWriter_Grid_1]: ...

    @overload
    def __getitem__(
        self,
        key: type[pytnl._meshes.Grid_2],
        /,
    ) -> type[pytnl._meshes.VTKWriter_Grid_2]: ...

    @overload
    def __getitem__(
        self,
        key: type[pytnl._meshes.Grid_3],
        /,
    ) -> type[pytnl._meshes.VTKWriter_Grid_3]: ...

    @overload
    def __getitem__(
        self,
        key: type[pytnl._meshes.Mesh_Edge],
        /,
    ) -> type[pytnl._meshes.VTKWriter_Mesh_Edge]: ...

    @overload
    def __getitem__(
        self,
        key: type[pytnl._meshes.Mesh_Hexahedron],
        /,
    ) -> type[pytnl._meshes.VTKWriter_Mesh_Hexahedron]: ...

    @overload
    def __getitem__(
        self,
        key: type[pytnl._meshes.Mesh_Polygon],
        /,
    ) -> type[pytnl._meshes.VTKWriter_Mesh_Polygon]: ...

    @overload
    def __getitem__(
        self,
        key: type[pytnl._meshes.Mesh_Polyhedron],
        /,
    ) -> type[pytnl._meshes.VTKWriter_Mesh_Polyhedron]: ...

    @overload
    def __getitem__(
        self,
        key: type[pytnl._meshes.Mesh_Quadrangle],
        /,
    ) -> type[pytnl._meshes.VTKWriter_Mesh_Quadrangle]: ...

    @overload
    def __getitem__(
        self,
        key: type[pytnl._meshes.Mesh_Tetrahedron],
        /,
    ) -> type[pytnl._meshes.VTKWriter_Mesh_Tetrahedron]: ...

    @overload
    def __getitem__(
        self,
        key: type[pytnl._meshes.Mesh_Triangle],
        /,
    ) -> type[pytnl._meshes.VTKWriter_Mesh_Triangle]: ...

    @overload
    def __getitem__(  # type: ignore[no-any-unimported, unused-ignore]
        self,
        key: type[_meshes_cuda.Grid_1],  # pyright: ignore
        /,
    ) -> type[_meshes_cuda.VTKWriter_Grid_1]: ...  # pyright: ignore

    @overload
    def __getitem__(  # type: ignore[no-any-unimported, overload-cannot-match, unused-ignore]
        self,
        key: type[_meshes_cuda.Grid_2],  # pyright: ignore
        /,
    ) -> type[_meshes_cuda.VTKWriter_Grid_2]: ...  # pyright: ignore

    @overload
    def __getitem__(  # type: ignore[no-any-unimported, overload-cannot-match, unused-ignore]
        self,
        key: type[_meshes_cuda.Grid_3],  # pyright: ignore
        /,
    ) -> type[_meshes_cuda.VTKWriter_Grid_3]: ...  # pyright: ignore

    def __getitem__(  # type: ignore[no-any-unimported, unused-ignore]
        self,
        key: type[  # pyright: ignore
            pytnl._meshes.Grid_1
            | pytnl._meshes.Grid_2
            | pytnl._meshes.Grid_3
            | pytnl._meshes.Mesh_Edge
            | pytnl._meshes.Mesh_Hexahedron
            | pytnl._meshes.Mesh_Polygon
            | pytnl._meshes.Mesh_Polyhedron
            | pytnl._meshes.Mesh_Quadrangle
            | pytnl._meshes.Mesh_Tetrahedron
            | pytnl._meshes.Mesh_Triangle
            | _meshes_cuda.Grid_1  # pyright: ignore
            | _meshes_cuda.Grid_2  # pyright: ignore
            | _meshes_cuda.Grid_3  # pyright: ignore
        ],
        /,
    ) -> type[Any]:
        items = (key,)  # pyright: ignore
        return self._get_cpp_class(items)  # pyright: ignore


class VTKWriter(metaclass=_VTKWriterMeta):
    """
    Allows `VTKWriter[mesh_type]` syntax to resolve to
    the appropriate C++ `VTKWriter` class.

    This class provides a Python interface to C++ mesh writers.

    Examples:
    - `VTKWriter[Mesh[topologies.Edge]]` → `VTKWriter_Mesh_Edge`
    - `VTKWriter[Mesh[topologies.Polygon]]` → `VTKWriter_Mesh_Polygon`
    """


class _PVTUWriterMeta(pytnl._meta.CPPClassTemplate):
    _cpp_module = pytnl._meshes
    _class_prefix = "PVTUWriter"
    _template_parameters = (("mesh_type", type),)
    _dispatch_same_module_parameter = "mesh_type"

    @overload
    def __getitem__(
        self,
        key: type[pytnl._meshes.Mesh_Edge],
        /,
    ) -> type[pytnl._meshes.PVTUWriter_Mesh_Edge]: ...

    @overload
    def __getitem__(
        self,
        key: type[pytnl._meshes.Mesh_Hexahedron],
        /,
    ) -> type[pytnl._meshes.PVTUWriter_Mesh_Hexahedron]: ...

    @overload
    def __getitem__(
        self,
        key: type[pytnl._meshes.Mesh_Quadrangle],
        /,
    ) -> type[pytnl._meshes.PVTUWriter_Mesh_Quadrangle]: ...

    @overload
    def __getitem__(
        self,
        key: type[pytnl._meshes.Mesh_Tetrahedron],
        /,
    ) -> type[pytnl._meshes.PVTUWriter_Mesh_Tetrahedron]: ...

    @overload
    def __getitem__(
        self,
        key: type[pytnl._meshes.Mesh_Triangle],
        /,
    ) -> type[pytnl._meshes.PVTUWriter_Mesh_Triangle]: ...

    def __getitem__(  # type: ignore[no-any-unimported, unused-ignore]
        self,
        key: type[  # pyright: ignore
            pytnl._meshes.Mesh_Edge
            | pytnl._meshes.Mesh_Hexahedron
            | pytnl._meshes.Mesh_Quadrangle
            | pytnl._meshes.Mesh_Tetrahedron
            | pytnl._meshes.Mesh_Triangle
        ],
        /,
    ) -> type[Any]:
        items = (key,)  # pyright: ignore
        return self._get_cpp_class(items)  # pyright: ignore


class PVTUWriter(metaclass=_PVTUWriterMeta):
    """
    Allows `PVTUWriter[mesh_type]` syntax to resolve to
    the appropriate C++ `PVTUWriter` class.

    This class provides a Python interface to C++ writers for distributed meshes.

    Example:
    - `PVTUWriter[Mesh[topologies.Edge]]` → `PVTUWriter_Mesh_Edge`
    - `PVTUWriter[Mesh[topologies.Polygon]]` → `PVTUWriter_Mesh_Polygon`
    """


def resolveMeshType(
    file_name: str,
    *,
    file_format: str = "auto",
    device_type: type[DT] = pytnl.devices.Host,
) -> tuple[MeshReader, type]:
    """
    Returns a `(reader, mesh)` pair where `reader` is initialized with the given
    file name (using `getMeshReader`) and `mesh` is empty.
    """
    if device_type is pytnl.devices.Cuda:
        _meshes_cuda = importlib.import_module("pytnl._meshes_cuda")
        return _meshes_cuda.resolveMeshType(file_name, file_format=file_format)  # type: ignore[no-any-return]
    return pytnl._meshes.resolveMeshType(file_name, file_format=file_format)


def resolveAndLoadMesh(
    file_name: str,
    *,
    file_format: str = "auto",
    device_type: type[DT] = pytnl.devices.Host,
) -> tuple[MeshReader, type]:
    """
    Returns a `(reader, mesh)` pair where `reader` is initialized with the given
    file name (using `getMeshReader`) and `mesh` contains the mesh loaded from
    the given file (using `reader.loadMesh(mesh)`).
    """
    if device_type is pytnl.devices.Cuda:
        _meshes_cuda = importlib.import_module("pytnl._meshes_cuda")
        return _meshes_cuda.resolveAndLoadMesh(file_name, file_format=file_format)  # type: ignore[no-any-return]
    return pytnl._meshes.resolveAndLoadMesh(file_name, file_format=file_format)
