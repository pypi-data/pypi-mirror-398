#include "Grid.h"

void
export_Grid1D( nb::module_& m )
{
   export_Grid< Grid_1_host >( m, "Grid_1" );
}
