#include "Mesh.h"

void
export_Meshes( nb::module_& m )
{
   export_Mesh< MeshOfEdges_host >( m, "Mesh_Edge" );
   export_Mesh< MeshOfTriangles_host >( m, "Mesh_Triangle" );
   export_Mesh< MeshOfQuadrangles_host >( m, "Mesh_Quadrangle" );
   export_Mesh< MeshOfTetrahedrons_host >( m, "Mesh_Tetrahedron" );
   export_Mesh< MeshOfHexahedrons_host >( m, "Mesh_Hexahedron" );
   export_Mesh< MeshOfPolygons_host >( m, "Mesh_Polygon" );
   export_Mesh< MeshOfPolyhedrons_host >( m, "Mesh_Polyhedron" );
}
