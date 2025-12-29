#include "MeshWriters.h"

void
export_MeshWriters( nb::module_& m )
{
   using namespace TNL::Meshes::Writers;
   using FileFormat = TNL::Meshes::VTK::FileFormat;

   export_MeshWriter< VTKWriter< Grid_1_host >, FileFormat::binary >( m, "VTKWriter_Grid_1" );
   export_MeshWriter< VTUWriter< Grid_1_host >, FileFormat::zlib_compressed >( m, "VTUWriter_Grid_1" );
   export_MeshWriter< VTIWriter< Grid_1_host >, FileFormat::zlib_compressed >( m, "VTIWriter_Grid_1" );
   export_MeshWriter< VTKWriter< Grid_2_host >, FileFormat::binary >( m, "VTKWriter_Grid_2" );
   export_MeshWriter< VTUWriter< Grid_2_host >, FileFormat::zlib_compressed >( m, "VTUWriter_Grid_2" );
   export_MeshWriter< VTIWriter< Grid_2_host >, FileFormat::zlib_compressed >( m, "VTIWriter_Grid_2" );
   export_MeshWriter< VTKWriter< Grid_3_host >, FileFormat::binary >( m, "VTKWriter_Grid_3" );
   export_MeshWriter< VTUWriter< Grid_3_host >, FileFormat::zlib_compressed >( m, "VTUWriter_Grid_3" );
   export_MeshWriter< VTIWriter< Grid_3_host >, FileFormat::zlib_compressed >( m, "VTIWriter_Grid_3" );

   export_MeshWriter< VTKWriter< MeshOfEdges_host >, FileFormat::binary >( m, "VTKWriter_Mesh_Edge" );
   export_MeshWriter< VTUWriter< MeshOfEdges_host >, FileFormat::zlib_compressed >( m, "VTUWriter_Mesh_Edge" );
   export_MeshWriter< VTKWriter< MeshOfTriangles_host >, FileFormat::binary >( m, "VTKWriter_Mesh_Triangle" );
   export_MeshWriter< VTUWriter< MeshOfTriangles_host >, FileFormat::zlib_compressed >( m, "VTUWriter_Mesh_Triangle" );
   export_MeshWriter< VTKWriter< MeshOfQuadrangles_host >, FileFormat::binary >( m, "VTKWriter_Mesh_Quadrangle" );
   export_MeshWriter< VTUWriter< MeshOfQuadrangles_host >, FileFormat::zlib_compressed >( m, "VTUWriter_Mesh_Quadrangle" );
   export_MeshWriter< VTKWriter< MeshOfTetrahedrons_host >, FileFormat::binary >( m, "VTKWriter_Mesh_Tetrahedron" );
   export_MeshWriter< VTUWriter< MeshOfTetrahedrons_host >, FileFormat::zlib_compressed >( m, "VTUWriter_Mesh_Tetrahedron" );
   export_MeshWriter< VTKWriter< MeshOfHexahedrons_host >, FileFormat::binary >( m, "VTKWriter_Mesh_Hexahedron" );
   export_MeshWriter< VTUWriter< MeshOfHexahedrons_host >, FileFormat::zlib_compressed >( m, "VTUWriter_Mesh_Hexahedron" );
   export_MeshWriter< VTKWriter< MeshOfPolygons_host >, FileFormat::binary >( m, "VTKWriter_Mesh_Polygon" );
   export_MeshWriter< VTUWriter< MeshOfPolygons_host >, FileFormat::zlib_compressed >( m, "VTUWriter_Mesh_Polygon" );
   export_MeshWriter< VTKWriter< MeshOfPolyhedrons_host >, FileFormat::binary >( m, "VTKWriter_Mesh_Polyhedron" );
   export_MeshWriter< VTUWriter< MeshOfPolyhedrons_host >, FileFormat::zlib_compressed >( m, "VTUWriter_Mesh_Polyhedron" );
}
