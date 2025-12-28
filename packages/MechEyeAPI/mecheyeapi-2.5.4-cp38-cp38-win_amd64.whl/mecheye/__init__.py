import ctypes
import importlib.util
import platform
import sys
import os
import os.path
from pathlib import Path


package_dir = Path(importlib.util.find_spec("mecheye").origin).parent
if (
    platform.system() == "Windows"
    and sys.version_info.major == 3
    and sys.version_info.minor >= 8
):
    # Starting with Python 3.8, the .dll search mechanism has changed.
    # WinDLL has anew argument "winmode",
    # https://docs.python.org/3.8/library/ctypes.html
    # and it turns out that we MUST import the pybind11 generated module
    # with "winmode=0". After doing this, the following import statement
    # picks this up since it's already imported, and things work as intended.
    #
    # The winmode parameter is used on Windows to specify how the library is
    # loaded (since mode is ignored). It takes any value that is valid for the
    # Win32 API LoadLibraryEx flags parameter. When omitted, the default is to
    # use the flags that result in the most secure DLL load to avoiding issues
    # such as DLL hijacking. Passing winmode=0 passes 0 as dwFlags to
    # LoadLibraryExA:
    # https://docs.microsoft.com/en-us/windows/win32/api/libloaderapi/nf-libloaderapi-loadlibraryexa

    ctypes.PyDLL(str(list(package_dir.glob("MechEyeApi.dll"))[0]))

    pyd_name = "*.pyd"
    pyd_files = list(package_dir.glob(pyd_name))
    for pyd_file in pyd_files:
        ctypes.PyDLL(str(pyd_file), winmode=0)
elif (platform.system() != "Windows"):
    ctypes.PyDLL(str(list(package_dir.glob("libMechEyeApi.so"))[0]))
