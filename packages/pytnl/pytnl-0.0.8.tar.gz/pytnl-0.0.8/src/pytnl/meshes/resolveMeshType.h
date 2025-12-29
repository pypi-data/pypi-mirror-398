#pragma once

#include <pytnl/pytnl.h>

#include <TNL/Meshes/TypeResolver/resolveMeshType.h>

template< typename Device >
nb::typed< nb::tuple, TNL::Meshes::Readers::MeshReader, nb::type_object >
resolveMeshType( const std::string& file_name, const std::string& file_format = "auto" )
{
   // NOTE: We cannot get the reader with TNL::Meshes::resolveMeshType,
   // because it exposes it only *by value* and we can't make a copy of
   // that (because it is an abstract base class MeshReader). Thus we
   // need to reimplement and use TNL::Meshes::Readers::getMeshReader
   // which returns a std::shared_ptr which is ok.
   std::shared_ptr< TNL::Meshes::Readers::MeshReader > reader = TNL::Meshes::Readers::getMeshReader( file_name, file_format );
   if( reader == nullptr )
      return nb::make_tuple( nb::none(), nb::none() );

   reader->detectMesh();
   reader->forceRealType( TNL::getType< RealType >() );
   // FIXME: hardcoded type name
   reader->forceGlobalIndexType( "std::int64_t" );

   nb::object py_mesh = nb::none();
   auto wrapper = [ & ]( auto& reader, auto&& mesh ) -> bool
   {
      py_mesh = nb::cast( mesh );
      return true;
   };

   if( reader->getMeshType() == "Meshes::Grid" || reader->getMeshType() == "Meshes::DistributedGrid" )
      TNL::Meshes::GridTypeResolver< PyTNLConfigTag, Device >::run( *reader, wrapper );
   else if( reader->getMeshType() == "Meshes::Mesh" || reader->getMeshType() == "Meshes::DistributedMesh" )
      TNL::Meshes::MeshTypeResolver< PyTNLConfigTag, Device >::run( *reader, wrapper );
   else {
      throw std::runtime_error( "The mesh type " + reader->getMeshType() + " is not supported." );
   }

   nb::object py_reader = nb::cast( reader );
   return nb::make_tuple( std::move( py_reader ), std::move( py_mesh ) );
}

template< typename Device >
nb::typed< nb::tuple, TNL::Meshes::Readers::MeshReader, nb::type_object >
resolveAndLoadMesh( const std::string& file_name, const std::string& file_format = "auto" )
{
   nb::tuple reader_and_mesh = resolveMeshType< Device >( file_name, file_format );
   reader_and_mesh[ 0 ].attr( "loadMesh" )( reader_and_mesh[ 1 ] );
   return reader_and_mesh;
}

template< typename Device >
void
export_resolveMeshType( nb::module_& m )
{
   m.def( "resolveMeshType",
          resolveMeshType< Device >,
          nb::arg( "file_name" ),
          nb::kw_only(),
          nb::arg( "file_format" ) = "auto",
          "Returns a `(reader, mesh)` pair where `reader` is initialized "
          "with the given file name (using `getMeshReader`) and `mesh` is empty." );

   m.def( "resolveAndLoadMesh",
          resolveAndLoadMesh< Device >,
          nb::arg( "file_name" ),
          nb::kw_only(),
          nb::arg( "file_format" ) = "auto",
          "Returns a `(reader, mesh)` pair where `reader` is initialized "
          "with the given file name (using `getMeshReader`) and `mesh` contains "
          "the mesh loaded from the given file (using `reader.loadMesh(mesh)`)." );
}
