import pytnl.containers
import pytnl.meshes


def test_typedefs() -> None:
    assert pytnl.meshes.Grid[1].CoordinatesType is pytnl.containers.StaticVector[1, int]
    assert pytnl.meshes.Grid[2].CoordinatesType is pytnl.containers.StaticVector[2, int]
    assert pytnl.meshes.Grid[3].CoordinatesType is pytnl.containers.StaticVector[3, int]

    assert pytnl.meshes.Grid[1].PointType is pytnl.containers.StaticVector[1, float]
    assert pytnl.meshes.Grid[2].PointType is pytnl.containers.StaticVector[2, float]
    assert pytnl.meshes.Grid[3].PointType is pytnl.containers.StaticVector[3, float]
