#include "MeshWriters.h"

void
export_MeshWriters( nb::module_& m )
{
   using namespace TNL::Meshes::Writers;
   using FileFormat = TNL::Meshes::VTK::FileFormat;

   export_MeshWriter< VTKWriter< Grid_1_cuda >, FileFormat::binary >( m, "VTKWriter_Grid_1" );
   export_MeshWriter< VTUWriter< Grid_1_cuda >, FileFormat::zlib_compressed >( m, "VTUWriter_Grid_1" );
   export_MeshWriter< VTIWriter< Grid_1_cuda >, FileFormat::zlib_compressed >( m, "VTIWriter_Grid_1" );
   export_MeshWriter< VTKWriter< Grid_2_cuda >, FileFormat::binary >( m, "VTKWriter_Grid_2" );
   export_MeshWriter< VTUWriter< Grid_2_cuda >, FileFormat::zlib_compressed >( m, "VTUWriter_Grid_2" );
   export_MeshWriter< VTIWriter< Grid_2_cuda >, FileFormat::zlib_compressed >( m, "VTIWriter_Grid_2" );
   export_MeshWriter< VTKWriter< Grid_3_cuda >, FileFormat::binary >( m, "VTKWriter_Grid_3" );
   export_MeshWriter< VTUWriter< Grid_3_cuda >, FileFormat::zlib_compressed >( m, "VTUWriter_Grid_3" );
   export_MeshWriter< VTIWriter< Grid_3_cuda >, FileFormat::zlib_compressed >( m, "VTIWriter_Grid_3" );

   // Writers for unstructured meshes do not work with CUDA
}
