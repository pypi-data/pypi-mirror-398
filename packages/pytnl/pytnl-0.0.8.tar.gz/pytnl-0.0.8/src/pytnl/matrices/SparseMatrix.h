#pragma once

#include <pytnl/pytnl.h>

#include <TNL/Containers/Vector.h>
#include <TNL/TypeTraits.h>

template< typename RowView, typename Scope >
void
export_RowView( Scope& s, const char* name )
{
   using RealType = typename RowView::RealType;
   using IndexType = typename RowView::IndexType;

   auto rowView = nb::class_< RowView >( s, name )
                     .def( "getSize", &RowView::getSize )
                     .def( "getRowIndex", &RowView::getRowIndex )
                     .def(
                        "getColumnIndex",
                        []( const RowView& row, IndexType localIdx ) -> const IndexType&
                        {
                           return row.getColumnIndex( localIdx );
                        },
                        nb::rv_policy::reference_internal )
                     .def(
                        "getValue",
                        []( const RowView& row, IndexType localIdx ) -> const RealType&
                        {
                           return row.getValue( localIdx );
                        },
                        nb::rv_policy::reference_internal )
                     .def( nb::self == nb::self, nb::sig( "def __eq__(self, arg: object, /) -> bool" ) )
      //      .def(nb::self_ns::str(nb::self_ns::self))
      ;

   if constexpr( ! std::is_const_v< typename RowView::RealType > ) {
      s.def( "setValue", &RowView::setValue )
         .def( "setColumnIndex", &RowView::setColumnIndex )
         .def( "setElement", &RowView::setElement );
   }
}

template< typename Segments, typename Enable = void >
struct export_CSR
{
   template< typename Scope >
   static void
   e( Scope& s )
   {}
};

template< typename Segments >
struct export_CSR< Segments, typename TNL::enable_if_type< decltype( Segments{}.getOffsets() ) >::type >
{
   template< typename Scope >
   static void
   e( Scope& s )
   {
      s.def(
         "getOffsets",
         []( const Segments& segments ) -> typename Segments::ConstOffsetsView
         {
            return segments.getOffsets();
         },
         nb::rv_policy::reference_internal );
   }
};

template< typename Segments, typename Scope >
void
export_Segments( Scope& s, const char* name )
{
   auto segments = nb::class_< Segments >( s, name )
                      .def( "getSegmentsCount", &Segments::getSegmentsCount )
                      .def( "getSegmentSize", &Segments::getSegmentSize )
                      .def( "getSize", &Segments::getSize )
                      .def( "getStorageSize", &Segments::getStorageSize )
                      .def( "getGlobalIndex", &Segments::getGlobalIndex )
      // FIXME: this does not compile
      //      .def(nb::self == nb::self)
      // TODO: forElements, forAllElements, forSegments, forAllSegments,
      // segmentsReduction, allReduction
      ;

   export_CSR< Segments >::e( segments );
}

template< typename Matrix >
void
export_Matrix( nb::module_& m, const char* name )
{
   using RealType = typename Matrix::RealType;
   using DeviceType = typename Matrix::DeviceType;
   using IndexType = typename Matrix::IndexType;

   using VectorType = TNL::Containers::Vector< RealType, DeviceType, IndexType >;
   using IndexVectorType = TNL::Containers::Vector< IndexType, DeviceType, IndexType >;

   auto matrix =
      nb::class_< Matrix >( m, name )
         .def( nb::init<>() )
         // File I/O
         .def_static( "getSerializationType", &Matrix::getSerializationType )
         .def( "save", &Matrix::save )
         .def( "load", &Matrix::load )

         .def( "print", &Matrix::print )
         .def( "__str__",
               []( Matrix& m )
               {
                  std::stringstream ss;
                  ss << m;
                  return ss.str();
               } )

         // Matrix
         .def( "setDimensions", nb::overload_cast< IndexType, IndexType >( &Matrix::setDimensions ) )
         // TODO: export for more types
         .def( "setLike",
               []( Matrix& matrix, const Matrix& other ) -> void
               {
                  matrix.setLike( other );
               } )
         .def( "getAllocatedElementsCount", &Matrix::getAllocatedElementsCount )
         .def( "getNonzeroElementsCount", &Matrix::getNonzeroElementsCount )
         .def( "reset", &Matrix::reset )
         .def( "getRows", &Matrix::getRows )
         .def( "getColumns", &Matrix::getColumns )
         // TODO: export for more types
         .def( nb::self == nb::self, nb::sig( "def __eq__(self, arg: object, /) -> bool" ) )
         .def( nb::self != nb::self, nb::sig( "def __ne__(self, arg: object, /) -> bool" ) )

         // SparseMatrix
         .def( "setRowCapacities", &Matrix::template setRowCapacities< IndexVectorType > )
         .def( "getRowCapacities", &Matrix::template getRowCapacities< IndexVectorType > )
         .def( "getCompressedRowLengths", &Matrix::template getCompressedRowLengths< IndexVectorType > )
         .def( "getRowCapacity", &Matrix::getRowCapacity )
         // TODO: implement bounds checking
         .def( "getRow",
               []( Matrix& matrix, IndexType rowIdx ) -> typename Matrix::RowView
               {
                  return matrix.getRow( rowIdx );
               } )
         // TODO: implement bounds checking
         .def( "setElement", &Matrix::setElement )
         // TODO: implement bounds checking
         .def( "addElement", &Matrix::addElement )
         // TODO: implement bounds checking
         .def( "getElement", &Matrix::getElement )
         // TODO: reduceRows, reduceAllRows, forElements, forAllElements,
         // forRows, forAllRows
         // TODO: export for more types
         .def( "vectorProduct", &Matrix::template vectorProduct< VectorType, VectorType > )
         // TODO: these two don't work
         //.def("addMatrix",           &Matrix::addMatrix)
         //.def("getTransposition",    &Matrix::getTransposition)
         // TODO: export for more types
         .def( "assign",
               []( Matrix& matrix, const Matrix& other ) -> Matrix&
               {
                  return matrix = other;
               } )

         // accessors for internal vectors
         .def( "getValues", nb::overload_cast<>( &Matrix::getValues ), nb::rv_policy::reference_internal )
         .def( "getColumnIndexes", nb::overload_cast<>( &Matrix::getColumnIndexes ), nb::rv_policy::reference_internal )
         .def( "getSegments", nb::overload_cast<>( &Matrix::getSegments ), nb::rv_policy::reference_internal );

   export_Segments< typename Matrix::SegmentsType >( matrix, "Segments" );
}
