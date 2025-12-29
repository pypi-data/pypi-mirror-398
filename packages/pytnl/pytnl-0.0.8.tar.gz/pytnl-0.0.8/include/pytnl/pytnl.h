#pragma once

// NOTE: This header file should be included by every .cpp file using PyTNL

#include <nanobind/nanobind.h>
#include <nanobind/ndarray.h>
#include <nanobind/operators.h>
#include <nanobind/make_iterator.h>

// Common type casters for STL classes (note: must be registered for each object file)
#include <nanobind/stl/array.h>
#include <nanobind/stl/complex.h>
#include <nanobind/stl/filesystem.h>
#include <nanobind/stl/optional.h>
#include <nanobind/stl/pair.h>
#include <nanobind/stl/shared_ptr.h>
#include <nanobind/stl/string.h>
#include <nanobind/stl/string_view.h>
#include <nanobind/stl/tuple.h>
#include <nanobind/stl/unique_ptr.h>
#include <nanobind/stl/variant.h>
#include <nanobind/stl/vector.h>

// Custom type casters for PyTNL (note: must be registered for each object file)
#include <pytnl/iostream_caster.h>
#include <pytnl/string_caster.h>
#include <pytnl/SizesHolder_caster.h>

// Common namespace alias
namespace nb = nanobind;
using namespace nanobind::literals;

// Header with type aliases for TNL data structures used throughout PyTNL
#include <pytnl/typedefs.h>

/* Reimplementation of nb::init but without list-initialization of the class,
 * which is not suitable for us due to using constructors with the
 * std::initializer_list parameter.
 *
 * Bug report: https://github.com/wjakob/nanobind/issues/1074
 */
template< typename... Args >
struct my_init : nb::def_visitor< my_init< Args... > >
{
   template< typename T, typename... Ts >
   friend class nb::class_;

   NB_INLINE
   my_init() {}

private:
   template< typename Class, typename... Extra >
   NB_INLINE static void
   execute( Class& cl, const Extra&... extra )
   {
      using Type = typename Class::Type;
      using Alias = typename Class::Alias;
      cl.def(
         "__init__",
         []( nb::pointer_and_handle< Type > v, Args... args )
         {
            if constexpr( ! std::is_same_v< Type, Alias > && std::is_constructible_v< Type, Args... > ) {
               if( ! nb::detail::nb_inst_python_derived( v.h.ptr() ) ) {
                  new( v.p ) Type( (nb::detail::forward_t< Args >) args... );
                  return;
               }
            }
            new( (void*) v.p ) Alias( (nb::detail::forward_t< Args >) args... );
         },
         extra... );
   }
};
