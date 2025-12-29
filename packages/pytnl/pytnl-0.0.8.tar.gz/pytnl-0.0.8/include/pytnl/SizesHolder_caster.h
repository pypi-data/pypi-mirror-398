#pragma once

#include <nanobind/nanobind.h>

#include <TNL/Containers/ndarray/SizesHolder.h>

namespace nanobind {
namespace detail {

template< typename Index, std::size_t... sizes >
struct type_caster< TNL::Containers::SizesHolder< Index, sizes... > >
{
private:
   using SizesHolderType = TNL::Containers::SizesHolder< Index, sizes... >;
   using IndexType = Index;
   static constexpr std::size_t dim = SizesHolderType::getDimension();

public:
   NB_TYPE_CASTER( SizesHolderType, make_caster< decltype( std::make_tuple( sizes... ) ) >::Name );

   // Conversion from Python to C++
   bool
   from_python( handle src, std::uint8_t flags, cleanup_list* cleanup )
   {
      if( ! isinstance< nanobind::tuple >( src ) ) {
         return false;
      }

      // Note: nanobind::detail::tuple is not nanobind::tuple
      nanobind::tuple py_tuple = nanobind::tuple( src );
      if( len( py_tuple ) != dim ) {
         return false;
      }

      std::array< IndexType, dim > elements;
      if( ! try_cast( py_tuple, elements ) )
         return false;

      // Validate that static dimensions are zero
      bool valid = true;
      TNL::Algorithms::staticFor< std::size_t, 0, dim >(
         [ & ]( auto level )
         {
            constexpr IndexType static_size = SizesHolderType::template getStaticSize< level >();
            if constexpr( static_size > 0 ) {
               // Python-specific behavior change: allow setting dynamic size equal to the static size
               if( elements[ level ] == static_size )
                  elements[ level ] = 0;
               // Same validation as in the SizesHolder class: "Dynamic size for a static dimension must be 0."
               if( elements[ level ] != 0 ) {
                  valid = false;
               }
            }
         } );
      if( ! valid ) {
         std::cout << "input tuple is not valid as requested SizesHolder\n";
         return false;
      }

      value = create_from_array( elements );

      return true;
   }

   // Conversion from C++ to Python
   static handle
   from_cpp( const SizesHolderType& src, rv_policy policy, cleanup_list* cleanup )
   {
      PyObject* py_tuple = PyTuple_New( dim );
      TNL::Algorithms::staticFor< std::size_t, 0, dim >(
         [ & ]( auto level )
         {
            constexpr IndexType static_size = SizesHolderType::getStaticSize( level );
            object element;
            if constexpr( static_size > 0 ) {
               element = cast( static_size );
            }
            else {
               element = cast( src[ level ] );
            }
            NB_TUPLE_SET_ITEM( py_tuple, level, element.release().ptr() );
         } );
      return py_tuple;
   }

private:
   // Helper to unpack array into constructor parameter pack
   template< std::size_t... Idx >
   static SizesHolderType
   create_from_array( const std::array< IndexType, SizesHolderType::getDimension() >& elements, std::index_sequence< Idx... > )
   {
      return SizesHolderType( elements[ Idx ]... );
   }

   static SizesHolderType
   create_from_array( const std::array< IndexType, SizesHolderType::getDimension() >& elements )
   {
      return create_from_array( elements, std::make_index_sequence< SizesHolderType::getDimension() >() );
   }
};

}  // namespace detail
}  // namespace nanobind
