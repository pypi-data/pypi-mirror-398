#include <pytnl/exceptions.h>
#include <pytnl/pytnl.h>

void
export_Grid1D( nb::module_& m );
void
export_Grid2D( nb::module_& m );
void
export_Grid3D( nb::module_& m );
void
export_Meshes( nb::module_& m );
void
export_MeshReaders( nb::module_& m );
void
export_MeshWriters( nb::module_& m );
void
export_DistributedMeshes( nb::module_& m );
void
export_DistributedMeshReaders( nb::module_& m );
void
export_DistributedMeshWriters( nb::module_& m );
void
export_resolveMeshType( nb::module_& m );

// Python module definition
NB_MODULE( _meshes_cuda, m )
{
   register_exceptions( m );

   // import depending modules
   nb::module_::import_( "pytnl._containers_cuda" );
   nb::module_::import_( "pytnl._meshes" );

   // bindings for data structures
   export_Grid1D( m );
   export_Grid2D( m );
   export_Grid3D( m );
   export_Meshes( m );
   export_MeshReaders( m );
   export_MeshWriters( m );

   // bindings for distributed data structures
   export_DistributedMeshes( m );
   export_DistributedMeshReaders( m );
   export_DistributedMeshWriters( m );

   // bindings for functions
   export_resolveMeshType( m );
}
