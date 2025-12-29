#include <pytnl/exceptions.h>
#include <pytnl/pytnl.h>

#include <TNL/Algorithms/Segments/CSR.h>
#include <TNL/Algorithms/Segments/Ellpack.h>
#include <TNL/Algorithms/Segments/SlicedEllpack.h>
#include <TNL/Matrices/SparseMatrix.h>
#include <TNL/Matrices/SparseOperations.h>

#include "SparseMatrix.h"

template< typename Device, typename Index, typename IndexAllocator >
using CSR = TNL::Algorithms::Segments::CSR< Device, Index, IndexAllocator >;
template< typename Device, typename Index, typename IndexAllocator >
using Ellpack = TNL::Algorithms::Segments::Ellpack< Device, Index, IndexAllocator >;
template< typename Device, typename Index, typename IndexAllocator >
using SlicedEllpack = TNL::Algorithms::Segments::SlicedEllpack< Device, Index, IndexAllocator >;

using CSR_cuda = TNL::Matrices::SparseMatrix< RealType, TNL::Devices::Cuda, IndexType, TNL::Matrices::GeneralMatrix, CSR >;
using E_cuda = TNL::Matrices::SparseMatrix< RealType, TNL::Devices::Cuda, IndexType, TNL::Matrices::GeneralMatrix, Ellpack >;
using SE_cuda =
   TNL::Matrices::SparseMatrix< RealType, TNL::Devices::Cuda, IndexType, TNL::Matrices::GeneralMatrix, SlicedEllpack >;

void
export_SparseMatrices( nb::module_& m )
{
   export_Matrix< CSR_cuda >( m, "CSR" );
   export_Matrix< E_cuda >( m, "Ellpack" );
   export_Matrix< SE_cuda >( m, "SlicedEllpack" );

   // NOTE: all exported formats (CSR, Ellpack, SlicedEllpack) use the same
   // SegmentView, so the RowView and ConstRowView are also the same types in all
   // three formats
   export_RowView< typename CSR_cuda::RowView >( m, "SparseMatrixRowView" );
   export_RowView< typename CSR_cuda::ConstRowView >( m, "SparseMatrixConstRowView" );

   m.def( "copySparseMatrix", &TNL::Matrices::copySparseMatrix< CSR_cuda, E_cuda > );
   m.def( "copySparseMatrix", &TNL::Matrices::copySparseMatrix< E_cuda, CSR_cuda > );
   m.def( "copySparseMatrix", &TNL::Matrices::copySparseMatrix< CSR_cuda, SE_cuda > );
   m.def( "copySparseMatrix", &TNL::Matrices::copySparseMatrix< SE_cuda, CSR_cuda > );
   m.def( "copySparseMatrix", &TNL::Matrices::copySparseMatrix< E_cuda, SE_cuda > );
   m.def( "copySparseMatrix", &TNL::Matrices::copySparseMatrix< SE_cuda, E_cuda > );
}

// Python module definition
NB_MODULE( matrices_cuda, m )
{
   register_exceptions( m );

   // import depending modules
   nb::module_::import_( "pytnl._containers_cuda" );

   export_SparseMatrices( m );
}
