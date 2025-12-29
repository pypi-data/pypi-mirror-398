#pragma once

#include <pytnl/pytnl.h>

template< typename Mesh >
void
export_getEntitiesCount( nb::class_< Mesh >& scope )
{
   scope  //
      .def( "getEntitiesCount",
            []( Mesh& self, nb::type_object_t< typename Mesh::Cell > entity_type )
            {
               return self.template getEntitiesCount< Mesh::Cell::getEntityDimension() >();
            } )
      .def( "getEntitiesCount",
            []( Mesh& self, nb::type_object_t< typename Mesh::Vertex > entity_type )
            {
               return self.template getEntitiesCount< Mesh::Vertex::getEntityDimension() >();
            } );

   // avoid duplicate signature if the type is the same
   if constexpr( ! std::is_same_v< typename Mesh::Face, typename Mesh::Vertex > )
      scope.def( "getEntitiesCount",
                 []( Mesh& self, nb::type_object_t< typename Mesh::Face > entity_type )
                 {
                    return self.template getEntitiesCount< Mesh::Face::getEntityDimension() >();
                 } );
}

template< typename Mesh >
void
export_getGhostEntitiesCount( nb::class_< Mesh >& scope )
{
   scope  //
      .def( "getGhostEntitiesCount",
            []( Mesh& self, nb::type_object_t< typename Mesh::Cell > entity_type )
            {
               return self.template getGhostEntitiesCount< Mesh::Cell::getEntityDimension() >();
            } )
      .def( "getGhostEntitiesCount",
            []( Mesh& self, nb::type_object_t< typename Mesh::Vertex > entity_type )
            {
               return self.template getGhostEntitiesCount< Mesh::Vertex::getEntityDimension() >();
            } );

   // avoid duplicate signature if the type is the same
   if constexpr( ! std::is_same_v< typename Mesh::Face, typename Mesh::Vertex > )
      scope.def( "getGhostEntitiesCount",
                 []( Mesh& self, nb::type_object_t< typename Mesh::Face > entity_type )
                 {
                    return self.template getGhostEntitiesCount< Mesh::Face::getEntityDimension() >();
                 } );
}

template< typename Mesh >
void
export_getGhostEntitiesOffset( nb::class_< Mesh >& scope )
{
   scope  //
      .def( "getGhostEntitiesOffset",
            []( Mesh& self, nb::type_object_t< typename Mesh::Cell > entity_type )
            {
               return self.template getGhostEntitiesOffset< Mesh::Cell::getEntityDimension() >();
            } )
      .def( "getGhostEntitiesOffset",
            []( Mesh& self, nb::type_object_t< typename Mesh::Vertex > entity_type )
            {
               return self.template getGhostEntitiesOffset< Mesh::Vertex::getEntityDimension() >();
            } );

   // avoid duplicate signature if the type is the same
   if constexpr( ! std::is_same_v< typename Mesh::Face, typename Mesh::Vertex > )
      scope.def( "getGhostEntitiesOffset",
                 []( Mesh& self, nb::type_object_t< typename Mesh::Face > entity_type )
                 {
                    return self.template getGhostEntitiesOffset< Mesh::Face::getEntityDimension() >();
                 } );
}
