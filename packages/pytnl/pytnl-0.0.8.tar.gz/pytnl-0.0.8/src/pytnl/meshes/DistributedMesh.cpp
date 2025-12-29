#include <pytnl/pytnl.h>
#include <pytnl/containers/Array.h>

#include "DistributedMesh.h"

void
export_DistributedMeshes( nb::module_& m )
{
   export_DistributedMesh< DistributedMeshOfEdges_host >( m, "DistributedMesh_Edge" );
   export_DistributedMesh< DistributedMeshOfTriangles_host >( m, "DistributedMesh_Triangle" );
   export_DistributedMesh< DistributedMeshOfQuadrangles_host >( m, "DistributedMesh_Quadrangle" );
   export_DistributedMesh< DistributedMeshOfTetrahedrons_host >( m, "DistributedMesh_Tetrahedron" );
   export_DistributedMesh< DistributedMeshOfHexahedrons_host >( m, "DistributedMesh_Hexahedron" );

   // export VTKTypesArrayType
   using VTKTypesArrayType = typename DistributedMeshOfEdges_host::VTKTypesArrayType;
   export_Array< VTKTypesArrayType >( m, "VTKTypesArrayType" );
}
