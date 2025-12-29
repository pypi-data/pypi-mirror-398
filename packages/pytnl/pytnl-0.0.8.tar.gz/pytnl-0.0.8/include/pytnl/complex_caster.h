#pragma once

#include <nanobind/nanobind.h>
#include <nanobind/ndarray.h>

#include <TNL/Arithmetics/Complex.h>

namespace nanobind {
namespace detail {

template< typename T >
class type_caster< TNL::Arithmetics::Complex< T > >
{
   using ComplexType = TNL::Arithmetics::Complex< T >;
   using StdComplexCaster = type_caster< std::complex< T > >;
   StdComplexCaster _caster;

public:
   NB_TYPE_CASTER( ComplexType, const_name( "complex" ) );

   /**
    * Conversion from Python to C++: convert a PyObject into a TNL::Arithmetics::Complex
    * instance or return false upon failure.
    */
   bool
   from_python( handle src, std::uint8_t flags, cleanup_list* cleanup )
   {
      if( ! _caster.from_python( src, flags, cleanup ) )
         return false;
      value = static_cast< std::complex< T >& >( _caster );
      return true;
   }

   /**
    * Conversion from C++ to Python: convert an TNL::Arithmetics::Complex
    * instance into a Python object.
    */
   static handle
   from_cpp( const ComplexType& src, rv_policy policy, cleanup_list* cleanup )
   {
      const std::complex< T > c( src.real(), src.imag() );
      return StdComplexCaster::from_cpp( c, policy, cleanup );
   }
};

template< typename T >
struct dtype_traits< TNL::Arithmetics::Complex< T > > : public dtype_traits< std::complex< T > >
{};

}  // namespace detail
}  // namespace nanobind
