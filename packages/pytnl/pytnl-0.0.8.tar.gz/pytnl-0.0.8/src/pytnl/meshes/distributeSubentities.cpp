#include <pytnl/pytnl.h>

#include <TNL/Meshes/DistributedMeshes/distributeSubentities.h>

void
export_distributeSubentities( nb::module_& m )
{
   using TNL::Meshes::DistributedMeshes::distributeSubentities;
   m.def( "distributeFaces",
          []( DistributedMeshOfTriangles_host& mesh )
          {
             distributeSubentities< 1 >( mesh );
          } );
   m.def( "distributeFaces",
          []( DistributedMeshOfQuadrangles_host& mesh )
          {
             distributeSubentities< 1 >( mesh );
          } );
   m.def( "distributeFaces",
          []( DistributedMeshOfTetrahedrons_host& mesh )
          {
             distributeSubentities< 2 >( mesh );
          } );
   m.def( "distributeFaces",
          []( DistributedMeshOfHexahedrons_host& mesh )
          {
             distributeSubentities< 2 >( mesh );
          } );
}
