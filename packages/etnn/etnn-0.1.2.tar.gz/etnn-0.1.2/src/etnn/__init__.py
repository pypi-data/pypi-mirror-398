"""E(n)-Equivariant Topological Neural Network package."""

from importlib import metadata

from etnn.combinatorial_data import Cell, CombinatorialComplexData
from etnn.lifter import Lifter
from etnn.model import ETNN

try:
    __version__ = metadata.version("etnn")
except metadata.PackageNotFoundError:  # pragma: no cover
    __version__ = "0.0.0"

__all__ = [
    "Cell",
    "CombinatorialComplexData",
    "ETNN",
    "Lifter",
]
