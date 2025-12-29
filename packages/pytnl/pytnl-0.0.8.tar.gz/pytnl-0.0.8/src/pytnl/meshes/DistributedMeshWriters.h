#include <pytnl/pytnl.h>
#include <pytnl/meshes/MeshWriters.h>

#include <TNL/Meshes/Writers/PVTUWriter.h>

template< template< typename > class WriterTemplate, typename LocalMesh, TNL::Meshes::VTK::FileFormat default_format >
void
export_DistributedMeshWriter( nb::module_& m, const char* name )
{
   using Writer = WriterTemplate< LocalMesh >;
   using Mesh = TNL::Meshes::DistributedMeshes::DistributedMesh< LocalMesh >;

   // We cannot use MeshReader::VariantVector for Python bindings, because its
   // variants are std::vector<T> for T in std::int8_t, std::uint8_t,
   // std::int16_t, std::uint16_t, std::int32_t, std::uint32_t, std::int64_t,
   // std::uint64_t, float and double. Python types do not map nicely to C++
   // types, integers even have unlimited precision, pybind11 even checks if
   // given Python value fits into the C++ type when selecting the alternative
   // for a scalar type, and for containers like std::vector it merely selects
   // the first possible type. For reference, see
   // https://github.com/pybind/pybind11/issues/1625#issuecomment-723499161
   using VariantVector = std::variant< std::vector< IndexType >, std::vector< RealType > >;

   // Binding to Writer directly is not possible, because the writer has a
   // std::ostream attribute which would reference the streambuf created by the
   // type caster from the Python file-like object. However, the streambuf would
   // be destroyed as soon as the writer is constructed and control returned to
   // Python, so the following invocations would use an invalid object and
   // segfault. To solve this, we use a transient wrapper struct PyWriter which
   // holds the streambuf in its own ostream attribute and is initialized by a
   // nb::object to avoid type casting.
   using PythonWriter = PyMeshWriter< Writer, default_format >;
   nb::class_< PythonWriter >( m, name )
      .def( nb::init< nb::object, TNL::Meshes::VTK::FileFormat >(),
            nb::keep_alive< 1, 2 >(),
            nb::arg( "stream" ),
            nb::kw_only(),
            nb::arg( "format" ) = default_format )
      .def( "writeMetadata", &Writer::writeMetadata, nb::kw_only(), nb::arg( "cycle" ) = -1, nb::arg( "time" ) = -1 )
      .def( "writeVertices",
            static_cast< void ( Writer::* )( const Mesh& ) >( &Writer::template writeEntities< 0 > ),
            nb::arg( "distributedMesh" ) )
      .def( "writeVertices",
            static_cast< void ( Writer::* )( const LocalMesh&, unsigned, unsigned ) >( &Writer::template writeEntities< 0 > ),
            nb::arg( "localMesh" ),
            nb::arg( "GhostLevel" ) = 0,
            nb::arg( "MinCommonVertices" ) = 0 )
      .def( "writeCells",
            static_cast< void ( Writer::* )( const Mesh& ) >( &Writer::template writeEntities<> ),
            nb::arg( "distributedMesh" ) )
      .def( "writeCells",
            static_cast< void ( Writer::* )( const LocalMesh&, unsigned, unsigned ) >( &Writer::template writeEntities<> ),
            nb::arg( "localMesh" ),
            nb::arg( "GhostLevel" ) = 0,
            nb::arg( "MinCommonVertices" ) = 0 )
      // INCONSISTENCY: the C++ methods writePPointData, writePCellData,
      // writePDataArray do not take the whole array as parameter, only the
      // ValueType as a template parameter. Since this does not map nicely to
      // Python, we pass the whole array just like in the VTKWriter and
      // VTUWriter classes. we use the VariantVector from MeshReader because we
      // already have a caster for it
      .def(
         "writePPointData",
         []( PythonWriter& writer, const VariantVector& array, std::string name, int numberOfComponents = 1 )
         {
            using std::visit;
            visit(
               [ & ]( auto&& array )
               {
                  using value_type = typename std::decay_t< decltype( array ) >::value_type;
                  writer.template writePPointData< value_type >( name, numberOfComponents );
               },
               array );
         },
         nb::arg( "array" ),
         nb::arg( "name" ),
         nb::arg( "numberOfComponents" ) = 1 )
      .def(
         "writePCellData",
         []( PythonWriter& writer, const VariantVector& array, std::string name, int numberOfComponents = 1 )
         {
            using std::visit;
            visit(
               [ & ]( auto&& array )
               {
                  using value_type = typename std::decay_t< decltype( array ) >::value_type;
                  writer.template writePCellData< value_type >( name, numberOfComponents );
               },
               array );
         },
         nb::arg( "array" ),
         nb::arg( "name" ),
         nb::arg( "numberOfComponents" ) = 1 )
      .def(
         "writePDataArray",
         []( PythonWriter& writer, const VariantVector& array, std::string name, int numberOfComponents = 1 )
         {
            using std::visit;
            visit(
               [ & ]( auto&& array )
               {
                  using value_type = typename std::decay_t< decltype( array ) >::value_type;
                  writer.template writePDataArray< value_type >( name, numberOfComponents );
               },
               array );
         },
         nb::arg( "array" ),
         nb::arg( "name" ),
         nb::arg( "numberOfComponents" ) = 1 )
      // NOTE: only the overload intended for sequential writing is exported,
      // because we don't have type casters for MPI_Comm (ideally, it would be
      // compatible with the mpi4py objects)
      .def( "addPiece",
            static_cast< std::string ( Writer::* )( const std::string&, unsigned ) >( &Writer::addPiece ),
            nb::arg( "mainFileName" ),
            nb::arg( "subdomainIndex" ) );
}
