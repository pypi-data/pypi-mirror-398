"""
jlgametheory: Python interface to GameTheory.jl

"""
from juliacall import Main as jl
from importlib.metadata import PackageNotFoundError, version as _version

jl.seval("using GameTheory")
GameTheory = jl.GameTheory

from .jlgametheory import (
    lrsnash, hc_solve
)

try:
    __version__ = _version("jlgametheory")
except PackageNotFoundError:  # pragma: no cover
    __version__ = "0+unknown"

__all__ = [
    "lrsnash", "hc_solve"
]
