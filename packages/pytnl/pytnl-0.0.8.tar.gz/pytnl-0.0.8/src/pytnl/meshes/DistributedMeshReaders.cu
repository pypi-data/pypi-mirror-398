#include <pytnl/pytnl.h>

#include <TNL/Meshes/Readers/PVTUReader.h>

void
export_DistributedMeshReaders( nb::module_& m )
{
   using PVTUReader = TNL::Meshes::Readers::PVTUReader;

   // bindings for the MeshReader::loadMesh method are in the module itself
   // to make it easily extensible by overloading
   m.def( "loadMesh", &PVTUReader::template loadMesh< DistributedMeshOfEdges_cuda > );
   m.def( "loadMesh", &PVTUReader::template loadMesh< DistributedMeshOfTriangles_cuda > );
   m.def( "loadMesh", &PVTUReader::template loadMesh< DistributedMeshOfQuadrangles_cuda > );
   m.def( "loadMesh", &PVTUReader::template loadMesh< DistributedMeshOfTetrahedrons_cuda > );
   m.def( "loadMesh", &PVTUReader::template loadMesh< DistributedMeshOfHexahedrons_cuda > );
}
