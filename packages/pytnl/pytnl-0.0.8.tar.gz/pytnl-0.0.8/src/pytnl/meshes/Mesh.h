#pragma once

#include <type_traits>

#include <pytnl/pytnl.h>

#include "mesh_getters.h"

#include <TNL/Meshes/Geometry/getEntityCenter.h>
#include <TNL/Meshes/Geometry/getEntityMeasure.h>
#include <TNL/String.h>

template< typename MeshEntity, int Superdimension, typename Scope >
void
export_getSuperentityIndex( Scope& m )
{
   if constexpr( Superdimension <= MeshEntity::MeshType::getMeshDimension()
                 // && MeshEntity::template SuperentityTraits< Superdimension >::storageEnabled
   )
   {
      m.def( "getSuperentityIndex",
             []( const MeshEntity& entity, const typename MeshEntity::LocalIndexType& i )
             {
                return entity.template getSuperentityIndex< Superdimension >( i );
             } );
   }
}

template< typename MeshEntity, int Subdimension, typename Scope >
void
export_getSubentityIndex( Scope& m, const char* name )
{
   if constexpr( Subdimension <= MeshEntity::MeshType::getMeshDimension()
                 && ( Subdimension < MeshEntity::getEntityDimension() ) )
   {
      m.def( name,
             []( const MeshEntity& entity, const typename MeshEntity::LocalIndexType& i )
             {
                return entity.template getSubentityIndex< Subdimension >( i );
             } );
   }
}

template< typename MeshEntity, typename Scope >
void
export_getPoint( Scope& scope )
{
   if constexpr( MeshEntity::getEntityDimension() == 0 ) {
      scope.def( "getPoint",
                 []( const MeshEntity& entity )
                 {
                    return entity.getPoint();
                 } );
   }
}

template< typename MeshEntity, typename Scope >
nb::class_< MeshEntity >
export_MeshEntity( Scope& scope, const char* name )
{
   auto entity =  //
      nb::class_< MeshEntity >( scope, name )
         //.def(nb::init<>())
         //.def(nb::init<typename MeshEntity::MeshType, typename
         //MeshEntity::GlobalIndexType>())
         .def_static( "getEntityDimension", &MeshEntity::getEntityDimension )
         .def( "getIndex", &MeshEntity::getIndex )
         .def( "getTag", &MeshEntity::getTag )
      // TODO
      ;

   export_getSuperentityIndex< MeshEntity, MeshEntity::getEntityDimension() + 1 >( entity );
   export_getSubentityIndex< MeshEntity, 0 >( entity, "getSubvertexIndex" );
   export_getPoint< MeshEntity >( entity );

   return entity;
}

template< typename Mesh >
void
export_Mesh( nb::module_& m, const char* name )
{
   auto mesh =  //
      nb::class_< Mesh >( m, name )
         .def( nb::init<>() )
         .def_static( "getMeshDimension", &Mesh::getMeshDimension )
         // NOTE: if combined into getEntity, the return type would depend on
         // the runtime parameter (entity)
         .def( "getCell", &Mesh::template getEntity< typename Mesh::Cell > )
         .def( "getFace", &Mesh::template getEntity< typename Mesh::Face > )
         .def( "getVertex", &Mesh::template getEntity< typename Mesh::Vertex > )
         .def( "getEntityCenter",
               []( const Mesh& mesh, const typename Mesh::Cell& cell )
               {
                  return getEntityCenter( mesh, cell );
               } )
         .def( "getEntityCenter",
               []( const Mesh& mesh, const typename Mesh::Vertex& vertex )
               {
                  return getEntityCenter( mesh, vertex );
               } )
         .def( "getEntityMeasure",
               []( const Mesh& mesh, const typename Mesh::Cell& cell )
               {
                  return getEntityMeasure( mesh, cell );
               } )
         .def( "getEntityMeasure",
               []( const Mesh& mesh, const typename Mesh::Vertex& vertex )
               {
                  return getEntityMeasure( mesh, vertex );
               } )
         .def( "isBoundaryEntity",
               []( const Mesh& mesh, const typename Mesh::Cell& cell )
               {
                  return mesh.template isBoundaryEntity< Mesh::Cell::getEntityDimension() >( cell.getIndex() );
               } )
         .def( "isBoundaryEntity",
               []( const Mesh& mesh, const typename Mesh::Vertex& vertex )
               {
                  return mesh.template isBoundaryEntity< Mesh::Vertex::getEntityDimension() >( vertex.getIndex() );
               } )
         .def( "isGhostEntity",
               []( const Mesh& mesh, const typename Mesh::Cell& cell )
               {
                  return mesh.template isGhostEntity< Mesh::Cell::getEntityDimension() >( cell.getIndex() );
               } )
         .def( "isGhostEntity",
               []( const Mesh& mesh, const typename Mesh::Vertex& vertex )
               {
                  return mesh.template isGhostEntity< Mesh::Vertex::getEntityDimension() >( vertex.getIndex() );
               } )

         // Comparison operators
         .def( nb::self == nb::self, nb::sig( "def __eq__(self, arg: object, /) -> bool" ) )
         .def( nb::self != nb::self, nb::sig( "def __ne__(self, arg: object, /) -> bool" ) )

      // TODO: more?
      ;

   // avoid duplicate signature if the type is the same
   if constexpr( ! std::is_same_v< typename Mesh::Face, typename Mesh::Vertex > ) {
      mesh  //
         .def( "getEntityCenter",
               []( const Mesh& mesh, const typename Mesh::Face& face )
               {
                  return getEntityCenter( mesh, face );
               } )
         .def( "getEntityMeasure",
               []( const Mesh& mesh, const typename Mesh::Face& face )
               {
                  return getEntityMeasure( mesh, face );
               } )
         .def( "isBoundaryEntity",
               []( const Mesh& mesh, const typename Mesh::Face& face )
               {
                  return mesh.template isBoundaryEntity< Mesh::Face::getEntityDimension() >( face.getIndex() );
               } )
         .def( "isGhostEntity",
               []( const Mesh& mesh, const typename Mesh::Face& face )
               {
                  return mesh.template isGhostEntity< Mesh::Face::getEntityDimension() >( face.getIndex() );
               } );
   }

   export_getEntitiesCount( mesh );
   export_getGhostEntitiesCount( mesh );
   export_getGhostEntitiesOffset( mesh );

   // nested types
   export_MeshEntity< typename Mesh::Cell >( mesh, "Cell" );
   auto Vertex = export_MeshEntity< typename Mesh::Vertex >( mesh, "Vertex" );
   // avoid duplicate conversion if the type is the same
   if constexpr( std::is_same< typename Mesh::Face, typename Mesh::Vertex >::value )
      mesh.attr( "Face" ) = Vertex;
   else
      export_MeshEntity< typename Mesh::Face >( mesh, "Face" );
}
