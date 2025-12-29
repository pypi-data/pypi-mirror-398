#pragma once

#include <stdexcept>

#include <nanobind/nanobind.h>

struct NotImplementedError : public std::runtime_error
{
   NotImplementedError( const char* msg )
   : std::runtime_error( msg )
   {}
};

static void
register_exceptions( nanobind::module_& m )
{
   // Translate C++ exceptions to native Python exceptions without creating new objects in the module
   // https://nanobind.readthedocs.io/en/latest/exceptions.html#handling-custom-exceptions
   nanobind::register_exception_translator(
      []( const std::exception_ptr& p, void* /* unused */ )
      {
         try {
            std::rethrow_exception( p );
         }
         // translate exceptions used in the bindings
         catch( const NotImplementedError& e ) {
            PyErr_SetString( PyExc_NotImplementedError, e.what() );
         }
      } );
}
