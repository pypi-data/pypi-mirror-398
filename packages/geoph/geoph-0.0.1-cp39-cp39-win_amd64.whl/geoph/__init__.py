from __future__ import annotations


# start delvewheel patch
def _delvewheel_patch_1_11_2():
    import ctypes
    import os
    import platform
    import sys
    libs_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, 'geoph.libs'))
    is_conda_cpython = platform.python_implementation() == 'CPython' and (hasattr(ctypes.pythonapi, 'Anaconda_GetVersion') or 'packaged by conda-forge' in sys.version)
    if sys.version_info[:2] >= (3, 8) and not is_conda_cpython or sys.version_info[:2] >= (3, 10):
        if os.path.isdir(libs_dir):
            os.add_dll_directory(libs_dir)
    else:
        load_order_filepath = os.path.join(libs_dir, '.load-order-geoph-0.0.1')
        if os.path.isfile(load_order_filepath):
            import ctypes.wintypes
            with open(os.path.join(libs_dir, '.load-order-geoph-0.0.1')) as file:
                load_order = file.read().split()
            kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
            kernel32.LoadLibraryExW.restype = ctypes.wintypes.HMODULE
            kernel32.LoadLibraryExW.argtypes = ctypes.wintypes.LPCWSTR, ctypes.wintypes.HANDLE, ctypes.wintypes.DWORD
            for lib in load_order:
                lib_path = os.path.join(os.path.join(libs_dir, lib))
                if os.path.isfile(lib_path) and not kernel32.LoadLibraryExW(lib_path, None, 8):
                    raise OSError('Error loading {}; {}'.format(lib, ctypes.FormatError(ctypes.get_last_error())))


_delvewheel_patch_1_11_2()
del _delvewheel_patch_1_11_2
# end delvewheel patch

from .geoph_impl import *

def delaunayRipsPersistenceDiagram(X, format:str='default') -> list[list[tuple[float, float]]] | list[tuple[int, tuple[float, float]]]:
    """
    Computes Delaunay-Rips persistence diagram.

    Args:
        X: an array with shape (*, *)
        format: 'default' or 'gudhi'

    Returns:
        A list of list of points (birth,death) when format is 'default'

        A list of tuples (dim,(birth,death)) when format is 'gudhi'
    """
    return geoph_impl.delaunayRipsPersistenceDiagram(X, format)

def delaunayRipsPersistencePairs(X) -> list[list[tuple[list[int], list[int]]]]:
    """
    Computes Delaunay-Rips persistence pairs.

    Args:
        X: an array with shape (*, *)

    Returns:
        A list of list of simplex pairs (birthSimplex, deathSimplex)
    """
    return geoph_impl.delaunayRipsPersistencePairs(X)

def delaunayRipsPersistenceGenerators2(X) -> list[tuple[list[tuple[int, int]], tuple[float, float]]]:
    """
    Computes Delaunay-Rips 1-dimensional persistent generators for a point cloud in R^2.
    Args:
        X: an array with shape (*, 2)
    Returns:
        A list of 1-dimensional persistent generators.
        Each generators consists in a list of edge, and a pair of values (birth, death)
    """
    return geoph_impl.delaunayRipsPersistenceGenerators2(X)

def delaunayRipsPersistenceGenerators3(X) -> tuple[list[tuple[list[tuple[int, int]], tuple[float, float]]], list[tuple[list[list[int]], tuple[float, float]]]]:
    """
    Computes Delaunay-Rips 1- and 2-dimensional persistent generators for a point cloud in R^3.
    Args:
        X: an array with shape (*, 3)
    Returns:
        A list of 1-dimensional persistent generators, and a list of 2-dimensional persistent generators.
    """
    return geoph_impl.delaunayRipsPersistenceGenerators3(X)

def ripsPersistenceGenerators2(X) -> list[tuple[list[tuple[int, int]], tuple[float, float]]]:
    """
    Computes Rips 1-dimensional persistent generators for a point cloud in R^2.
    Args:
        X: an array with shape (*, 2)
    Returns:
        A list of 1-dimensional persistent generators.
        Each generators consists in a list of edge, and a pair of values (birth, death)
    """
    return geoph_impl.ripsPersistenceGenerators2(X)

def ripsPersistenceDiagram2(X, format:str='default') -> list[list[tuple[float, float]]] | list[tuple[int, tuple[float, float]]]:
    """
    Computes Rips persistence diagram for a point cloud in R^2.
    Args:
        X: an array with shape (*, *)
        format: 'default' or 'gudhi'
    Returns:
        A list of list of points (birth,death) when format is 'default'

        A list of tuples (dim,(birth,death)) when format is 'gudhi'
    """
    return geoph_impl.ripsPersistenceDiagram2(X, format)

def ripsPersistencePairs2(X) -> list[list[tuple[list[int], list[int]]]]:
    """
    Computes Rips persistence pairs for a point cloud in R^2.
    Args:
        X: an array with shape (*, *)
    Returns:
        A list of list of simplex pairs (birthSimplex, deathSimplex)
    """
    return geoph_impl.ripsPersistencePairs2(X)