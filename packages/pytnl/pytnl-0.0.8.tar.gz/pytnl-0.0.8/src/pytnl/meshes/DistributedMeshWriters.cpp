#include "DistributedMeshWriters.h"

template< typename Mesh >
using PVTUWriter = TNL::Meshes::Writers::PVTUWriter< Mesh >;

void
export_DistributedMeshWriters( nb::module_& m )
{
   constexpr TNL::Meshes::VTK::FileFormat default_format = TNL::Meshes::VTK::FileFormat::zlib_compressed;
   export_DistributedMeshWriter< PVTUWriter, MeshOfEdges_host, default_format >( m, "PVTUWriter_Mesh_Edge" );
   export_DistributedMeshWriter< PVTUWriter, MeshOfTriangles_host, default_format >( m, "PVTUWriter_Mesh_Triangle" );
   export_DistributedMeshWriter< PVTUWriter, MeshOfQuadrangles_host, default_format >( m, "PVTUWriter_Mesh_Quadrangle" );
   export_DistributedMeshWriter< PVTUWriter, MeshOfTetrahedrons_host, default_format >( m, "PVTUWriter_Mesh_Tetrahedron" );
   export_DistributedMeshWriter< PVTUWriter, MeshOfHexahedrons_host, default_format >( m, "PVTUWriter_Mesh_Hexahedron" );
}
