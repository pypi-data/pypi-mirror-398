#pragma once

#include <pytnl/pytnl.h>

#include "indexing.h"
#include "vector_operators.h"

template< typename VectorType, typename Scope >
void
export_StaticVector( Scope& scope, const char* name )
{
   using IndexType = typename VectorType::IndexType;
   using ValueType = typename VectorType::ValueType;
   using RealType = typename VectorType::RealType;

   auto vector =  //
      nb::class_< VectorType >( scope, name )
         // NOTE: the nb::init<...> does not work due to list-initialization and
         //       std::list_initializer constructor in ArrayType
         .def( my_init< RealType >() )
         .def( my_init< VectorType >() )
         // this enables initialization from Python lists (assuming that implicit conversion for STL containers is enabled)
         .def( my_init< std::array< ValueType, VectorType::getSize() > >() )

         // Conversion back to Python list through the STL container
         .def( "as_list",
               []( VectorType& self )
               {
                  return reinterpret_cast< std::array< ValueType, VectorType::getSize() >& >( self );
               } )

         // Typedefs
         .def_prop_ro_static(  //
            "IndexType",
            []( nb::handle ) -> nb::typed< nb::handle, nb::type_object >
            {
               // nb::type<> does not handle generic types like int, float, etc.
               // https://github.com/wjakob/nanobind/discussions/1070
               if constexpr( std::is_integral_v< IndexType > ) {
                  return nb::borrow( &PyLong_Type );
               }
               else {
                  return nb::type< IndexType >();
               }
            } )
         .def_prop_ro_static(  //
            "ValueType",
            []( nb::handle ) -> nb::typed< nb::handle, nb::type_object >
            {
               // nb::type<> does not handle generic types like int, float, etc.
               // https://github.com/wjakob/nanobind/discussions/1070
               if constexpr( std::is_same_v< ValueType, bool > ) {
                  return nb::borrow( &PyBool_Type );
               }
               else if constexpr( std::is_integral_v< ValueType > ) {
                  return nb::borrow( &PyLong_Type );
               }
               else if constexpr( std::is_floating_point_v< ValueType > ) {
                  return nb::borrow( &PyFloat_Type );
               }
               else if constexpr( TNL::is_complex_v< ValueType > ) {
                  return nb::borrow( &PyComplex_Type );
               }
               else {
                  return nb::type< ValueType >();
               }
            } )
         .def_prop_ro_static(  //
            "RealType",
            []( nb::handle ) -> nb::typed< nb::handle, nb::type_object >
            {
               // nb::type<> does not handle generic types like int, float, etc.
               // https://github.com/wjakob/nanobind/discussions/1070
               if constexpr( std::is_same_v< RealType, bool > ) {
                  return nb::borrow( &PyBool_Type );
               }
               else if constexpr( std::is_integral_v< RealType > ) {
                  return nb::borrow( &PyLong_Type );
               }
               else if constexpr( std::is_floating_point_v< RealType > ) {
                  return nb::borrow( &PyFloat_Type );
               }
               else if constexpr( TNL::is_complex_v< RealType > ) {
                  return nb::borrow( &PyComplex_Type );
               }
               else {
                  return nb::type< RealType >();
               }
            } )

         // Size getter
         .def_static( "getSize", &VectorType::getSize )

         // Assignment
         .def( "assign",
               []( VectorType& vector, const VectorType& other ) -> VectorType&
               {
                  return vector = other;
               } )

         // Fill
         .def( "setValue", &VectorType::setValue )

         // TODO: __str__ and __repr__

         // Deepcopy support https://pybind11.readthedocs.io/en/stable/advanced/classes.html#deepcopy-support
         .def( "__copy__",
               []( const VectorType& self )
               {
                  return VectorType( self );
               } )
         .def(
            "__deepcopy__",
            []( const VectorType& self, nb::typed< nb::dict, nb::str, nb::any > )
            {
               return VectorType( self );
            },
            nb::arg( "memo" ) );

   // x, y, z properties
   vector.def_prop_rw(
      "x",
      []( const VectorType& self )
      {
         return self.x();
      },
      []( VectorType& self, ValueType value )
      {
         self.x() = value;
      } );
   if constexpr( VectorType::getSize() >= 2 ) {
      vector.def_prop_rw(
         "y",
         []( const VectorType& self )
         {
            return self.y();
         },
         []( VectorType& self, ValueType value )
         {
            self.y() = value;
         } );
   }
   if constexpr( VectorType::getSize() >= 3 ) {
      vector.def_prop_rw(
         "z",
         []( const VectorType& self )
         {
            return self.z();
         },
         []( VectorType& self, ValueType value )
         {
            self.z() = value;
         } );
   }

   def_vector_operators( vector );
   def_indexing< VectorType >( vector );
}
