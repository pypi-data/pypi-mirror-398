from __future__ import annotations  # 避免在 Python 3.8 解析 list[int] 报错

import itertools
import re
from types import MappingProxyType
from typing import Literal, Union

import torch
from torch import Tensor
from torch_geometric.data import Data

# Type alias for a cell in a simplicial complex. Frozenset of node indices and a list of features.
Cell = tuple[frozenset[int], tuple[float]]


class CombinatorialComplexData(Data):
    """
    A subclass of PyTorch Geometric's Data class designed for representing combinatorial complexes.

    This class extends standard graph representation to handle higher-dimensional structures found
    in complex networks. It supports adjacency tensors for cells of different ranks (vertices,
    edges, faces, etc.) and their relationships, following a specific naming convention for dynamic
    attribute recognition and processing.

    Attributes
    ----------
    x : torch.FloatTensor
        Features of rank 0 cells (atoms).
    y : torch.FloatTensor
        Target values, assumed to be at the graph level. This tensor should have shape (1,
        num_targets).
    pos : torch.FloatTensor
        Positions of rank 0 cells (atoms). Expected to have shape (num_atoms, 3).
    x_i : torch.FloatTensor
        Features of cells of rank i, where i is a non-negative integer.
    adj_i_j : torch.LongTensor
        Adjacency tensors representing the relationships (edges) between cells of rank i and j,
        where i and j are non-negative integers.
    cells_i : torch.FloatTensor
        Concatenated list of node indices associated with cells of rank i. Note: Use the cell_list
        method to split this tensor into individual cells.
    slices_i : torch.LongTensor
        Slices to split the concatenated cell_i tensor into individual cells. Note: Use the cell_list
        method to split this tensor into individual cells.
    mem_i : torch.BoolTensor
        Optional. Lifters associated with cells of rank i, where i is a non-negative integer.
    """

    attr_dtype = MappingProxyType(
        {
            "x_": torch.float32,
            "cells_": torch.long,
            "slices_": torch.long,
            "mem_": torch.bool,
            "adj_": torch.int64,
        }
    )

    def __inc__(self, key: str, value: any, *args, **kwargs) -> any:
        """Specify how to increment indices for batch processing of data."""
        if re.match(r"adj_(\d+_\d+|\d+_\d+_\d+)", key):
            i, j = key.split("_")[1:3]
            return torch.tensor([[self.num_cells(rank=i)], [self.num_cells(rank=j)]])
        elif re.match(r"cells_\d+", key):
            return self.num_cells(rank=0)
        else:
            return super().__inc__(key, value, *args, **kwargs)

    def __cat_dim__(self, key: str, value: any, *args, **kwargs) -> int:
        """Specify dimension along which tensors are concatenated for batching."""
        if re.match(r"adj_\d+_\d+", key):
            return 1
        else:
            return 0

    def cell_list(
        self,
        rank: int,
        format: Literal["list", "padded"] = "list",
        pad_value: float = torch.nan,
    ) -> Union[list[Tensor], Tensor]:
        """Return the list of cells of a given rank."""
        concatenated_cells = getattr(self, f"cells_{rank}")
        slices = getattr(self, f"slices_{rank}")
        cell_list = list(torch.split(concatenated_cells, slices.tolist()))

        if format == "padded":
            cell_list = torch.nested.as_nested_tensor(cell_list, dtype=torch.float)
            return cell_list.to_padded_tensor(padding=pad_value)
        elif format == "list":
            return cell_list
        else:
            raise ValueError(f"Unknown format: {format}")

    def num_cells(self, rank: int) -> int:
        """Return the number of cells of a given rank."""
        return len(getattr(self, f"slices_{rank}"))

    @property
    def num_features_per_rank(self) -> dict[int, int]:
        """Return number of features for each rank."""
        D = {}
        for key in self.keys():
            if key == "x":
                D[0] = getattr(self, key).size(1)
            elif key.startswith("x_"):
                rank = int(key.split("_")[1])
                D[rank] = getattr(self, key).size(1)
        return D

    @classmethod
    def from_ccdict(cls, data: dict[str, any]) -> "CombinatorialComplexData":
        """Convert a dictionary to a CombinatorialComplexData object."""
        attr = {}
        for key, value in data.items():
            if any(key.startswith(s) for s in ["pos", "y"]):
                attr[key] = torch.tensor(value)

            elif "x_" in key:
                if len(value) == 0:
                    rank = key.split("_")[1]
                    num_features = data["num_features_dict"][rank]
                    attr_value = torch.empty(
                        (0, num_features), dtype=cls.attr_dtype["x_"]
                    )
                else:
                    attr_value = torch.tensor(value, dtype=cls.attr_dtype["x_"])
                attr[key] = attr_value

            elif "cell_" in key:
                if len(value) == 0:
                    slices_val = torch.empty((0,), dtype=cls.attr_dtype["slices_"])
                    cell_val = torch.empty((0,), dtype=cls.attr_dtype["cells_"])
                else:
                    lens = [len(cell) for cell in value]
                    vals = list(itertools.chain.from_iterable(value))
                    cell_val = torch.tensor(vals, dtype=cls.attr_dtype["cells_"])
                    slices_val = torch.tensor(lens, dtype=cls.attr_dtype["slices_"])

                rank = key.split("_")[1]
                attr[f"cells_{rank}"] = cell_val
                attr[f"slices_{rank}"] = slices_val

            elif "mem_" in key:
                num_lifters = len(data["mem_0"][0]) if len(data.get("mem_0", [])) > 0 else 0
                if len(value) == 0:
                    attr_value = torch.empty((0, num_lifters), dtype=cls.attr_dtype["mem_"])
                else:
                    attr_value = torch.tensor(value, dtype=cls.attr_dtype["mem_"])
                attr[key] = attr_value

            elif "adj_" in key:
                attr[key] = torch.tensor(value, dtype=cls.attr_dtype["adj_"])

        if "num_features_dict" in data:
            attr["num_features_dict"] = data["num_features_dict"]
        else:
            print("?? Warning: 'num_features_dict' not found in from_ccdict().")

        return cls.from_dict(attr)


