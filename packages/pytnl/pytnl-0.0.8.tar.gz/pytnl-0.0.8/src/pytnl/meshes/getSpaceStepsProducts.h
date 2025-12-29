#pragma once

#include <pytnl/pytnl.h>

template< typename Grid >
struct SpaceStepsProductsGetter
{};

template< typename RealType, typename DeviceType, typename IndexType >
struct SpaceStepsProductsGetter< TNL::Meshes::Grid< 1, RealType, DeviceType, IndexType > >
{
   using Grid = TNL::Meshes::Grid< 1, RealType, DeviceType, IndexType >;

   static RealType
   get( const Grid& grid, const int& xPow )
   {
      if( xPow == -2 )
         return grid.template getSpaceStepsProducts< -2 >();
      if( xPow == -1 )
         return grid.template getSpaceStepsProducts< -1 >();
      if( xPow == 0 )
         return grid.template getSpaceStepsProducts< 0 >();
      if( xPow == 1 )
         return grid.template getSpaceStepsProducts< 1 >();
      if( xPow == 2 )
         return grid.template getSpaceStepsProducts< 2 >();
      const auto hx = grid.template getSpaceStepsProducts< 1 >();
      return pow( hx, xPow );
   }

   template< typename PyGrid >
   static void
   export_getSpaceSteps( PyGrid& scope )
   {
      scope.def( "getSpaceStepsProducts", get, nb::arg( "xPow" ) );
   }
};

template< typename RealType, typename DeviceType, typename IndexType >
struct SpaceStepsProductsGetter< TNL::Meshes::Grid< 2, RealType, DeviceType, IndexType > >
{
   using Grid = TNL::Meshes::Grid< 2, RealType, DeviceType, IndexType >;

   static RealType
   get( const Grid& grid, const int& xPow, const int& yPow = 0 )
   {
      if( xPow == 0 && yPow == 0 )
         return grid.template getSpaceStepsProducts< 0, 0 >();
      auto hx = grid.template getSpaceStepsProducts< 1, 0 >();
      auto hy = grid.template getSpaceStepsProducts< 0, 1 >();
      if( xPow != 1 )
         hx = pow( hx, xPow );
      if( yPow != 1 )
         hy = pow( hy, yPow );
      return hx * hy;
   }

   template< typename PyGrid >
   static void
   export_getSpaceSteps( PyGrid& scope )
   {
      scope.def( "getSpaceStepsProducts", get, nb::arg( "xPow" ), nb::arg( "yPow" ) = 0 );
   }
};

template< typename RealType, typename DeviceType, typename IndexType >
struct SpaceStepsProductsGetter< TNL::Meshes::Grid< 3, RealType, DeviceType, IndexType > >
{
   using Grid = TNL::Meshes::Grid< 3, RealType, DeviceType, IndexType >;

   static RealType
   get( const Grid& grid, const int& xPow, const int& yPow = 0, const int& zPow = 0 )
   {
      if( xPow == 0 && yPow == 0 && zPow == 0 )
         return grid.template getSpaceStepsProducts< 0, 0, 0 >();
      auto hx = grid.template getSpaceStepsProducts< 1, 0, 0 >();
      auto hy = grid.template getSpaceStepsProducts< 0, 1, 0 >();
      auto hz = grid.template getSpaceStepsProducts< 0, 0, 1 >();
      if( xPow != 1 )
         hx = pow( hx, xPow );
      if( yPow != 1 )
         hy = pow( hy, yPow );
      if( zPow != 1 )
         hz = pow( hz, zPow );
      return hx * hy * hz;
   }

   template< typename PyGrid >
   static void
   export_getSpaceSteps( PyGrid& scope )
   {
      scope.def( "getSpaceStepsProducts", get, nb::arg( "xPow" ), nb::arg( "yPow" ) = 0, nb::arg( "zPow" ) = 0 );
   }
};
