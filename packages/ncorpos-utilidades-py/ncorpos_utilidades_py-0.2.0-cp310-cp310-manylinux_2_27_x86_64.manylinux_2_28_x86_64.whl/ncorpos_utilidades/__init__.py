# ncorpos_utilidades/__init__.py
import os
import sys
import ctypes
from pathlib import Path

# Carrega a biblioteca manualmente antes de qualquer import
def _preload_library():
    """Pré-carrega a biblioteca Fortran"""
    package_dir = Path(__file__).parent
    lib_paths = [
        package_dir / "_core" / "libutilidades.so.0",
        package_dir / "_core" / "libutilidades.so.0.1.0",
        package_dir / "_core" / "libutilidades.so"
    ]
    
    for lib_path in lib_paths:
        if lib_path.exists():
            try:
                ctypes.CDLL(str(lib_path), mode=ctypes.RTLD_GLOBAL)
                break
            except Exception as e:
                print(f"Failed to preload {lib_path}: {e}")

# Executa o pré-carregamento
_preload_library()

# Agora importa o módulo
from .api import *
from ._version import __version__