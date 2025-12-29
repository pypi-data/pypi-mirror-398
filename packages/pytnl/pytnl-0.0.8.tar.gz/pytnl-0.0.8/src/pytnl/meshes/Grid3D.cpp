#include "Grid.h"

void
export_Grid3D( nb::module_& m )
{
   export_Grid< Grid_3_host >( m, "Grid_3" );
}
