#pragma once

#include <pytnl/pytnl.h>

template< typename Mesh >
void
export_DistributedMesh( nb::module_& m, const char* name )
{
   auto mesh =  //
      nb::class_< Mesh >( m, name )
         .def( nb::init<>() )
         .def_static( "getMeshDimension", &Mesh::getMeshDimension )
         //.def("setCommunicationGroup", &Mesh::setCommunicationGroup)
         //.def("getCommunicationGroup", &Mesh::getCommunicationGroup)
         .def( "getLocalMesh", nb::overload_cast<>( &Mesh::getLocalMesh ), nb::rv_policy::reference_internal )
         .def( "setGhostLevels", &Mesh::setGhostLevels )
         .def( "getGhostLevels", &Mesh::getGhostLevels )
         .def(
            "getGlobalPointIndices",
            []( const Mesh& mesh ) -> typename Mesh::GlobalIndexArray const&
            {
               return mesh.template getGlobalIndices< 0 >();
            },
            nb::rv_policy::reference_internal )
         .def(
            "getGlobalCellIndices",
            []( const Mesh& mesh ) -> typename Mesh::GlobalIndexArray const&
            {
               return mesh.template getGlobalIndices< Mesh::getMeshDimension() >();
            },
            nb::rv_policy::reference_internal )
         .def(
            "vtkPointGhostTypes",
            []( const Mesh& mesh ) -> typename Mesh::VTKTypesArrayType const&
            {
               return mesh.vtkPointGhostTypes();
            },
            nb::rv_policy::reference_internal )
         .def(
            "vtkCellGhostTypes",
            []( const Mesh& mesh ) -> typename Mesh::VTKTypesArrayType const&
            {
               return mesh.vtkCellGhostTypes();
            },
            nb::rv_policy::reference_internal );
}
