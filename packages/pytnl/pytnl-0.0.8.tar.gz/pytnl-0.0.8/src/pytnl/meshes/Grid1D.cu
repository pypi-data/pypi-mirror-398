#include "Grid.h"

void
export_Grid1D( nb::module_& m )
{
   export_Grid< Grid_1_cuda >( m, "Grid_1" );
}
