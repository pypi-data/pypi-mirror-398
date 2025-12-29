#pragma once

#include <pytnl/pytnl.h>

#include <TNL/Containers/Array.h>
#include <TNL/Allocators/CudaHost.h>
#include <TNL/Allocators/CudaManaged.h>

#include "dlpack.h"
#include "indexing.h"

template< typename ArrayType >
void
export_Array( nb::module_& m, const char* name )
{
   using IndexType = typename ArrayType::IndexType;
   using ValueType = typename ArrayType::ValueType;
   using DeviceType = typename ArrayType::DeviceType;

   auto array =  //
      nb::class_< ArrayType >( m, name )
         // Constructors
         .def( nb::init<>() )
         // NOTE: the nb::init<...> does not work due to list-initialization and
         //       std::list_initializer constructor in ArrayType
         .def( my_init< IndexType >(), nb::arg( "size" ) )
         .def( my_init< IndexType, ValueType >(), nb::arg( "size" ), nb::arg( "value" ) )

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

         // Size management
         .def( "getSize", &ArrayType::getSize )
         .def( "setSize", &ArrayType::setSize, nb::arg( "size" ) )
         .def( "setLike", &ArrayType::template setLike< ArrayType > )
         .def( "resize", nb::overload_cast< IndexType >( &ArrayType::resize ), nb::arg( "size" ) )
         .def(
            "resize", nb::overload_cast< IndexType, ValueType >( &ArrayType::resize ), nb::arg( "size" ), nb::arg( "value" ) )
         .def( "swap", &ArrayType::swap )
         .def( "reset", &ArrayType::reset )
         .def( "empty", &ArrayType::empty )

         // Data access
         .def(
            "setElement",
            []( ArrayType& array, typename ArrayType::IndexType i, typename ArrayType::ValueType value )
            {
               if( i < 0 || i >= array.getSize() )
                  throw nb::index_error( ( "index " + std::to_string( i ) + " is out-of-bounds for given array with size "
                                           + std::to_string( array.getSize() ) )
                                            .c_str() );
               array.setElement( i, value );
            },
            nb::arg( "i" ),
            nb::arg( "value" ) )
         .def(
            "getElement",
            []( const ArrayType& array, typename ArrayType::IndexType i )
            {
               if( i < 0 || i >= array.getSize() )
                  throw nb::index_error( ( "index " + std::to_string( i ) + " is out-of-bounds for given array with size "
                                           + std::to_string( array.getSize() ) )
                                            .c_str() );
               return array.getElement( i );
            },
            nb::arg( "i" ) )

         // Assignment
         .def( "assign",
               []( ArrayType& array, const ArrayType& other ) -> ArrayType&
               {
                  return array = other;
               } )

         // Comparison
         .def( nb::self == nb::self, nb::sig( "def __eq__(self, arg: object, /) -> bool" ) )
         .def( nb::self != nb::self, nb::sig( "def __ne__(self, arg: object, /) -> bool" ) )

         // Fill
         .def( "setValue", &ArrayType::setValue, nb::arg( "value" ), nb::arg( "begin" ) = 0, nb::arg( "end" ) = 0 )

         // File I/O
         .def_static( "getSerializationType", &ArrayType::getSerializationType )
         .def( "save", &ArrayType::save )
         .def( "load", &ArrayType::load )

         // String representation
         .def( "__str__",
               []( ArrayType& a )
               {
                  std::stringstream ss;
                  ss << a;
                  return ss.str();
               } )

         // Deepcopy support https://pybind11.readthedocs.io/en/stable/advanced/classes.html#deepcopy-support
         .def( "__copy__",
               []( const ArrayType& self )
               {
                  return ArrayType( self );
               } )
         .def(
            "__deepcopy__",
            []( const ArrayType& self, nb::typed< nb::dict, nb::str, nb::any > )
            {
               return ArrayType( self );
            },
            nb::arg( "memo" ) );

   // Interoperability with Python array API standard (DLPack)
   // (note that the set of dtypes supported by DLPack is limited)
   if constexpr( nb::dtype< ValueType >().bits != 0 ) {
      array
         .def(
            "__dlpack__",
            []( nb::pointer_and_handle< ArrayType > self, nb::kwargs kwargs )
            {
               int device_id = 0;
               // FIXME: DLPack support switching CUDA devices but TNL does not
               if constexpr( std::is_same_v< DeviceType, TNL::Devices::Cuda > )
                  device_id = TNL::Backend::getDevice();

               using array_api_t = nb::ndarray< nb::array_api, ValueType >;
               array_api_t array_api( self.p->getData(),
                                      { static_cast< std::size_t >( self.p->getSize() ) },
                                      self.h,  // pass the Python object associated with `self` as owner
                                      {},      // strides
                                      nb::dtype< ValueType >(),
                                      dlpack_device< ArrayType >().first,
                                      device_id );

               // call the array_api's __dlpack__ Python method to properly handle the kwargs
               nb::object aa = nb::cast( array_api, nb::rv_policy::reference_internal, self.h );
               return aa.attr( "__dlpack__" )( **kwargs );
            },
            nb::sig( "def __dlpack__(self, **kwargs: typing.Any) -> typing_extensions.CapsuleType" ) )
         .def_static( "__dlpack_device__", dlpack_device< ArrayType > );
   }

   def_indexing< ArrayType >( array );
   def_slice_indexing< ArrayType >( array );
}
