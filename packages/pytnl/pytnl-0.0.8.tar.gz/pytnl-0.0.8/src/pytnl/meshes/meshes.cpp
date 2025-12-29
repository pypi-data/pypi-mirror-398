#include <pytnl/exceptions.h>
#include <pytnl/pytnl.h>

#include <TNL/MPI/ScopedInitializer.h>
#include <TNL/MPI/Wrappers.h>

void
export_topologies( nb::module_& m );
void
export_VTKTraits( nb::module_& m );

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
void
export_distributeSubentities( nb::module_& m );

// Python module definition
NB_MODULE( _meshes, m )
{
   register_exceptions( m );

   // import depending modules
   nb::module_::import_( "pytnl._containers" );

   // MPI initialization and finalization
   // https://stackoverflow.com/q/64647846
   if( ! TNL::MPI::Initialized() ) {
      int argc = 0;
      char** argv = nullptr;
      TNL::MPI::Init( argc, argv );
   }
   // https://pybind11.readthedocs.io/en/stable/advanced/misc.html#module-destructors
   auto atexit = nb::module_::import_( "atexit" );
   atexit.attr( "register" )( nb::cpp_function(
      []()
      {
         if( TNL::MPI::Initialized() && ! TNL::MPI::Finalized() )
            TNL::MPI::Finalize();
      } ) );

   // bindings for traits
   export_topologies( m );
   export_VTKTraits( m );

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
   export_distributeSubentities( m );
}
