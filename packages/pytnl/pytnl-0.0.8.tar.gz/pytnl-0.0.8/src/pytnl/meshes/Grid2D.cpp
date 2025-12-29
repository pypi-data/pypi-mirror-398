#include "Grid.h"

void
export_Grid2D( nb::module_& m )
{
   export_Grid< Grid_2_host >( m, "Grid_2" );
}
