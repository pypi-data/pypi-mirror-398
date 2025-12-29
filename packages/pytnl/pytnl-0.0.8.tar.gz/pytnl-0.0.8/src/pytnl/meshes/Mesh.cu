#include "Mesh.h"

void
export_Meshes( nb::module_& m )
{
   export_Mesh< MeshOfEdges_cuda >( m, "Mesh_Edge" );
   export_Mesh< MeshOfTriangles_cuda >( m, "Mesh_Triangle" );
   export_Mesh< MeshOfQuadrangles_cuda >( m, "Mesh_Quadrangle" );
   export_Mesh< MeshOfTetrahedrons_cuda >( m, "Mesh_Tetrahedron" );
   export_Mesh< MeshOfHexahedrons_cuda >( m, "Mesh_Hexahedron" );
   export_Mesh< MeshOfPolygons_cuda >( m, "Mesh_Polygon" );
   export_Mesh< MeshOfPolyhedrons_cuda >( m, "Mesh_Polyhedron" );
}
