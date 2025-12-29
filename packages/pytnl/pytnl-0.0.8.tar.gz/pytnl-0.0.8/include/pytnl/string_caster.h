#pragma once

#include <nanobind/nanobind.h>

#include <TNL/String.h>

namespace nanobind {
namespace detail {

template<>
struct type_caster< TNL::String >
{
   using StdStringCaster = type_caster< std::string >;
   StdStringCaster _caster;

public:
   NB_TYPE_CASTER( TNL::String, const_name( "str" ) );

   /**
    * Conversion from Python to C++: convert a PyObject into a TNL::String
    * instance or return false upon failure.
    */
   bool
   from_python( handle src, std::uint8_t flags, cleanup_list* cleanup )
   {
      if( ! _caster.from_python( src, flags, cleanup ) )
         return false;
      const std::string& str = static_cast< std::string& >( _caster );
      value = TNL::String( str.c_str() );
      return true;
   }

   /**
    * Conversion from C++ to Python: convert an TNL::String instance into
    * a Python object.
    */
   static handle
   from_cpp( TNL::String&& src, rv_policy policy, cleanup_list* cleanup )
   {
      return StdStringCaster::from_cpp( src.getString(), policy, cleanup );
   }
};

}  // namespace detail
}  // namespace nanobind
