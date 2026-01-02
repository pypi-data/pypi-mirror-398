"""
KuoEliassen - High-Performance Kuo-Eliassen Circulation Solver
Author: Qianye Su 
Email: suqianye2000@gmail.com
Created: 2025/11/12 12:05
"""


# start delvewheel patch
def _delvewheel_patch_1_11_2():
    import os
    if os.path.isdir(libs_dir := os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, 'kuoeliassen.libs'))):
        os.add_dll_directory(libs_dir)


_delvewheel_patch_1_11_2()
del _delvewheel_patch_1_11_2
# end delvewheel patch

from .core import solve_ke, solve_ke_LHS
from .xarray_interface import solve_ke_xarray, solve_ke_LHS_xarray
__version__ = '0.2.2'
__author__ = "Qianye Su"
__all__ = ["solve_ke", "solve_ke_xarray"]
