#pragma once

#include <pytnl/pytnl.h>
#include <pytnl/RawIterator.h>

template< typename Array, typename Scope >
void
def_indexing( Scope& scope )
{
   using Index = typename Array::IndexType;
   using Value = typename Array::ValueType;

   scope.def( "__len__",
              &Array::getSize,
              // need to set custom signature because StaticArray has static getSize
              // and .def() generates a signature without argument by default
              nb::sig( "def __len__(self) -> int" ) );

   scope.def(
      "__iter__",
      []( Array& array )
      {
         return nb::make_iterator( nb::type< Array >(),
                                   "Iterator",
                                   RawIterator< Value >( array.getData() ),
                                   RawIterator< Value >( array.getData() + array.getSize() ) );
      },
      nb::keep_alive< 0, 1 >()  // keep array alive while iterator is used
   );

   scope.def( "__getitem__",
              []( Array& a, Index i )
              {
                 if( i < 0 || i >= a.getSize() )
                    throw nb::index_error( ( "index " + std::to_string( i ) + " is out-of-bounds for given array with size "
                                             + std::to_string( a.getSize() ) )
                                              .c_str() );
                 // getElement is equivalent to operator[] on host but works on cuda
                 return a.getElement( i );
              } );

   scope.def( "__setitem__",
              []( Array& a, Index i, const Value& e )
              {
                 if( i < 0 || i >= a.getSize() )
                    throw nb::index_error( ( "index " + std::to_string( i ) + " is out-of-bounds for given array with size "
                                             + std::to_string( a.getSize() ) )
                                              .c_str() );
                 // setElement is equivalent to operator[] on host but works on cuda
                 a.setElement( i, e );
              } );
}

template< typename Array, typename Scope >
void
def_slice_indexing( Scope& scope )
{
   /// Slicing protocol
   scope.def(
      "__getitem__",
      []( const Array& a, nb::slice slice ) -> Array*
      {
         auto [ start, stop, step, slicelength ] = slice.compute( a.getSize() );

         Array* seq = new Array();
         seq->setSize( slicelength );

         for( std::size_t i = 0; i < slicelength; ++i ) {
            // setElement/getElement is equivalent to operator[] on host but works on cuda
            seq->setElement( i, a.getElement( start ) );
            start += step;
         }
         return seq;
      },
      "Retrieve list elements using a slice object" );

   scope.def(
      "__setitem__",
      []( Array& a, nb::slice slice, const Array& value )
      {
         auto [ start, stop, step, slicelength ] = slice.compute( a.getSize() );

         if( slicelength != (std::size_t) value.getSize() )
            throw std::runtime_error( "Left and right hand size of slice "
                                      "assignment have different sizes!" );

         for( std::size_t i = 0; i < slicelength; ++i ) {
            // setElement/getElement is equivalent to operator[] on host but works on cuda
            a.setElement( start, value.getElement( i ) );
            start += step;
         }
      },
      "Assign list elements using a slice object" );
}
