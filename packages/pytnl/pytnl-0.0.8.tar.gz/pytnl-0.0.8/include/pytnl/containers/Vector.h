#pragma once

#include <pytnl/pytnl.h>

#include <TNL/Containers/Vector.h>

#include "indexing.h"
#include "vector_operators.h"

template< typename ArrayType, typename VectorType >
void
export_Vector( nb::module_& m, const char* name )
{
   using IndexType = typename VectorType::IndexType;
   using RealType = typename VectorType::RealType;

   auto vector =  //
      nb::class_< VectorType, ArrayType >( m, name )
         // Constructors
         .def( nb::init<>() )
         // NOTE: the nb::init<...> does not work due to list-initialization and
         //       std::list_initializer constructor in ArrayType
         .def( my_init< IndexType >(), nb::arg( "size" ) )
         .def( my_init< IndexType, RealType >(), nb::arg( "size" ), nb::arg( "value" ) )

         // Typedefs
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

         // Serialization
         .def_static( "getSerializationType", &VectorType::getSerializationType )

         // Copy/Deepcopy
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

   def_vector_operators( vector );

   // override so slice indexing can be used with vector operators
   def_indexing< VectorType >( vector );
   def_slice_indexing< VectorType >( vector );
}
