# mypy: disable-error-code="import-not-found, no-any-unimported, no-untyped-call, index, unused-ignore"
# pyright: standard
# pyright: reportMissingImports=information

import shutil
import subprocess
from pathlib import Path
from types import ModuleType
from typing import TYPE_CHECKING, Literal

import pytest

import pytnl._meshes
import pytnl.meshes
from pytnl._meta import DIMS
from pytnl.devices import Cuda

mpi4py: ModuleType | None
try:
    import mpi4py
    import mpi4py.MPI
except ImportError:
    mpi4py = None

if TYPE_CHECKING:
    import pytnl._meshes_cuda as _meshes_cuda
else:
    _meshes_cuda = pytest.importorskip("pytnl._meshes_cuda")

# Mark all tests in this module
pytestmark = pytest.mark.cuda

# Aliases for tested types
type Grid = _meshes_cuda.Grid_1 | _meshes_cuda.Grid_2 | _meshes_cuda.Grid_3
type HostMesh = (
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
type Mesh = (
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
type MeshWriter = (
    _meshes_cuda.VTIWriter_Grid_1
    | _meshes_cuda.VTIWriter_Grid_2
    | _meshes_cuda.VTIWriter_Grid_3
    | _meshes_cuda.VTKWriter_Grid_1
    | _meshes_cuda.VTKWriter_Grid_2
    | _meshes_cuda.VTKWriter_Grid_3
    | _meshes_cuda.VTUWriter_Grid_1
    | _meshes_cuda.VTUWriter_Grid_2
    | _meshes_cuda.VTUWriter_Grid_3
    | pytnl._meshes.VTKWriter_Mesh_Edge
    | pytnl._meshes.VTKWriter_Mesh_Triangle
    | pytnl._meshes.VTKWriter_Mesh_Quadrangle
    | pytnl._meshes.VTKWriter_Mesh_Polygon
    | pytnl._meshes.VTKWriter_Mesh_Hexahedron
    | pytnl._meshes.VTKWriter_Mesh_Tetrahedron
    | pytnl._meshes.VTKWriter_Mesh_Polyhedron
    | pytnl._meshes.VTUWriter_Mesh_Edge
    | pytnl._meshes.VTUWriter_Mesh_Triangle
    | pytnl._meshes.VTUWriter_Mesh_Quadrangle
    | pytnl._meshes.VTUWriter_Mesh_Polygon
    | pytnl._meshes.VTUWriter_Mesh_Hexahedron
    | pytnl._meshes.VTUWriter_Mesh_Tetrahedron
    | pytnl._meshes.VTUWriter_Mesh_Polyhedron
)

# Global flags
TNL_DECOMPOSE_CMD = "tnl-decompose-mesh"
TNL_DECOMPOSE_FLAGS = "--ghost-levels 1"

# Mapping from file suffix to reader class
suffix_to_reader = {
    ".vti": pytnl.meshes.VTIReader,
    ".vtk": pytnl.meshes.VTKReader,
    ".vtu": pytnl.meshes.VTUReader,
}

# Mapping from topology directory to mesh topology class
topologies_map = {
    "triangles": pytnl.meshes.topologies.Triangle,
    "triangles_2x2x2": pytnl.meshes.topologies.Triangle,
    "tetrahedrons": pytnl.meshes.topologies.Tetrahedron,
    "quadrangles": pytnl.meshes.topologies.Quadrangle,
    "hexahedrons": pytnl.meshes.topologies.Hexahedron,
    "polygons": pytnl.meshes.topologies.Polygon,
    "polyhedrons": pytnl.meshes.topologies.Polyhedron,
}

# Define test cases with expected vertex and cell counts
test_cases = [
    # grids
    ("quadrangles/grid_2x3.vti", 12, 6),
    ("hexahedrons/grid_2x3x4.vti", 60, 24),
    # triangles
    ("triangles/mrizka_1.vtk", 142, 242),
    ("triangles/mrizka_1.vtu", 142, 242),
    # tetrahedrons
    ("tetrahedrons/cube1m_1.vtk", 395, 1312),
    ("tetrahedrons/cube1m_1.vtu", 395, 1312),
    # triangles_2x2x2
    ("triangles_2x2x2/original_with_metadata_and_cell_data.vtk", 9, 8),
    ("triangles_2x2x2/minimized_ascii.vtk", 9, 8),
    ("triangles_2x2x2/minimized_binary.vtk", 9, 8),
    ("triangles_2x2x2/version_5.1_ascii.vtk", 9, 8),
    ("triangles_2x2x2/version_5.1_binary.vtk", 9, 8),
    # quadrangles
    ("quadrangles/grid_2x3.vtk", 12, 6),
    ("quadrangles/grid_2x3.vtu", 12, 6),
    # hexahedrons
    ("hexahedrons/grid_2x3x4.vtk", 60, 24),
    ("hexahedrons/grid_2x3x4.vtu", 60, 24),
    # polygons
    ("polygons/unicorn.vtk", 193, 90),
    ("polygons/unicorn.vtu", 193, 90),
    # polyhedrons
    ("polyhedrons/two_polyhedra.vtk", 22, 2),
    ("polyhedrons/two_polyhedra.vtu", 22, 2),
    ("polyhedrons/cube1m_1.vtk", 2018, 395),
    ("polyhedrons/cube1m_1.vtu", 2018, 395),
]


# Generic function for testing mesh readers and writers
def _test_reader_writer(
    reader_class: type[pytnl.meshes.MeshReader],
    writer_class: type[MeshWriter],
    mesh: Mesh,
    tmp_path: Path,
    host_mesh: HostMesh | Mesh | None = None,
) -> None:
    """
    Test that writing a mesh to a file with the given writer and reading it back
    with the given reader preserves the mesh structure.

    Parameters:
    - reader_class: The reader class (e.g., tnl.VTKReader)
    - writer_class: The writer class (e.g., tnl.VTKWriter_MeshOfTriangles)
    - mesh: A populated mesh instance to test
    - tmp_path: Pytest fixture for temporary directory
    """
    output_file = tmp_path / "test_mesh"

    # Write the mesh to a temporary file
    with open(output_file, "wb") as file:
        writer = writer_class(file)
        writer.writeMetadata(cycle=0, time=1.0)
        if host_mesh is None:
            writer.writeCells(mesh)  # type: ignore[arg-type]
        else:
            writer.writeCells(host_mesh)  # type: ignore[arg-type]
        del writer  # Force flush

    # Check that the writer produced output
    output = output_file.read_bytes()
    if "VTKWriter" in writer_class.__name__:
        assert output.startswith(b"# vtk DataFile Version 5.1\n")
        assert output.count(b"# vtk DataFile Version 5.1\n") == 1
    else:
        assert output.startswith(b'<?xml version="1.0"?>\n<VTKFile type="')
        assert output.rstrip().endswith(b"</VTKFile>")

    # Read the mesh back from the file
    mesh_out = type(mesh)()
    reader = reader_class(str(output_file))
    reader.loadMesh(mesh_out)

    assert mesh_out == mesh


# Generic function for testing mesh readers and writers with data arrays
def _test_meshfunction(
    reader_class: type[pytnl.meshes.MeshReader],
    writer_class: type[MeshWriter],
    mesh: Mesh,
    tmp_path: Path,
    data_type: Literal["PointData", "CellData"] = "PointData",
    host_mesh: HostMesh | Mesh | None = None,
) -> None:
    """
    Tests writing and reading point/cell data arrays with the mesh.
    """
    if data_type == "PointData":
        n_points = mesh.getEntitiesCount(mesh.Vertex)  # type: ignore[arg-type]
        assert isinstance(n_points, int)
        scalar_data = list(range(n_points))
        vector_data = list(range(3 * n_points))
    else:
        n_cells = mesh.getEntitiesCount(mesh.Cell)  # type: ignore[arg-type]
        assert isinstance(n_cells, int)
        scalar_data = list(range(n_cells))
        vector_data = list(range(3 * n_cells))

    output_file = tmp_path / "test_mesh"

    # Write mesh and data arrays
    with open(output_file, "wb") as file:
        writer = writer_class(file)
        writer.writeMetadata(cycle=42, time=3.14)
        if host_mesh is None:
            writer.writeCells(mesh)  # type: ignore[arg-type]
        else:
            writer.writeCells(host_mesh)  # type: ignore[arg-type]
        if data_type == "PointData":
            writer.writePointData(scalar_data, "foo", 1)
            writer.writePointData(vector_data, "bar", 3)
        else:
            writer.writeCellData(scalar_data, "foo", 1)
            writer.writeCellData(vector_data, "bar", 3)
        del writer  # Force flush

    # Read mesh and data arrays
    mesh_out = type(mesh)()
    reader = reader_class(str(output_file))
    reader.loadMesh(mesh_out)

    if data_type == "PointData":
        scalar_data_in = reader.readPointData("foo")
        vector_data_in = reader.readPointData("bar")
    else:
        scalar_data_in = reader.readCellData("foo")
        vector_data_in = reader.readCellData("bar")

    assert scalar_data_in == scalar_data, f"{data_type} scalar data mismatch"
    assert vector_data_in == vector_data, f"{data_type} vector data mismatch"


# Parametrized synthetic grid test cases
@pytest.mark.parametrize(
    "dim, origin, proportions, dimensions",
    [
        (1, [1], [2], [10]),
        (2, [1, 2], [3, 4], [10, 20]),
        (3, [1, 2, 3], [4, 5, 6], [10, 20, 30]),
    ],
)
def test_vti_reader_synthetic(dim: DIMS, origin: list[int], proportions: list[int], dimensions: list[int], tmp_path: Path) -> None:
    # Choose appropriate grid, reader and writer based on dimension
    grid_class = pytnl.meshes.Grid[dim, Cuda]  # type: ignore[type-arg, valid-type]
    reader_class = pytnl.meshes.VTIReader
    writer_class: type[MeshWriter] = pytnl.meshes.VTIWriter[grid_class]  # pyright: ignore[reportUnknownVariableType]

    # Create synthetic grid
    grid = grid_class()
    grid.setDomain(grid_class.PointType(origin), grid_class.PointType(proportions))
    grid.setDimensions(grid_class.CoordinatesType(dimensions))

    # Round-trip tests
    _test_reader_writer(reader_class, writer_class, grid, tmp_path)
    _test_meshfunction(reader_class, writer_class, grid, tmp_path, "PointData")
    _test_meshfunction(reader_class, writer_class, grid, tmp_path, "CellData")


# Parametrize test cases with file path, expected vertices, expected cells
@pytest.mark.parametrize("file_path, expected_vertices, expected_cells", test_cases)
def test_mesh_file(file_path: str, expected_vertices: int, expected_cells: int, tmp_path: Path) -> None:
    data_dir = Path(__file__).parent / "data"
    full_path = (data_dir / file_path).resolve()
    suffix = full_path.suffix
    directory = full_path.parent.name

    # Get reader class based on suffix
    try:
        reader_class = suffix_to_reader[suffix]
    except KeyError:
        pytest.fail(f"Unsupported file suffix: {suffix}")

    if suffix == ".vti":
        # Choose appropriate grid class and writer class based on dimension
        dim: Literal[2, 3] = 2 if "quadrangles" in file_path else 3
        mesh_class: type[Mesh] = pytnl.meshes.Grid[dim, Cuda]  # type: ignore[assignment]
        host_mesh_class: type[HostMesh | Mesh] = mesh_class
        writer_class: type[MeshWriter] = pytnl.meshes.VTIWriter[mesh_class]  # type: ignore[assignment]
    else:
        # Get mesh topology based on directory
        try:
            topology = topologies_map[directory]
        except KeyError:
            pytest.fail(f"Unsupported directory: {directory}")

        mesh_class = pytnl.meshes.Mesh[topology, Cuda]  # type: ignore[assignment]
        host_mesh_class = pytnl.meshes.Mesh[topology]

        # Choose writer based on reader
        if reader_class == pytnl.meshes.VTKReader:
            writer_class = pytnl.meshes.VTKWriter[host_mesh_class]  # pyright: ignore
        else:
            writer_class = pytnl.meshes.VTUWriter[host_mesh_class]  # pyright: ignore

    # Load mesh
    mesh = mesh_class()
    host_mesh = host_mesh_class()
    reader = reader_class(str(full_path))
    reader.loadMesh(mesh)
    reader = reader_class(str(full_path))
    reader.loadMesh(host_mesh)

    # Check mesh entities
    assert mesh.getEntitiesCount(mesh.Vertex) == expected_vertices, f"Expected {expected_vertices} points in {file_path}"  # type: ignore[arg-type]
    assert mesh.getEntitiesCount(mesh.Cell) == expected_cells, f"Expected {expected_cells} cells in {file_path}"  # type: ignore[arg-type]

    # Round-trip tests
    _test_reader_writer(reader_class, writer_class, mesh, tmp_path, host_mesh=host_mesh)
    _test_meshfunction(reader_class, writer_class, mesh, tmp_path, "PointData", host_mesh=host_mesh)
    _test_meshfunction(reader_class, writer_class, mesh, tmp_path, "CellData", host_mesh=host_mesh)


# This test actually tests three functions:
# 1. getMeshReader - returns the MeshReader instance based on file extension
#       (does not call `reader.detectMesh` so it succeeds even for invalid file)
# 2. resolveMeshType - returns a `(reader, mesh)` pair where `reader` is initialized
#       with the given file name (using `getMeshReader`) and `mesh` is empty
# 3. resolveAndLoadMesh - same plus loads the mesh using `reader.loadMesh`
@pytest.mark.parametrize("file_path, expected_vertices, expected_cells", test_cases)
def test_resolveMeshType(file_path: str, expected_vertices: int, expected_cells: int) -> None:
    data_dir = Path(__file__).parent / "data"
    full_path = (data_dir / file_path).resolve()
    suffix = full_path.suffix
    directory = full_path.parent.name

    # Get reader class based on suffix
    try:
        reader_class = suffix_to_reader[suffix]
    except KeyError:
        pytest.fail(f"Unsupported file suffix: {suffix}")

    if suffix == ".vti":
        # Choose appropriate grid class based on dimension
        dim: Literal[2, 3] = 2 if "quadrangles" in file_path else 3
        mesh_class: type[Mesh] = pytnl.meshes.Grid[dim, Cuda]  # type: ignore[assignment]
    else:
        # Get mesh topology based on directory
        try:
            topology = topologies_map[directory]
        except KeyError:
            pytest.fail(f"Unsupported directory: {directory}")

        mesh_class = pytnl.meshes.Mesh[topology, Cuda]  # type: ignore[assignment]

    # Test getMeshReader
    reader = pytnl.meshes.getMeshReader(f"invalid{suffix}")
    assert isinstance(reader, reader_class), reader
    reader = pytnl.meshes.getMeshReader(str(full_path))
    assert isinstance(reader, reader_class), reader

    # Test resolveMeshType
    with pytest.raises(RuntimeError):
        pytnl.meshes.resolveMeshType(f"invalid{suffix}")
    reader, mesh = pytnl.meshes.resolveMeshType(str(full_path), device_type=Cuda)
    assert isinstance(reader, reader_class), reader
    assert isinstance(mesh, mesh_class), mesh
    # Check mesh entities
    assert mesh.getEntitiesCount(mesh.Vertex) == 0  # type: ignore[attr-defined]
    assert mesh.getEntitiesCount(mesh.Cell) == 0  # type: ignore[attr-defined]

    # Test resolveAndLoadMesh
    with pytest.raises(RuntimeError):
        pytnl.meshes.resolveAndLoadMesh(f"invalid{suffix}")
    reader, mesh = pytnl.meshes.resolveAndLoadMesh(str(full_path), device_type=Cuda)
    assert isinstance(reader, reader_class), reader
    assert isinstance(mesh, mesh_class), mesh
    # Check mesh entities
    assert mesh.getEntitiesCount(mesh.Vertex) == expected_vertices, f"Expected {expected_vertices} points in {file_path}"  # type: ignore[attr-defined]
    assert mesh.getEntitiesCount(mesh.Cell) == expected_cells, f"Expected {expected_cells} cells in {file_path}"  # type: ignore[attr-defined]


# Test for PVTUReader and PVTUWriter (requires MPI)
@pytest.mark.mpi
@pytest.mark.skipif(not shutil.which("tnl-decompose-mesh"), reason="tnl-decompose-mesh is not available")
@pytest.mark.skipif(mpi4py is None or mpi4py.MPI.COMM_WORLD.Get_size() < 2, reason="Needs at least 2 MPI processes")
@pytest.mark.parametrize("file_path, expected_vertices, expected_cells", test_cases)
def test_pvtu_reader_writer(file_path: str, expected_vertices: int, expected_cells: int, tmp_path: Path) -> None:
    data_dir = Path(__file__).parent / "data"
    full_path = (data_dir / file_path).resolve()

    # Skip grids
    if full_path.suffix == ".vti":
        pytest.skip("not an unstructured mesh")

    # Skip small meshes
    if expected_cells < 20:
        pytest.skip("not enough cells to decompose")

    assert mpi4py is not None
    comm = mpi4py.MPI.COMM_WORLD
    nproc = comm.Get_size()
    # rank = comm.Get_rank()

    # Decompose mesh first
    output_pvtu = tmp_path / "test.pvtu"
    cmd = f"{TNL_DECOMPOSE_CMD} --input-file {full_path} --output-file {output_pvtu} --subdomains {nproc} {TNL_DECOMPOSE_FLAGS}"
    subprocess.run(cmd, shell=True, check=True)

    # Load mesh and read data
    mesh_class = pytnl.meshes.Mesh[pytnl.meshes.topologies.Triangle, Cuda]  # type: ignore[type-arg]
    mesh = pytnl.meshes.DistributedMesh[mesh_class]()
    # local_mesh = mesh.getLocalMesh()
    reader = pytnl.meshes.PVTUReader(str(output_pvtu))
    reader.loadMesh(mesh)
    # NOTE: distributeFaces is host-only
    # pytnl.meshes.distributeFaces(mesh)
    indices = reader.readCellData("GlobalIndex")

    assert len(indices) > 0
    assert min(indices) >= 0
    assert max(indices) > 0

    # NOTE: writer is host-only
