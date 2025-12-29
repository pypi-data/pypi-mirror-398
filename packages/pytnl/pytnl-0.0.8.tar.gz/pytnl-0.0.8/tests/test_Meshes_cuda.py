# mypy: disable-error-code="import-not-found, no-any-unimported, no-untyped-call, unused-ignore"
# pyright: standard
# pyright: reportMissingImports=information

from typing import TYPE_CHECKING

import pytest

from pytnl import devices
from pytnl.meshes import Grid, Mesh, topologies

if TYPE_CHECKING:
    import pytnl._meshes_cuda as _meshes_cuda
else:
    _meshes_cuda = pytest.importorskip("pytnl._meshes_cuda")

# Mark all tests in this module
pytestmark = pytest.mark.cuda

# Aliases for tested types
type M = (
    _meshes_cuda.Grid_1
    | _meshes_cuda.Grid_2
    | _meshes_cuda.Grid_3
    | _meshes_cuda.Mesh_Edge
    | _meshes_cuda.Mesh_Triangle
    | _meshes_cuda.Mesh_Quadrangle
    | _meshes_cuda.Mesh_Polygon
    | _meshes_cuda.Mesh_Hexahedron
    | _meshes_cuda.Mesh_Tetrahedron
    | _meshes_cuda.Mesh_Polyhedron
)

# List of tested mesh types
mesh_types = M.__value__.__args__


# ----------------------
# Pythonizations and types
# ----------------------


def test_Grid_pythonization() -> None:
    assert Grid[1, devices.Cuda] is _meshes_cuda.Grid_1
    assert Grid[2, devices.Cuda] is _meshes_cuda.Grid_2
    assert Grid[3, devices.Cuda] is _meshes_cuda.Grid_3


def test_Mesh_pythonization() -> None:
    assert Mesh[topologies.Edge, devices.Cuda] is _meshes_cuda.Mesh_Edge
    assert Mesh[topologies.Hexahedron, devices.Cuda] is _meshes_cuda.Mesh_Hexahedron
    assert Mesh[topologies.Polygon, devices.Cuda] is _meshes_cuda.Mesh_Polygon
    assert Mesh[topologies.Polyhedron, devices.Cuda] is _meshes_cuda.Mesh_Polyhedron
    assert Mesh[topologies.Quadrangle, devices.Cuda] is _meshes_cuda.Mesh_Quadrangle
    assert Mesh[topologies.Tetrahedron, devices.Cuda] is _meshes_cuda.Mesh_Tetrahedron
    assert Mesh[topologies.Triangle, devices.Cuda] is _meshes_cuda.Mesh_Triangle


# def test_typedefs() -> None:
#    for mesh_type in mesh_types:
#        assert mesh_type.IndexType is int
#        assert mesh_type.RealType is float
