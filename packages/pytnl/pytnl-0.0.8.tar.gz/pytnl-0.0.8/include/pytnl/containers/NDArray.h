#pragma once

#include <array>

#include <pytnl/pytnl.h>

#include <TNL/Containers/NDArray.h>
#include <TNL/Allocators/CudaHost.h>
#include <TNL/Allocators/CudaManaged.h>

#include "dlpack.h"

template< typename Index >
void
ndarray_check_index( std::size_t i, Index idx, Index size )
{
   if( idx < 0 )
      throw nb::index_error(
         ( std::to_string( i ) + "-th index is out-of-bounds: " + std::to_string( idx ) + " < 0" ).c_str() );
   if( idx >= size )
      throw nb::index_error(
         ( std::to_string( i ) + "-th index is out-of-bounds: " + std::to_string( idx ) + " >= " + std::to_string( size ) )
            .c_str() );
}

template< typename ArrayType, typename... Args >
void
ndarray_indexing( nb::class_< ArrayType, Args... >& array )
{
   using IndexType = typename ArrayType::IndexType;
   using ValueType = typename ArrayType::ValueType;
   constexpr std::size_t dim = ArrayType::getDimension();

   array.def(
      "__getitem__",
      [ dim ]( ArrayType& self, nb::object indices ) -> ValueType
      {
         nb::tuple tuple_indices;

         if( nb::isinstance< nb::tuple >( indices ) ) {
            tuple_indices = nb::cast< nb::tuple >( indices );
         }
         else {
            tuple_indices = nb::make_tuple( indices );
         }

         if( tuple_indices.size() != dim ) {
            throw nb::value_error( ( "Expected " + std::to_string( dim ) + " indices" ).c_str() );
         }

         std::array< IndexType, dim > indices_array;
         for( std::size_t i = 0; i < dim; ++i ) {
            indices_array[ i ] = nb::cast< IndexType >( tuple_indices[ i ] );
            ndarray_check_index( i, indices_array[ i ], self.getSizes()[ i ] );
         }

         // Unpack the array into the operator()
         return std::apply(
            [ & ]( auto... indices ) -> ValueType
            {
               // getElement is equivalent to operator[] on host but works on cuda
               return self.getElement( indices... );
            },
            indices_array );
      },
      nb::arg( "indices" ) );

   array.def(
      "__setitem__",
      [ dim ]( ArrayType& self, nb::object indices, ValueType value )
      {
         nb::tuple tuple_indices;

         if( nb::isinstance< nb::tuple >( indices ) ) {
            tuple_indices = nb::cast< nb::tuple >( indices );
         }
         else {
            tuple_indices = nb::make_tuple( indices );
         }

         if( tuple_indices.size() != dim ) {
            throw nb::value_error( ( "Expected " + std::to_string( dim ) + " indices" ).c_str() );
         }

         std::array< IndexType, dim > indices_array;
         for( std::size_t i = 0; i < dim; ++i ) {
            indices_array[ i ] = nb::cast< IndexType >( tuple_indices[ i ] );
            ndarray_check_index( i, indices_array[ i ], self.getSizes()[ i ] );
         }

         // Unpack and assign
         std::apply(
            [ & ]( auto... indices )
            {
               // setElement is equivalent to operator[] on host but works on cuda
               const auto idx = self.getStorageIndex( indices... );
               self.getStorageArray().setElement( idx, value );
            },
            indices_array );
      },
      nb::arg( "indices" ),
      nb::arg( "value" ) );
}

template< typename ArrayType, typename... Args >
void
ndarray_iteration( nb::class_< ArrayType, Args... >& array )
{
   using SizesHolderType = typename ArrayType::SizesHolderType;

   // FIXME: calling Python functions does not work on CUDA (even using Devices::Host fails due to GIL...)
   if constexpr( ! std::is_same_v< typename ArrayType::DeviceType, TNL::Devices::GPU > ) {
      array
         .def(
            "forAll",
            []( ArrayType& self, const nb::typed< nb::callable, nb::ellipsis, nb::any >& f )
            {
               self.template forAll< TNL::Devices::Sequential >( f );
            },
            nb::arg( "f" ),
            "Evaluates the function `f` for all elements of the array. "
            "The function is called with N indices, where N is the array dimension." )
         .def(
            "forInterior",
            []( ArrayType& self, const nb::typed< nb::callable, nb::ellipsis, nb::any >& f )
            {
               self.template forInterior< TNL::Devices::Sequential >( f );
            },
            nb::arg( "f" ),
            "Evaluates the function `f` for all interior elements of the array. "
            "Excludes one element from each side of each dimension." )
         .def(
            "forInterior",
            []( ArrayType& self,
                const SizesHolderType& begins,
                const SizesHolderType& ends,
                const nb::typed< nb::callable, nb::ellipsis, nb::any >& f )
            {
               self.template forInterior< TNL::Devices::Sequential >( begins, ends, f );
            },
            nb::arg( "begins" ),
            nb::arg( "ends" ),
            nb::arg( "f" ),
            "Evaluates the function `f` for all elements inside the given N-dimensional range `[begins, ends)`." )
         .def(
            "forBoundary",
            []( ArrayType& self, const nb::typed< nb::callable, nb::ellipsis, nb::any >& f )
            {
               self.template forBoundary< TNL::Devices::Sequential >( f );
            },
            nb::arg( "f" ),
            "Evaluates the function `f` for all boundary elements of the array." )
         .def(
            "forBoundary",
            []( ArrayType& self,
                const SizesHolderType& skipBegins,
                const SizesHolderType& skipEnds,
                const nb::typed< nb::callable, nb::ellipsis, nb::any >& f )
            {
               self.template forBoundary< TNL::Devices::Sequential >( skipBegins, skipEnds, f );
            },
            nb::arg( "skipBegins" ),
            nb::arg( "skipEnds" ),
            nb::arg( "f" ),
            "Evaluates the function `f` for all elements outside the given N-dimensional range "
            "`[skipBegins, skipEnds)`." );
   }
}

template< typename IndexerType >
nb::class_< IndexerType >
export_NDArrayIndexer( nb::module_& m, const char* name )
{
   using IndexType = typename IndexerType::IndexType;
   using SizesHolderType = typename IndexerType::SizesHolderType;
   using StridesHolderType = typename IndexerType::StridesHolderType;
   using OverlapsType = typename IndexerType::OverlapsType;

   auto indexer =  //
      nb::class_< IndexerType >( m, name )
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
         // No bindings for other types like SizesHolderType, StridesHolderType, and OverlapsType
         // (we have type casters instead)

         // Default constructor
         .def( nb::init<>(), "Constructs an empty NDArrayIndexer with zero sizes and strides" )

         // Constructor from sizes, strides, overlaps
         .def( nb::init< const SizesHolderType&, const StridesHolderType&, const OverlapsType& >(),
               "Constructs with given sizes, strides, and overlaps",
               nb::arg( "sizes" ),
               nb::arg( "strides" ),
               nb::arg( "overlaps" ) )

         // Dimension getter
         .def_static( "getDimension", &IndexerType::getDimension, "Returns the dimension of the N-dimensional array, i.e. N" )

         // Accessors
         .def( "getSizes",
               nb::overload_cast<>( &IndexerType::getSizes, nb::const_ ),
               "Returns the sizes of the array (as a tuple in Python)" )
         .def( "getStrides",
               nb::overload_cast<>( &IndexerType::getStrides, nb::const_ ),
               "Returns the strides of the array (as a tuple in Python)" )
         .def( "getOverlaps",
               nb::overload_cast<>( &IndexerType::getOverlaps, nb::const_ ),
               "Returns the overlaps of the array (as a tuple in Python)" )

         // Storage size
         .def( "getStorageSize", &IndexerType::getStorageSize, "Returns the total size needed to store the array" )

         // Storage index computation
         .def(
            "getStorageIndex",
            []( const IndexerType& self, const nb::args& indices )
            {
               if( len( static_cast< const nb::tuple& >( indices ) ) != IndexerType::getDimension() ) {
                  throw nb::value_error( "Incorrect number of indices" );
               }

               std::array< IndexType, IndexerType::getDimension() > indices_array;
               for( size_t i = 0; i < indices_array.size(); ++i ) {
                  indices_array[ i ] = nb::cast< IndexType >( indices[ i ] );
                  ndarray_check_index( i, indices_array[ i ], self.getSizes()[ i ] );
               }

               return std::apply(
                  [ & ]( auto... indices )
                  {
                     return self.getStorageIndex( indices... );
                  },
                  indices_array );
            },
            nb::sig( "def getStorageIndex(self, *indices: int) -> int" ),
            "Computes the linear storage index from N-dimensional indices" )

         // Contiguity check
         .def(
            "isContiguousBlock",
            []( const IndexerType& self, const SizesHolderType& begins, const SizesHolderType& ends )
            {
               return self.isContiguousBlock( begins, ends );
            },
            "Checks if a given block is contiguous",
            nb::arg( "begins" ),
            nb::arg( "ends" ) )

         // String representation
         .def(
            "__str__",
            []( const IndexerType& self )
            {
               constexpr std::size_t dim = IndexerType::getDimension();
               std::ostringstream oss;
               oss << "NDArrayIndexer[" << dim << "](";
               TNL::Algorithms::staticFor< std::size_t, 0, dim >(
                  [ & ]( auto i )
                  {
                     if constexpr( i > 0 )
                        oss << ", ";
                     oss << self.template getSize< i >();
                  } );
               oss << ")";
               return oss.str();
            },
            "Returns a readable string representation of the indexer" );

   return indexer;
}

template< typename ArrayType >
void
export_NDArray( nb::module_& m, const char* name )
{
   using IndexerType = typename ArrayType::IndexerType;
   using ValueType = typename ArrayType::ValueType;
   using DeviceType = typename ArrayType::DeviceType;

   auto array =  //
      nb::class_< ArrayType, IndexerType >( m, name )
         // Typedefs
         .def_prop_ro_static(  //
            "IndexerType",
            []( nb::handle ) -> nb::typed< nb::handle, nb::type_object >
            {
               return nb::type< IndexerType >();
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

         // Constructors
         .def( nb::init<>() )
         .def( nb::init< ArrayType >(), nb::arg( "other" ) )

         // Size management
         .def( "setSizes",
               &ArrayType::setSize,  // Note: C++ method should be renamed
               nb::arg( "sizes" ),
               "Set sizes of the array using an instance of SizesHolder (a tuple of ints in Python)" )
         .def(
            "setSizes",
            []( ArrayType& self, const nb::args& sizes )
            {
               constexpr std::size_t dim = ArrayType::getDimension();
               using IndexType = typename ArrayType::IndexType;

               if( sizes.size() != dim ) {
                  throw nb::value_error( ( "Expected " + std::to_string( dim ) + " sizes" ).c_str() );
               }

               std::array< IndexType, dim > sizes_array;
               for( std::size_t i = 0; i < dim; ++i ) {
                  sizes_array[ i ] = nb::cast< IndexType >( sizes[ i ] );
               }

               return std::apply(
                  [ & ]( auto... sizes )
                  {
                     self.setSizes( sizes... );
                  },
                  sizes_array );
            },
            nb::arg( "sizes" ),
            nb::sig( "def setSizes(self, *sizes: int) -> None" ),
            "Set sizes of the array using a sequence of ints" )
         .def(
            "setLike",
            []( ArrayType& self, const ArrayType& other )
            {
               self.setLike( other );
            },
            nb::arg( "other" ) )
         .def( "reset",
               &ArrayType::reset,
               "Reset the array to the empty state. The current data will be deallocated, "
               "thus all pointers and views to the array elements will become invalid." )

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
         .def( "setValue", &ArrayType::setValue, nb::arg( "value" ) )

         // Internal storage
         .def( "getStorageArray",
               nb::overload_cast<>( &ArrayType::getStorageArray ),
               nb::rv_policy::reference_internal,
               "Return a reference to the underlying storage array." )

         // String representation
         .def(
            "__str__",
            []( const ArrayType& self )
            {
               constexpr std::size_t dim = ArrayType::getDimension();
               std::ostringstream oss;
               oss << "NDArray[" << dim << ", ";
               if constexpr( std::is_same_v< ValueType, bool > ) {
                  oss << "bool";
               }
               else if constexpr( std::is_integral_v< ValueType > ) {
                  oss << "int";
               }
               else if constexpr( std::is_floating_point_v< ValueType > ) {
                  oss << "float";
               }
               else if constexpr( TNL::is_complex_v< ValueType > ) {
                  oss << "complex";
               }
               else {
                  oss << TNL::getType( ValueType{} );
               }
               oss << ", ";
               if constexpr( std::is_same_v< DeviceType, TNL::Devices::Cuda > )
                  oss << "Cuda";
               else
                  oss << "Host";
               oss << "](";
               TNL::Algorithms::staticFor< std::size_t, 0, dim >(
                  [ & ]( auto i )
                  {
                     if constexpr( i > 0 )
                        oss << ", ";
                     oss << self.template getSize< i >();
                  } );
               oss << ")";
               return oss.str();
            },
            "Returns a readable string representation of the array" )

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

               constexpr std::size_t dim = ArrayType::getDimension();
               std::array< std::size_t, dim > sizes;
               std::array< std::int64_t, dim > strides;
               TNL::Algorithms::staticFor< std::size_t, 0, dim >(
                  [ & ]( auto i )
                  {
                     sizes[ i ] = self.p->template getSize< i >();
                     strides[ i ] = self.p->template getStride< i >();
                  } );

               using array_api_t = nb::ndarray< nb::array_api, ValueType >;
               array_api_t array_api( self.p->getData(),
                                      dim,
                                      sizes.data(),
                                      self.h,  // pass the Python object associated with `self` as owner
                                      strides.data(),
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

   ndarray_indexing( array );
   ndarray_iteration( array );
}
