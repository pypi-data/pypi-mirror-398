#include <nanobind/trampoline.h>

#include <TNL/Meshes/Readers/MeshReader.h>
#include <TNL/Meshes/Readers/XMLVTK.h>

// trampoline classes needed for overriding virtual methods
// https://nanobind.readthedocs.io/en/latest/classes.html#trampolines

class PyMeshReader : public TNL::Meshes::Readers::MeshReader
{
   using Parent = TNL::Meshes::Readers::MeshReader;

public:
   NB_TRAMPOLINE( Parent, 2 );

   // trampolines (one for each virtual method)
   void
   reset() override
   {
      NB_OVERRIDE_PURE( reset );
   }

   void
   detectMesh() override
   {
      NB_OVERRIDE_PURE( detectMesh );
   }
};

class PyXMLVTK : public TNL::Meshes::Readers::XMLVTK
{
   using Parent = TNL::Meshes::Readers::XMLVTK;

public:
   NB_TRAMPOLINE( Parent, 2 );

   // trampolines (one for each virtual method)
   void
   reset() override
   {
      NB_OVERRIDE_PURE( reset );
   }

   void
   detectMesh() override
   {
      NB_OVERRIDE_PURE( detectMesh );
   }
};
