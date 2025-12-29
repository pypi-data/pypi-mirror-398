#include <pytnl/exceptions.h>
#include <pytnl/pytnl.h>

#include <pytnl/containers/Array.h>
#include <pytnl/containers/Vector.h>
#include <pytnl/containers/NDArray.h>
#include <pytnl/complex_caster.h>
#include <TNL/Arithmetics/Complex.h>

using namespace TNL::Containers;

template< typename T >
using _array = TNL::Containers::Array< T, TNL::Devices::Cuda, IndexType >;

template< typename T >
using _vector = TNL::Containers::Vector< T, TNL::Devices::Cuda, IndexType >;

template< int dim, typename T >
using _ndarray = NDArray< T,
                          make_sizes_holder< IndexType, dim >,
                          std::make_index_sequence< dim >,  // identity by default
                          TNL::Devices::Cuda,
                          IndexType,
                          make_sizes_holder< IndexType, dim >  // all overlaps are set at runtime
                          //ConstStaticSizesHolder< IndexType, dim, 0 >  // ConstStaticSizesHolder does not have Python bindings
                          >;

// Python module definition
NB_MODULE( _containers_cuda, m )
{
   register_exceptions( m );

   // import depending modules
   nb::module_::import_( "pytnl._containers" );

   // std::complex does not work with CUDA (even in C++20)
   using ComplexType = TNL::Arithmetics::Complex< RealType >;

   export_Array< _array< bool > >( m, "Array_bool" );
   export_Array< _array< IndexType > >( m, "Array_int" );
   export_Array< _array< RealType > >( m, "Array_float" );
   export_Array< _array< ComplexType > >( m, "Array_complex" );
   export_Vector< _array< IndexType >, _vector< IndexType > >( m, "Vector_int" );
   export_Vector< _array< RealType >, _vector< RealType > >( m, "Vector_float" );
   export_Vector< _array< ComplexType >, _vector< ComplexType > >( m, "Vector_complex" );

   export_NDArray< _ndarray< 1, IndexType > >( m, "NDArray_1_int" );
   export_NDArray< _ndarray< 2, IndexType > >( m, "NDArray_2_int" );
   export_NDArray< _ndarray< 3, IndexType > >( m, "NDArray_3_int" );
   export_NDArray< _ndarray< 1, RealType > >( m, "NDArray_1_float" );
   export_NDArray< _ndarray< 2, RealType > >( m, "NDArray_2_float" );
   export_NDArray< _ndarray< 3, RealType > >( m, "NDArray_3_float" );
   export_NDArray< _ndarray< 1, ComplexType > >( m, "NDArray_1_complex" );
   export_NDArray< _ndarray< 2, ComplexType > >( m, "NDArray_2_complex" );
   export_NDArray< _ndarray< 3, ComplexType > >( m, "NDArray_3_complex" );
}
