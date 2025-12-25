"""
Python package for computing CP decompositions of sparse and dense tensors
using GenTen.

GenTen is a tool providing Canonical Polyadic (CP) tensor decomposition
capabilities for sparse and dense tensors.  It provides data structures
for storing sparse and dense tensors, and several solver methods
for computing CP decompositions of those tensors.  It leverages Kokkos
for shared-memory parallelism on CPU and GPU architectures, and MPI for
distributed memory parallelism.

pygenten is not intended to be used on its own, but rather in conjunction
with the pyttb package, which provides a much larger set of tools for
analyzing and manipulating tensor data.
"""


# start delvewheel patch
def _delvewheel_patch_1_10_0():
    import ctypes
    import os
    import platform
    import sys
    libs_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, 'pygenten.libs'))
    is_conda_cpython = platform.python_implementation() == 'CPython' and (hasattr(ctypes.pythonapi, 'Anaconda_GetVersion') or 'packaged by conda-forge' in sys.version)
    if sys.version_info[:2] >= (3, 8) and not is_conda_cpython or sys.version_info[:2] >= (3, 10):
        if os.path.isdir(libs_dir):
            os.add_dll_directory(libs_dir)
    else:
        load_order_filepath = os.path.join(libs_dir, '.load-order-pygenten-0.1.4')
        if os.path.isfile(load_order_filepath):
            import ctypes.wintypes
            with open(os.path.join(libs_dir, '.load-order-pygenten-0.1.4')) as file:
                load_order = file.read().split()
            kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
            kernel32.LoadLibraryExW.restype = ctypes.wintypes.HMODULE
            kernel32.LoadLibraryExW.argtypes = ctypes.wintypes.LPCWSTR, ctypes.wintypes.HANDLE, ctypes.wintypes.DWORD
            for lib in load_order:
                lib_path = os.path.join(os.path.join(libs_dir, lib))
                if os.path.isfile(lib_path) and not kernel32.LoadLibraryExW(lib_path, None, 8):
                    raise OSError('Error loading {}; {}'.format(lib, ctypes.FormatError(ctypes.get_last_error())))


_delvewheel_patch_1_10_0()
del _delvewheel_patch_1_10_0
# end delvewheel patch

# Import DLLs on Windows since python 3.8+ doesn't do it automatically anymore
import os
if hasattr(os, 'add_dll_directory'):
  if 'GENTEN_DLL_PATH' in os.environ:
    gt_dlls = os.environ['GENTEN_DLL_PATH']
    for dll in gt_dlls.split(';'):
      if os.path.isdir(dll):
        os.add_dll_directory(dll)

from pygenten._pygenten import *
from pygenten.solvers import cp_als, cp_opt, gcp_opt, gcp_sgd, gcp_fed, online_gcp
from pygenten.utils import read_and_distribute_tensor, distribute_tensor
try:
    from pygenten.helpers import make_ttb_tensor, make_ttb_sptensor, make_ttb_ktensor, make_gt_tensor, make_gt_sptensor, make_gt_ktensor, ttb_tensor_supports_copy
except:
    pass
import atexit

# Initialize GenTen when module is loaded (it internally checks if GenTen
# has already been initialized).  This initializes Kokkos and MPI (if enabled).
did_initialize = _pygenten.initializeGenten()

# Register function to finalize GenTen at exit, but only if we initialized it
if did_initialize:
    atexit.register(_pygenten.finalizeGenten)