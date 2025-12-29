#pragma once

#include <TNL/TypeTraits.h>
#include <pytnl/pytnl.h>

template< typename VectorType, typename... Args >
void
def_vector_operators( nb::class_< VectorType, Args... >& vector )
{
   using RealType = typename VectorType::RealType;

   vector
      // Comparison operators (Vector OP Vector)
      .def(
         "__eq__",
         []( const VectorType& self, const VectorType& other )
         {
            return self == other;
         },
         nb::sig( "def __eq__(self, arg: object, /) -> bool" ),
         nb::is_operator() )
      .def(
         "__ne__",
         []( const VectorType& self, const VectorType& other )
         {
            return self != other;
         },
         nb::sig( "def __ne__(self, arg: object, /) -> bool" ),
         nb::is_operator() );

   if constexpr( TNL::IsScalarType< RealType >::value && ! TNL::is_complex_v< RealType > ) {
      vector
         .def(
            "__lt__",
            []( const VectorType& self, const VectorType& other )
            {
               return self < other;
            },
            nb::is_operator() )
         .def(
            "__le__",
            []( const VectorType& self, const VectorType& other )
            {
               return self <= other;
            },
            nb::is_operator() )
         .def(
            "__gt__",
            []( const VectorType& self, const VectorType& other )
            {
               return self > other;
            },
            nb::is_operator() )
         .def(
            "__ge__",
            []( const VectorType& self, const VectorType& other )
            {
               return self >= other;
            },
            nb::is_operator() );
   }

   if constexpr( TNL::IsScalarType< RealType >::value ) {
      vector
         // In-place arithmetic operators (Vector OP Vector)
         .def(
            "__iadd__",
            []( VectorType& self, const VectorType& other ) -> VectorType&
            {
               self += other;
               return self;
            },
            nb::is_operator() )
         .def(
            "__isub__",
            []( VectorType& self, const VectorType& other ) -> VectorType&
            {
               self -= other;
               return self;
            },
            nb::is_operator() )
         .def(
            "__imul__",
            []( VectorType& self, const VectorType& other ) -> VectorType&
            {
               self *= other;
               return self;
            },
            nb::is_operator() )
         .def(
            "__idiv__",
            []( VectorType& self, const VectorType& other ) -> VectorType&
            {
               self /= other;
               return self;
            },
            nb::is_operator() )

         // In-place arithmetic operators (Vector OP Scalar)
         .def(
            "__iadd__",
            []( VectorType& self, RealType scalar ) -> VectorType&
            {
               self += scalar;
               return self;
            },
            nb::is_operator() )
         .def(
            "__isub__",
            []( VectorType& self, RealType scalar ) -> VectorType&
            {
               self -= scalar;
               return self;
            },
            nb::is_operator() )
         .def(
            "__imul__",
            []( VectorType& self, RealType scalar ) -> VectorType&
            {
               self *= scalar;
               return self;
            },
            nb::is_operator() )
         .def(
            "__idiv__",
            []( VectorType& self, RealType scalar ) -> VectorType&
            {
               self /= scalar;
               return self;
            },
            nb::is_operator() )

         // Binary arithmetic operators (Vector OP Vector)
         .def(
            "__add__",
            []( const VectorType& self, const VectorType& other )
            {
               return VectorType( self + other );
            },
            nb::is_operator() )
         .def(
            "__sub__",
            []( const VectorType& self, const VectorType& other )
            {
               return VectorType( self - other );
            },
            nb::is_operator() )
         .def(
            "__mul__",
            []( const VectorType& self, const VectorType& other )
            {
               return VectorType( self * other );
            },
            nb::is_operator() )
         .def(
            "__truediv__",
            []( const VectorType& self, const VectorType& other )
            {
               return VectorType( self / other );
            },
            nb::is_operator() )

         // Binary arithmetic operators (Vector OP Scalar)
         .def(
            "__add__",
            []( const VectorType& self, RealType scalar )
            {
               return VectorType( self + scalar );
            },
            nb::is_operator() )
         .def(
            "__sub__",
            []( const VectorType& self, RealType scalar )
            {
               return VectorType( self - scalar );
            },
            nb::is_operator() )
         .def(
            "__mul__",
            []( const VectorType& self, RealType scalar )
            {
               return VectorType( self * scalar );
            },
            nb::is_operator() )
         .def(
            "__truediv__",
            []( const VectorType& self, RealType scalar )
            {
               return VectorType( self / scalar );
            },
            nb::is_operator() )

         // Reverse arithmetic operators (Scalar OP Vector)
         .def(
            "__radd__",
            []( const VectorType& self, RealType scalar )
            {
               return VectorType( scalar + self );
            },
            nb::is_operator() )
         .def(
            "__rsub__",
            []( const VectorType& self, RealType scalar )
            {
               return VectorType( scalar - self );
            },
            nb::is_operator() )
         .def(
            "__rmul__",
            []( const VectorType& self, RealType scalar )
            {
               return VectorType( scalar * self );
            },
            nb::is_operator() )
         .def(
            "__rtruediv__",
            []( const VectorType& self, RealType scalar )
            {
               return VectorType( scalar / self );
            },
            nb::is_operator() )

         // Unary Operators
         .def( "__pos__",
               []( const VectorType& self )
               {
                  return VectorType( +self );
               } )
         .def( "__neg__",
               []( const VectorType& self )
               {
                  return VectorType( -self );
               } );
   }

   // Additional operators defined only for integral value types
   if constexpr( std::is_integral_v< RealType > ) {
      vector
         // Modulo operators
         .def(
            "__mod__",
            []( const VectorType& self, const VectorType& other )
            {
               return VectorType( self % other );
            },
            nb::is_operator() )
         .def(
            "__mod__",
            []( const VectorType& self, RealType scalar )
            {
               return VectorType( self % scalar );
            },
            nb::is_operator() )
         .def(
            "__rmod__",
            []( const VectorType& self, const VectorType& other )
            {
               return VectorType( other % self );
            },
            nb::is_operator() )
         .def(
            "__rmod__",
            []( const VectorType& self, RealType scalar )
            {
               return VectorType( scalar % self );
            },
            nb::is_operator() )
         .def(
            "__imod__",
            []( VectorType& self, const VectorType& other ) -> VectorType&
            {
               self %= other;
               return self;
            },
            nb::is_operator() )
         .def(
            "__imod__",
            []( VectorType& self, RealType scalar ) -> VectorType&
            {
               self %= scalar;
               return self;
            },
            nb::is_operator() )

         // Bitwise operators
         .def(
            "__and__",
            []( const VectorType& self, const VectorType& other )
            {
               return VectorType( self & other );
            },
            nb::is_operator() )
         .def(
            "__and__",
            []( const VectorType& self, RealType scalar )
            {
               return VectorType( self & scalar );
            },
            nb::is_operator() )
         .def(
            "__rand__",
            []( const VectorType& self, RealType scalar )
            {
               return VectorType( scalar & self );
            },
            nb::is_operator() )

         .def(
            "__or__",
            []( const VectorType& self, const VectorType& other )
            {
               return VectorType( self | other );
            },
            nb::is_operator() )
         .def(
            "__or__",
            []( const VectorType& self, RealType scalar )
            {
               return VectorType( self | scalar );
            },
            nb::is_operator() )
         .def(
            "__ror__",
            []( const VectorType& self, RealType scalar )
            {
               return VectorType( scalar | self );
            },
            nb::is_operator() )

         .def(
            "__xor__",
            []( const VectorType& self, const VectorType& other )
            {
               return VectorType( self ^ other );
            },
            nb::is_operator() )
         .def(
            "__xor__",
            []( const VectorType& self, RealType scalar )
            {
               return VectorType( self ^ scalar );
            },
            nb::is_operator() )
         .def(
            "__rxor__",
            []( const VectorType& self, RealType scalar )
            {
               return VectorType( scalar ^ self );
            },
            nb::is_operator() )

         // Bitwise negation
         .def( "__invert__",
               []( const VectorType& self )
               {
                  return VectorType( ~self );
               } );
   }

   // While not operators, these functions are defined as expression templates
   // in TNL and also exposed via dunder methods in Python.
   vector.def( "__abs__",
               []( const VectorType& self )
               {
                  return VectorType( TNL::abs( self ) );
               } );
   if constexpr( TNL::IsScalarType< RealType >::value && ! TNL::is_complex_v< RealType > ) {
      vector  //
         .def( "__floor__",
               []( const VectorType& self )
               {
                  return VectorType( TNL::floor( self ) );
               } )
         .def( "__ceil__",
               []( const VectorType& self )
               {
                  return VectorType( TNL::ceil( self ) );
               } );
   }
}
