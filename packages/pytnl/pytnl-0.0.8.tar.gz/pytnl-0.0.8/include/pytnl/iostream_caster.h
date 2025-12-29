#pragma once

#include <memory>

#include <pytnl/3rdparty/cctbx/pystreambuf.h>

namespace nanobind {
namespace detail {

template<>
struct type_caster< std::istream >
{
protected:
   object obj;
   std::unique_ptr< pystreambuf::istream > value;

public:
   static constexpr auto Name = const_name( "typing.BinaryIO" );

   template< typename T_ >
   using Cast = movable_cast_t< T_ >;

   template< typename T_ >
   static constexpr bool
   can_cast()
   {
      return true;
   }

   template< typename T_, enable_if_t< std::is_same_v< std::remove_cv_t< T_ >, std::istream > > = 0 >
   static handle
   from_cpp( T_* p, rv_policy policy, cleanup_list* list )
   {
      if( ! p )
         return none().release();
      return from_cpp( *p, policy, list );
   }

   static handle
   from_cpp( const std::istream&& src, rv_policy policy, cleanup_list* cleanup )
   {
      return none().release();
   }

   bool
   from_python( handle src, std::uint8_t flags, cleanup_list* cleanup )
   {
      if( getattr( src, "read", none() ).is_none() ) {
         return false;
      }

      obj = borrow( src );
      value = std::unique_ptr< pystreambuf::istream >( new pystreambuf::istream( obj, 0 ) );

      return true;
   }

   explicit
   operator std::istream*()
   {
      return value.get();
   }

   explicit
   operator std::istream&()
   {
      return *value.get();
   }

   explicit
   operator std::istream&&()
   {
      return (std::istream&&) *value.get();
   }
};

template<>
struct type_caster< std::ostream >
{
protected:
   object obj;
   std::unique_ptr< pystreambuf::ostream > value;

public:
   static constexpr auto Name = const_name( "typing.BinaryIO" );

   template< typename T_ >
   using Cast = movable_cast_t< T_ >;

   template< typename T_ >
   static constexpr bool
   can_cast()
   {
      return true;
   }

   template< typename T_, enable_if_t< std::is_same_v< std::remove_cv_t< T_ >, std::ostream > > = 0 >
   static handle
   from_cpp( T_* p, rv_policy policy, cleanup_list* list )
   {
      if( ! p )
         return none().release();
      return from_cpp( *p, policy, list );
   }

   static handle
   from_cpp( const std::ostream&& src, rv_policy policy, cleanup_list* cleanup )
   {
      return none().release();
   }

   bool
   from_python( handle src, std::uint8_t flags, cleanup_list* cleanup )
   {
      if( getattr( src, "write", none() ).is_none() ) {
         return false;
      }

      obj = borrow( src );
      value = std::unique_ptr< pystreambuf::ostream >( new pystreambuf::ostream( obj, 0 ) );

      return true;
   }

   explicit
   operator std::ostream*()
   {
      return value.get();
   }

   explicit
   operator std::ostream&()
   {
      return *value.get();
   }

   explicit
   operator std::ostream&&()
   {
      return (std::ostream&&) *value.get();
   }
};

}  // namespace detail
}  // namespace nanobind
