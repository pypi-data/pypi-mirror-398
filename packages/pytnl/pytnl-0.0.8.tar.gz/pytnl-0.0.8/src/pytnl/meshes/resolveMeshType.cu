#include "resolveMeshType.h"

void
export_resolveMeshType( nb::module_& m )
{
   export_resolveMeshType< TNL::Devices::Cuda >( m );
}
