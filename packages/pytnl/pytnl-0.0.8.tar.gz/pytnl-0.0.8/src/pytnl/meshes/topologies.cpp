#include <pytnl/pytnl.h>

#include <TNL/Meshes/Topologies/Edge.h>
#include <TNL/Meshes/Topologies/Hexahedron.h>
#include <TNL/Meshes/Topologies/Polygon.h>
#include <TNL/Meshes/Topologies/Polyhedron.h>
#include <TNL/Meshes/Topologies/Quadrangle.h>
#include <TNL/Meshes/Topologies/Tetrahedron.h>
#include <TNL/Meshes/Topologies/Triangle.h>

template< typename Topology, typename Scope >
void
export_topology( Scope& m, const char* name )
{
   nb::class_< Topology >( m, name );
}

void
export_topologies( nb::module_& m )
{
   auto submodule = m.def_submodule( "topologies" );

   export_topology< TNL::Meshes::Topologies::Edge >( submodule, "Edge" );
   export_topology< TNL::Meshes::Topologies::Hexahedron >( submodule, "Hexahedron" );
   export_topology< TNL::Meshes::Topologies::Polygon >( submodule, "Polygon" );
   export_topology< TNL::Meshes::Topologies::Polyhedron >( submodule, "Polyhedron" );
   export_topology< TNL::Meshes::Topologies::Quadrangle >( submodule, "Quadrangle" );
   export_topology< TNL::Meshes::Topologies::Tetrahedron >( submodule, "Tetrahedron" );
   export_topology< TNL::Meshes::Topologies::Triangle >( submodule, "Triangle" );
}
