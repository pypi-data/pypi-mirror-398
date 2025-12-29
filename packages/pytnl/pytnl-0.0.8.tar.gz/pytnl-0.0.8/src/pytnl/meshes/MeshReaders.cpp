#include <pytnl/pytnl.h>
#include <pytnl/meshes/MeshReaders.h>

#include <TNL/Meshes/Readers/getMeshReader.h>

inline bool
ends_with( const std::string& value, const std::string& ending )
{
   if( ending.size() > value.size() )
      return false;
   return std::equal( ending.rbegin(), ending.rend(), value.rbegin() );
}

void
export_MeshReaders( nb::module_& m )
{
   using MeshReader = TNL::Meshes::Readers::MeshReader;
   using XMLVTK = TNL::Meshes::Readers::XMLVTK;

   // bindings for the MeshReader::loadMesh method are in the module itself
   // to make it easily extensible by overloading
   m.def( "loadMesh", &MeshReader::template loadMesh< Grid_1_host > );
   m.def( "loadMesh", &MeshReader::template loadMesh< Grid_2_host > );
   m.def( "loadMesh", &MeshReader::template loadMesh< Grid_3_host > );
   m.def( "loadMesh", &MeshReader::template loadMesh< MeshOfEdges_host > );
   m.def( "loadMesh", &MeshReader::template loadMesh< MeshOfTriangles_host > );
   m.def( "loadMesh", &MeshReader::template loadMesh< MeshOfQuadrangles_host > );
   m.def( "loadMesh", &MeshReader::template loadMesh< MeshOfTetrahedrons_host > );
   m.def( "loadMesh", &MeshReader::template loadMesh< MeshOfHexahedrons_host > );
   m.def( "loadMesh", &MeshReader::template loadMesh< MeshOfPolygons_host > );
   m.def( "loadMesh", &MeshReader::template loadMesh< MeshOfPolyhedrons_host > );

   // base class with trampolines for virtual methods
   nb::class_< MeshReader, PyMeshReader >( m, "MeshReader" )
      .def( nb::init< std::string >() )
      // bindings against the actual class, NOT the trampoline
      .def( "reset", &MeshReader::reset )
      .def( "detectMesh", &MeshReader::detectMesh )
      .def( "loadMesh",
            []( nb::object self, nb::object mesh ) -> void
            {
               // call the loadMesh function from the same Python module that contains the mesh
               const auto module_name = nb::cast< std::string >( mesh.attr( "__class__" ).attr( "__module__" ) );
               nb::object module = nb::module_::import_( module_name.c_str() );
               nb::object loadMesh = module.attr( "loadMesh" );
               loadMesh( self, mesh );
            } )
      .def( "readPointData", &MeshReader::readPointData )
      .def( "readCellData", &MeshReader::readCellData );

   nb::class_< TNL::Meshes::Readers::VTKReader, MeshReader >( m, "VTKReader" ).def( nb::init< std::string >() );

   // base class for VTUReader, VTIReader and PVTUReader
   nb::class_< XMLVTK, PyXMLVTK, MeshReader >( m, "XMLVTK" ).def( nb::init< std::string >() );

   nb::class_< TNL::Meshes::Readers::VTUReader, XMLVTK >( m, "VTUReader" ).def( nb::init< std::string >() );

   nb::class_< TNL::Meshes::Readers::VTIReader, XMLVTK >( m, "VTIReader" ).def( nb::init< std::string >() );

   nb::class_< TNL::Meshes::Readers::PVTUReader, XMLVTK >( m, "PVTUReader" ).def( nb::init< std::string >() );

   auto getMeshReader =  //
      m.def( "getMeshReader",
             TNL::Meshes::Readers::getMeshReader,
             nb::arg( "file_name" ),
             nb::kw_only(),
             nb::arg( "file_format" ) = "auto",
             "Returns the MeshReader instance for given file based on file extension "
             "(does not call `reader.detectMesh` so it succeeds even for invalid file)" );
}
