#pragma once

#include <TNL/Meshes/DefaultConfig.h>
#include <TNL/Meshes/DistributedMeshes/DistributedMesh.h>
#include <TNL/Meshes/Grid.h>
#include <TNL/Meshes/Mesh.h>
#include <TNL/Meshes/Topologies/Edge.h>
#include <TNL/Meshes/Topologies/Hexahedron.h>
#include <TNL/Meshes/Topologies/Polygon.h>
#include <TNL/Meshes/Topologies/Polyhedron.h>
#include <TNL/Meshes/Topologies/Quadrangle.h>
#include <TNL/Meshes/Topologies/Tetrahedron.h>
#include <TNL/Meshes/Topologies/Triangle.h>
#include <TNL/Meshes/TypeResolver/BuildConfigTags.h>

using RealType = double;
using IndexType = std::int64_t;
using ComplexType = std::complex< RealType >;

using Grid_1_host = TNL::Meshes::Grid< 1, RealType, TNL::Devices::Host, IndexType >;
using Grid_2_host = TNL::Meshes::Grid< 2, RealType, TNL::Devices::Host, IndexType >;
using Grid_3_host = TNL::Meshes::Grid< 3, RealType, TNL::Devices::Host, IndexType >;
using Grid_1_cuda = TNL::Meshes::Grid< 1, RealType, TNL::Devices::Cuda, IndexType >;
using Grid_2_cuda = TNL::Meshes::Grid< 2, RealType, TNL::Devices::Cuda, IndexType >;
using Grid_3_cuda = TNL::Meshes::Grid< 3, RealType, TNL::Devices::Cuda, IndexType >;

using LocalIndexType = short int;
template< typename Topology, typename Device = TNL::Devices::Host >
using DefaultMeshTemplate =
   TNL::Meshes::Mesh< TNL::Meshes::DefaultConfig< Topology, Topology::dimension, RealType, IndexType, LocalIndexType >,
                      Device >;

using MeshOfEdges_host = DefaultMeshTemplate< TNL::Meshes::Topologies::Edge >;
using MeshOfTriangles_host = DefaultMeshTemplate< TNL::Meshes::Topologies::Triangle >;
using MeshOfQuadrangles_host = DefaultMeshTemplate< TNL::Meshes::Topologies::Quadrangle >;
using MeshOfTetrahedrons_host = DefaultMeshTemplate< TNL::Meshes::Topologies::Tetrahedron >;
using MeshOfHexahedrons_host = DefaultMeshTemplate< TNL::Meshes::Topologies::Hexahedron >;
using MeshOfPolygons_host = DefaultMeshTemplate< TNL::Meshes::Topologies::Polygon >;
using MeshOfPolyhedrons_host = DefaultMeshTemplate< TNL::Meshes::Topologies::Polyhedron >;

using MeshOfEdges_cuda = DefaultMeshTemplate< TNL::Meshes::Topologies::Edge, TNL::Devices::Cuda >;
using MeshOfTriangles_cuda = DefaultMeshTemplate< TNL::Meshes::Topologies::Triangle, TNL::Devices::Cuda >;
using MeshOfQuadrangles_cuda = DefaultMeshTemplate< TNL::Meshes::Topologies::Quadrangle, TNL::Devices::Cuda >;
using MeshOfTetrahedrons_cuda = DefaultMeshTemplate< TNL::Meshes::Topologies::Tetrahedron, TNL::Devices::Cuda >;
using MeshOfHexahedrons_cuda = DefaultMeshTemplate< TNL::Meshes::Topologies::Hexahedron, TNL::Devices::Cuda >;
using MeshOfPolygons_cuda = DefaultMeshTemplate< TNL::Meshes::Topologies::Polygon, TNL::Devices::Cuda >;
using MeshOfPolyhedrons_cuda = DefaultMeshTemplate< TNL::Meshes::Topologies::Polyhedron, TNL::Devices::Cuda >;

using DistributedMeshOfEdges_host = TNL::Meshes::DistributedMeshes::DistributedMesh< MeshOfEdges_host >;
using DistributedMeshOfTriangles_host = TNL::Meshes::DistributedMeshes::DistributedMesh< MeshOfTriangles_host >;
using DistributedMeshOfQuadrangles_host = TNL::Meshes::DistributedMeshes::DistributedMesh< MeshOfQuadrangles_host >;
using DistributedMeshOfTetrahedrons_host = TNL::Meshes::DistributedMeshes::DistributedMesh< MeshOfTetrahedrons_host >;
using DistributedMeshOfHexahedrons_host = TNL::Meshes::DistributedMeshes::DistributedMesh< MeshOfHexahedrons_host >;

using DistributedMeshOfEdges_cuda = TNL::Meshes::DistributedMeshes::DistributedMesh< MeshOfEdges_cuda >;
using DistributedMeshOfTriangles_cuda = TNL::Meshes::DistributedMeshes::DistributedMesh< MeshOfTriangles_cuda >;
using DistributedMeshOfQuadrangles_cuda = TNL::Meshes::DistributedMeshes::DistributedMesh< MeshOfQuadrangles_cuda >;
using DistributedMeshOfTetrahedrons_cuda = TNL::Meshes::DistributedMeshes::DistributedMesh< MeshOfTetrahedrons_cuda >;
using DistributedMeshOfHexahedrons_cuda = TNL::Meshes::DistributedMeshes::DistributedMesh< MeshOfHexahedrons_cuda >;

// Config tag for GridTypeResolver and MeshTypeResolver
struct PyTNLConfigTag
{};

namespace TNL::Meshes::BuildConfigTags {

// Note: cannot replace int with generic Index due to ambiguity :-(
template<>
struct GridRealTag< PyTNLConfigTag, float >
{
   static constexpr bool enabled = false;
};
template<>
struct GridRealTag< PyTNLConfigTag, RealType >
{
   static constexpr bool enabled = true;
};

// Note: cannot replace int with generic Index due to ambiguity :-(
template<>
struct GridIndexTag< PyTNLConfigTag, int >
{
   static constexpr bool enabled = false;
};
template<>
struct GridIndexTag< PyTNLConfigTag, IndexType >
{
   static constexpr bool enabled = true;
};

// Unstructured mesh topologies
template<>
struct MeshCellTopologyTag< PyTNLConfigTag, Topologies::Edge >
{
   static constexpr bool enabled = true;
};
template<>
struct MeshCellTopologyTag< PyTNLConfigTag, Topologies::Triangle >
{
   static constexpr bool enabled = true;
};
template<>
struct MeshCellTopologyTag< PyTNLConfigTag, Topologies::Quadrangle >
{
   static constexpr bool enabled = true;
};
template<>
struct MeshCellTopologyTag< PyTNLConfigTag, Topologies::Polygon >
{
   static constexpr bool enabled = true;
};
template<>
struct MeshCellTopologyTag< PyTNLConfigTag, Topologies::Tetrahedron >
{
   static constexpr bool enabled = true;
};
template<>
struct MeshCellTopologyTag< PyTNLConfigTag, Topologies::Hexahedron >
{
   static constexpr bool enabled = true;
};
template<>
struct MeshCellTopologyTag< PyTNLConfigTag, Topologies::Polyhedron >
{
   static constexpr bool enabled = true;
};

// Meshes are enabled only for the world dimension equal to the cell dimension.
template< typename CellTopology, int WorldDimension >
struct MeshSpaceDimensionTag< PyTNLConfigTag, CellTopology, WorldDimension >
{
   static constexpr bool enabled = WorldDimension == CellTopology::dimension;
};

// Meshes are enabled only for types explicitly listed below.
template<>
struct MeshRealTag< PyTNLConfigTag, RealType >
{
   static constexpr bool enabled = true;
};
template<>
struct MeshGlobalIndexTag< PyTNLConfigTag, IndexType >
{
   static constexpr bool enabled = true;
};
template<>
struct MeshLocalIndexTag< PyTNLConfigTag, LocalIndexType >
{
   static constexpr bool enabled = true;
};

}  // namespace TNL::Meshes::BuildConfigTags
