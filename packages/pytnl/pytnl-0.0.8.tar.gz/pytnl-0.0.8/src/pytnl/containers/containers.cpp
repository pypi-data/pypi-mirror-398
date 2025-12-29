#include <pytnl/exceptions.h>
#include <pytnl/pytnl.h>

#include <pytnl/containers/Array.h>
#include <pytnl/containers/Vector.h>
#include <pytnl/containers/StaticVector.h>
#include <pytnl/containers/NDArray.h>

using namespace TNL::Containers;

template< typename T >
using _array = TNL::Containers::Array< T, TNL::Devices::Host, IndexType >;

template< typename T >
using _vector = TNL::Containers::Vector< T, TNL::Devices::Host, IndexType >;

template< std::size_t dim >
using _ndindexer =
   NDArrayIndexer< make_sizes_holder< IndexType, dim >,  // all sizes are set at runtime
                   make_sizes_holder< IndexType, dim >,  // all strides are set at runtime
                   make_sizes_holder< IndexType, dim >   // all overlaps are set at runtime
                   //ConstStaticSizesHolder< IndexType, dim, 0 >  // ConstStaticSizesHolder does not have Python bindings
                   >;

template< int dim, typename T >
using _ndarray = NDArray< T,
                          make_sizes_holder< IndexType, dim >,
                          std::make_index_sequence< dim >,  // identity by default
                          TNL::Devices::Host,
                          IndexType,
                          make_sizes_holder< IndexType, dim >  // all overlaps are set at runtime
                          //ConstStaticSizesHolder< IndexType, dim, 0 >  // ConstStaticSizesHolder does not have Python bindings
                          >;

// Python module definition
NB_MODULE( _containers, m )
{
   register_exceptions( m );

   export_Array< _array< bool > >( m, "Array_bool" );
   export_Array< _array< IndexType > >( m, "Array_int" );
   export_Array< _array< RealType > >( m, "Array_float" );
   export_Array< _array< ComplexType > >( m, "Array_complex" );
   export_Vector< _array< IndexType >, _vector< IndexType > >( m, "Vector_int" );
   export_Vector< _array< RealType >, _vector< RealType > >( m, "Vector_float" );
   export_Vector< _array< ComplexType >, _vector< ComplexType > >( m, "Vector_complex" );

   export_StaticVector< StaticVector< 1, IndexType > >( m, "StaticVector_1_int" );
   export_StaticVector< StaticVector< 2, IndexType > >( m, "StaticVector_2_int" );
   export_StaticVector< StaticVector< 3, IndexType > >( m, "StaticVector_3_int" );
   export_StaticVector< StaticVector< 1, RealType > >( m, "StaticVector_1_float" );
   export_StaticVector< StaticVector< 2, RealType > >( m, "StaticVector_2_float" );
   export_StaticVector< StaticVector< 3, RealType > >( m, "StaticVector_3_float" );
   export_StaticVector< StaticVector< 1, ComplexType > >( m, "StaticVector_1_complex" );
   export_StaticVector< StaticVector< 2, ComplexType > >( m, "StaticVector_2_complex" );
   export_StaticVector< StaticVector< 3, ComplexType > >( m, "StaticVector_3_complex" );

   export_NDArrayIndexer< _ndindexer< 1 > >( m, "NDArrayIndexer_1" );
   export_NDArrayIndexer< _ndindexer< 2 > >( m, "NDArrayIndexer_2" );
   export_NDArrayIndexer< _ndindexer< 3 > >( m, "NDArrayIndexer_3" );

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
