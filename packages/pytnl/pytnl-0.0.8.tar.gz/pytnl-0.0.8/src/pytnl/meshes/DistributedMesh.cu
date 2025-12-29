#include "DistributedMesh.h"

void
export_DistributedMeshes( nb::module_& m )
{
   export_DistributedMesh< DistributedMeshOfEdges_cuda >( m, "DistributedMesh_Edge" );
   export_DistributedMesh< DistributedMeshOfTriangles_cuda >( m, "DistributedMesh_Triangle" );
   export_DistributedMesh< DistributedMeshOfQuadrangles_cuda >( m, "DistributedMesh_Quadrangle" );
   export_DistributedMesh< DistributedMeshOfTetrahedrons_cuda >( m, "DistributedMesh_Tetrahedron" );
   export_DistributedMesh< DistributedMeshOfHexahedrons_cuda >( m, "DistributedMesh_Hexahedron" );
}
