class AbstractDevice:
    """
    A base class for all device types supported by PyTNL.
    It does not have a direct counter-part in the C++ code in TNL.
    """


class Host(AbstractDevice):
    """
    Class for the *host* device in TNL. It corresponds to the
    `TNL::Devices::Host` class in C++.

    Same as in TNL, the purpose of this class is to select data structures and
    algorithms compiled for the *host system*, i.e. CPU execution.
    """


class Cuda(AbstractDevice):
    """
    Class for the *CUDA* device in TNL. It corresponds to the
    `TNL::Devices::Cuda` class in C++.

    Same as in TNL, the purpose of this class is to select data structures and
    algorithms compiled with GPU acceleration using CUDA.
    """
