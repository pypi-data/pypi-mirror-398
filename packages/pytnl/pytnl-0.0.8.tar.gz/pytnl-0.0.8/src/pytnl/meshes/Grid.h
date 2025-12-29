#pragma once

#include <type_traits>

#include <pytnl/pytnl.h>

#include "getSpaceStepsProducts.h"
#include "mesh_getters.h"

template< typename GridEntity, typename PyGrid >
nb::class_< GridEntity >
export_GridEntity( PyGrid& scope, const char* name )
{
   auto entity =
      nb::class_< GridEntity >( scope, name )
         .def( nb::init< typename GridEntity::GridType >(), nb::rv_policy::reference_internal )
         .def( nb::init< typename GridEntity::GridType, typename GridEntity::CoordinatesType >(),
               nb::rv_policy::reference_internal )
         .def( nb::init< typename GridEntity::GridType,
                         typename GridEntity::CoordinatesType,
                         typename GridEntity::CoordinatesType >(),
               nb::rv_policy::reference_internal )
         .def( nb::init< typename GridEntity::GridType,
                         typename GridEntity::CoordinatesType,
                         typename GridEntity::CoordinatesType,
                         typename GridEntity::IndexType >(),
               nb::rv_policy::reference_internal )
         .def( nb::init< typename GridEntity::GridType, typename GridEntity::IndexType >(), nb::rv_policy::reference_internal )
         .def_static( "getEntityDimension", &GridEntity::getEntityDimension )
         .def_static( "getMeshDimension", &GridEntity::getMeshDimension )
         // TODO: constructors
         .def( "getCoordinates", nb::overload_cast<>( &GridEntity::getCoordinates ), nb::rv_policy::reference_internal )
         .def( "setCoordinates", &GridEntity::setCoordinates )
         .def( "refresh", &GridEntity::refresh )
         .def( "getIndex", &GridEntity::getIndex )
         .def( "getNormals", &GridEntity::getNormals )
         .def( "setNormals", &GridEntity::setNormals )
         .def( "getOrientation", &GridEntity::getOrientation )
         .def( "setOrientation", &GridEntity::setOrientation )
         .def( "getBasis", &GridEntity::getBasis )
         // TODO: getNeighbourEntity
         .def( "isBoundary", &GridEntity::isBoundary )
         .def( "getCenter", &GridEntity::getCenter )
         .def( "getMeasure", &GridEntity::getMeasure )
         .def( "getMesh", &GridEntity::getMesh, nb::rv_policy::reference_internal );

   return entity;
}

template< typename Grid >
void
export_Grid( nb::module_& m, const char* name )
{
   void ( Grid::*_setDimensions )( const typename Grid::CoordinatesType& ) = &Grid::setDimensions;
   void ( Grid::*_setOrigin )( const typename Grid::PointType& ) = &Grid::setOrigin;

   auto grid =
      nb::class_< Grid >( m, name )
         .def( nb::init<>() )
         .def_static( "getMeshDimension", &Grid::getMeshDimension )
         .def( "setDimensions", _setDimensions )
         .def( "getDimensions", &Grid::getDimensions, nb::rv_policy::reference_internal )
         .def( "setDomain", &Grid::setDomain )
         .def( "setOrigin", _setOrigin )
         .def( "getOrigin", &Grid::getOrigin, nb::rv_policy::reference_internal )
         .def( "getProportions", &Grid::getProportions, nb::rv_policy::reference_internal )
         // NOTE: if combined into getEntity, the return type would depend on
         // the runtime parameter (entity)
         .def( "getCell",
               nb::overload_cast< typename Grid::IndexType >( &Grid::template getEntity< typename Grid::Cell >, nb::const_ ) )
         .def( "getCell",
               nb::overload_cast< const typename Grid::CoordinatesType& >( &Grid::template getEntity< typename Grid::Cell >,
                                                                           nb::const_ ) )
         .def( "getFace",
               nb::overload_cast< typename Grid::IndexType >( &Grid::template getEntity< typename Grid::Face >, nb::const_ ) )
         .def( "getFace",
               nb::overload_cast< const typename Grid::CoordinatesType& >( &Grid::template getEntity< typename Grid::Face >,
                                                                           nb::const_ ) )
         .def( "getVertex",
               nb::overload_cast< typename Grid::IndexType >( &Grid::template getEntity< typename Grid::Vertex >, nb::const_ ) )
         .def( "getVertex",
               nb::overload_cast< const typename Grid::CoordinatesType& >( &Grid::template getEntity< typename Grid::Vertex >,
                                                                           nb::const_ ) )
         .def( "getEntityIndex", &Grid::template getEntityIndex< typename Grid::Cell > )
         .def( "getEntityIndex", &Grid::template getEntityIndex< typename Grid::Vertex > )
         .def( "getCellMeasure", &Grid::getCellMeasure, nb::rv_policy::reference_internal )
         .def( "getSpaceSteps", &Grid::getSpaceSteps, nb::rv_policy::reference_internal )
         .def( "getSmallestSpaceStep", &Grid::getSmallestSpaceStep )

         // Comparison operators
         .def( nb::self == nb::self, nb::sig( "def __eq__(self, arg: object, /) -> bool" ) )
         .def( nb::self != nb::self, nb::sig( "def __ne__(self, arg: object, /) -> bool" ) )

      // TODO: more?
      ;

   // avoid duplicate signature if the type is the same
   if constexpr( ! std::is_same_v< typename Grid::Face, typename Grid::Vertex > )
      grid.def( "getEntityIndex", &Grid::template getEntityIndex< typename Grid::Face > );

   // complicated methods
   export_getEntitiesCount( grid );
   SpaceStepsProductsGetter< Grid >::export_getSpaceSteps( grid );

   // nested types
   grid.def_prop_ro_static(  //
      "CoordinatesType",
      []( nb::handle ) -> nb::typed< nb::handle, nb::type_object >
      {
         return nb::type< typename Grid::CoordinatesType >();
      } );
   grid.def_prop_ro_static(  //
      "PointType",
      []( nb::handle ) -> nb::typed< nb::handle, nb::type_object >
      {
         return nb::type< typename Grid::PointType >();
      } );
   export_GridEntity< typename Grid::Cell >( grid, "Cell" );
   auto Vertex = export_GridEntity< typename Grid::Vertex >( grid, "Vertex" );
   // avoid duplicate conversion if the type is the same
   if constexpr( std::is_same_v< typename Grid::Face, typename Grid::Vertex > )
      grid.attr( "Face" ) = Vertex;
   else
      export_GridEntity< typename Grid::Face >( grid, "Face" );
}
