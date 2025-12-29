#include "Grid.h"

void
export_Grid2D( nb::module_& m )
{
   export_Grid< Grid_2_cuda >( m, "Grid_2" );
}
