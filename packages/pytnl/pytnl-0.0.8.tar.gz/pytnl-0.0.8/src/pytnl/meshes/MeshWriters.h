#include <pytnl/pytnl.h>
#include <pytnl/meshes/MeshWriters.h>

#include <TNL/Meshes/Writers/VTIWriter.h>
#include <TNL/Meshes/Writers/VTKWriter.h>
#include <TNL/Meshes/Writers/VTUWriter.h>

template< typename Writer, TNL::Meshes::VTK::FileFormat default_format >
void
export_MeshWriter( nb::module_& m, const char* name )
{
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
      .def( "writeVertices", &Writer::template writeEntities< 0 > )
      .def( "writeCells", &Writer::template writeEntities<> )
      // we use the VariantVector from MeshReader because we already have a
      // caster for it
      .def(
         "writePointData",
         []( PythonWriter& writer, const VariantVector& array, std::string name, int numberOfComponents = 1 )
         {
            using std::visit;
            visit(
               [ & ]( auto&& array )
               {
                  // we need a view for the std::vector
                  using vector_t = std::decay_t< decltype( array ) >;
                  using view_t = TNL::Containers::
                     ArrayView< std::add_const_t< typename vector_t::value_type >, TNL::Devices::Host, std::int64_t >;
                  view_t view( array.data(), array.size() );
                  writer.writePointData( view, name, numberOfComponents );
               },
               array );
         },
         nb::arg( "array" ),
         nb::arg( "name" ),
         nb::arg( "numberOfComponents" ) = 1 )
      .def(
         "writeCellData",
         []( PythonWriter& writer, const VariantVector& array, std::string name, int numberOfComponents = 1 )
         {
            using std::visit;
            visit(
               [ & ]( auto&& array )
               {
                  // we need a view for the std::vector
                  using vector_t = std::decay_t< decltype( array ) >;
                  using view_t = TNL::Containers::
                     ArrayView< std::add_const_t< typename vector_t::value_type >, TNL::Devices::Host, std::int64_t >;
                  view_t view( array.data(), array.size() );
                  writer.writeCellData( view, name, numberOfComponents );
               },
               array );
         },
         nb::arg( "array" ),
         nb::arg( "name" ),
         nb::arg( "numberOfComponents" ) = 1 )
      .def(
         "writeDataArray",
         []( PythonWriter& writer, const VariantVector& array, std::string name, int numberOfComponents = 1 )
         {
            using std::visit;
            visit(
               [ & ]( auto&& array )
               {
                  // we need a view for the std::vector
                  using vector_t = std::decay_t< decltype( array ) >;
                  using view_t = TNL::Containers::
                     ArrayView< std::add_const_t< typename vector_t::value_type >, TNL::Devices::Host, std::int64_t >;
                  view_t view( array.data(), array.size() );
                  writer.writeDataArray( view, name, numberOfComponents );
               },
               array );
         },
         nb::arg( "array" ),
         nb::arg( "name" ),
         nb::arg( "numberOfComponents" ) = 1 );
}
