#pragma once

#include <pytnl/pytnl.h>

#include <TNL/Backend.h>
#include <TNL/Allocators/CudaHost.h>
#include <TNL/Allocators/CudaManaged.h>
#include <TNL/TypeTraits.h>

template< typename ArrayType >
auto
dlpack_device()
{
   using ValueType = typename ArrayType::ValueType;
   using DeviceType = typename ArrayType::DeviceType;

   if constexpr( TNL::IsViewType< ArrayType >::value ) {
      // FIXME: ArrayView does not have AllocatorType so we can check only DeviceType
      if constexpr( std::is_same_v< DeviceType, TNL::Devices::Cuda > )
         // FIXME: DLPack supports switching CUDA devices but TNL does not
         return std::make_pair( nb::device::cuda::value, TNL::Backend::getDevice() );
      else
         return std::make_pair( nb::device::cpu::value, 0 );
   }
   else {
      using AllocatorType = typename ArrayType::AllocatorType;

      if constexpr( std::is_same_v< AllocatorType, TNL::Allocators::Cuda< ValueType > > )
         // FIXME: DLPack supports switching CUDA devices but TNL does not
         return std::make_pair( nb::device::cuda::value, TNL::Backend::getDevice() );
      else if constexpr( std::is_same_v< AllocatorType, TNL::Allocators::CudaHost< ValueType > > )
         // FIXME: DLPack supports switching CUDA devices but TNL does not
         return std::make_pair( nb::device::cuda_host::value, TNL::Backend::getDevice() );
      else if constexpr( std::is_same_v< AllocatorType, TNL::Allocators::CudaManaged< ValueType > > )
         // FIXME: DLPack supports switching CUDA devices but TNL does not
         return std::make_pair( nb::device::cuda_managed::value, TNL::Backend::getDevice() );
      else
         return std::make_pair( nb::device::cpu::value, 0 );
   }
}
