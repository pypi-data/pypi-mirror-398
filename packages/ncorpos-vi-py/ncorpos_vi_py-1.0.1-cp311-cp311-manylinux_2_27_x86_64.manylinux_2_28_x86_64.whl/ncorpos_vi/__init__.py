import os
import sys
import ctypes
from pathlib import Path

# Carrega a biblioteca manualmente antes de qualquer import
def _preload_libraries():
    """Pré-carrega a biblioteca Fortran"""
    package_dir = Path(__file__).parent
    core_dir = package_dir / "_core"

    def find_library(prefix: str) -> Path:
        """
        Encontra a melhor biblioteca compartilhada para um dado prefixo.
        Prioridade:
        1) libXXX.so
        2) libXXX.so.<major>
        3) libXXX.so.<major>.<minor>.<patch>
        """
        if not core_dir.exists():
            raise RuntimeError(f"Diretório {core_dir} não existe")

        candidates = list(core_dir.glob(f"{prefix}.so*"))

        if not candidates:
            raise RuntimeError(f"Nenhuma biblioteca encontrada para {prefix}")

        # ordena colocando as mais genéricas primeiro
        candidates.sort(key=lambda p: (
            p.suffix != ".so",          # .so primeiro
            p.name.count(".")           # menos pontos = mais genérica
        ))

        return candidates[0]


    libutilidades = find_library("libutilidades")
    libvalores_iniciais = find_library("libvalores_iniciais")

    ctypes.CDLL(libutilidades, mode=ctypes.RTLD_GLOBAL)
    ctypes.CDLL(libvalores_iniciais, mode=ctypes.RTLD_GLOBAL)

# Executa o pré-carregamento
_preload_libraries()

from .api import Gerador
from ._version import __version__

__all__ = ["Gerador", "__version__"]