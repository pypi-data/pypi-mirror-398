import pytnl._meshes
from pytnl import devices
from pytnl.meshes import Grid, Mesh, topologies

# Aliases for tested types
type M = (
    pytnl._meshes.Grid_1
    | pytnl._meshes.Grid_2
    | pytnl._meshes.Grid_3
    | pytnl._meshes.Mesh_Edge
    | pytnl._meshes.Mesh_Triangle
    | pytnl._meshes.Mesh_Quadrangle
    | pytnl._meshes.Mesh_Polygon
    | pytnl._meshes.Mesh_Hexahedron
    | pytnl._meshes.Mesh_Tetrahedron
    | pytnl._meshes.Mesh_Polyhedron
)

# List of tested mesh types
mesh_types = M.__value__.__args__


# ----------------------
# Pythonizations and types
# ----------------------


def test_Grid_pythonization() -> None:
    assert Grid[1] is pytnl._meshes.Grid_1
    assert Grid[2] is pytnl._meshes.Grid_2
    assert Grid[3] is pytnl._meshes.Grid_3

    assert Grid[1, devices.Host] is pytnl._meshes.Grid_1
    assert Grid[2, devices.Host] is pytnl._meshes.Grid_2
    assert Grid[3, devices.Host] is pytnl._meshes.Grid_3


def test_Mesh_pythonization() -> None:
    assert Mesh[topologies.Edge] is pytnl._meshes.Mesh_Edge
    assert Mesh[topologies.Hexahedron] is pytnl._meshes.Mesh_Hexahedron
    assert Mesh[topologies.Polygon] is pytnl._meshes.Mesh_Polygon
    assert Mesh[topologies.Polyhedron] is pytnl._meshes.Mesh_Polyhedron
    assert Mesh[topologies.Quadrangle] is pytnl._meshes.Mesh_Quadrangle
    assert Mesh[topologies.Tetrahedron] is pytnl._meshes.Mesh_Tetrahedron
    assert Mesh[topologies.Triangle] is pytnl._meshes.Mesh_Triangle

    assert Mesh[topologies.Edge, devices.Host] is pytnl._meshes.Mesh_Edge
    assert Mesh[topologies.Hexahedron, devices.Host] is pytnl._meshes.Mesh_Hexahedron
    assert Mesh[topologies.Polygon, devices.Host] is pytnl._meshes.Mesh_Polygon
    assert Mesh[topologies.Polyhedron, devices.Host] is pytnl._meshes.Mesh_Polyhedron
    assert Mesh[topologies.Quadrangle, devices.Host] is pytnl._meshes.Mesh_Quadrangle
    assert Mesh[topologies.Tetrahedron, devices.Host] is pytnl._meshes.Mesh_Tetrahedron
    assert Mesh[topologies.Triangle, devices.Host] is pytnl._meshes.Mesh_Triangle


# def test_typedefs() -> None:
#    for mesh_type in mesh_types:
#        assert mesh_type.IndexType is int
#        assert mesh_type.RealType is float
