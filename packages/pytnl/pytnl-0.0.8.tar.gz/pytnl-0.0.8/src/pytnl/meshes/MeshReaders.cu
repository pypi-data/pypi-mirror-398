#include <pytnl/pytnl.h>
#include <pytnl/meshes/MeshReaders.h>

void
export_MeshReaders( nb::module_& m )
{
   using MeshReader = TNL::Meshes::Readers::MeshReader;

   // bindings for the MeshReader::loadMesh method are in the module itself
   // to make it easily extensible by overloading
   m.def( "loadMesh", &MeshReader::template loadMesh< Grid_1_cuda > );
   m.def( "loadMesh", &MeshReader::template loadMesh< Grid_2_cuda > );
   m.def( "loadMesh", &MeshReader::template loadMesh< Grid_3_cuda > );
   m.def( "loadMesh", &MeshReader::template loadMesh< MeshOfEdges_cuda > );
   m.def( "loadMesh", &MeshReader::template loadMesh< MeshOfTriangles_cuda > );
   m.def( "loadMesh", &MeshReader::template loadMesh< MeshOfQuadrangles_cuda > );
   m.def( "loadMesh", &MeshReader::template loadMesh< MeshOfTetrahedrons_cuda > );
   m.def( "loadMesh", &MeshReader::template loadMesh< MeshOfHexahedrons_cuda > );
   m.def( "loadMesh", &MeshReader::template loadMesh< MeshOfPolygons_cuda > );
   m.def( "loadMesh", &MeshReader::template loadMesh< MeshOfPolyhedrons_cuda > );
}
