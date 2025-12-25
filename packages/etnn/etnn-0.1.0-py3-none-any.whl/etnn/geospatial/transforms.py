import numpy as np
import torch

from etnn.combinatorial_data import CombinatorialComplexData


def standardize_cc(data: CombinatorialComplexData) -> CombinatorialComplexData:
    for key, tensor in data.items():
        if key.startswith("x_"):
            # loop per column
            for i in range(tensor.shape[1]):
                # if dummy variable, skip
                if tensor[:, i].unique().shape[0] == 2:
                    continue
                else:
                    tensor[:, i] = (tensor[:, i] - tensor[:, i].mean()) / tensor[
                        :, i
                    ].std()
        if key.startswith("y"):
            data[key] = (tensor - tensor.mean()) / tensor.std()
        if "pos" == key:
            # normalize to 0-1 range per columns
            data[key] = (tensor - tensor.amin(0)) / (tensor.amax(0) - tensor.amin(0))
    return data


def add_pos_to_cc(data: CombinatorialComplexData) -> CombinatorialComplexData:
    data.x_0 = torch.cat([data.x_0, data.pos], dim=1)
    return data

def squash_cc(
    data: CombinatorialComplexData, soft: bool = False
) -> CombinatorialComplexData:
    x_0 = data.x_0
    for key, tensor in data.items():
        if key.startswith("x_") and key != "x_0":
            # extract i from key
            i = key.split("_")[1]
            # x_0 = torch.cat((x_0, tensor[getattr(data, "index_" + i)]), dim=1)
            index_i = getattr(data, "index_" + i)
            agg_feats = torch.stack([tensor[ix].mean(0) for ix in index_i])
            x_0 = torch.cat((x_0, agg_feats), dim=1)
            # remove the original tensor
        if not soft:
            if key.startswith("x_") and key != "x_0":
                delattr(data, key)  # inplace
            elif key.startswith("adj_") and key != "adj_0_0":
                delattr(data, key)
            elif key.startswith("cell_") and key != "cell_0":
                delattr(data, key)
            elif key.startswith("slices_") and key != "slices_0":
                delattr(data, key)
    data.x_0 = x_0
    return data

def create_mask(data, train_ratio=0.7, val_ratio=0.15, test_ratio=0.15, seed=None):
    """
    为 CombinatorialComplexData 创建节点级划分 mask。
    确保 train/val/test 互斥且覆盖所有节点。
    """
    if seed is not None:
        torch.manual_seed(seed)

    # 使用节点数量（x_0的第一个维度）
    if hasattr(data, "x_0") and data.x_0 is not None:
        N = data.x_0.size(0)
    else:
        N = len(data.slices_0)

    perm = torch.randperm(N)  # 打乱所有节点顺序

    n_train = int(train_ratio * N)
    n_val = int(val_ratio * N)
    n_test = N - n_train - n_val

    train_idx = perm[:n_train]
    val_idx = perm[n_train:n_train + n_val]
    test_idx = perm[n_train + n_val:]

    data.training_mask = torch.zeros(N, dtype=torch.bool)
    data.validation_mask = torch.zeros(N, dtype=torch.bool)
    data.test_mask = torch.zeros(N, dtype=torch.bool)

    data.training_mask[train_idx] = True
    data.validation_mask[val_idx] = True
    data.test_mask[test_idx] = True

    print(f"[create_mask] train={data.training_mask.sum().item()}, val={data.validation_mask.sum().item()}, test={data.test_mask.sum().item()}")

    return data




def ensure_x0(data, feat_dim=1):
    import torch
    # 如果已有 x_0，直接返回
    if hasattr(data, "x_0"):
        return data
    # 尝试从 pos 推断节点数
    if hasattr(data, "pos"):
        N = data.pos.size(0)
    # 尝试从 cells_0 推断（若存在）
    elif hasattr(data, "cells_0"):
        N = int(data.cells_0.max().item() + 1)
    else:
        raise RuntimeError("ensure_x0: 无法推断节点数，无法创建 x_0")
    device = getattr(data, "pos", None).device if hasattr(data, "pos") else None
    data.x_0 = torch.zeros((N, feat_dim), dtype=torch.float32, device=device)
    return data


def add_virtual_node(data: CombinatorialComplexData) -> CombinatorialComplexData:
    """
    添加虚拟节点并同步扩展常见 per-node 字段：
      - 扩展 x_0, pos
      - 扩展 mask（training/validation/test/observed）
      - 扩展 y（仅当是 per-node label 时）
    """
    import torch

    feat_dim = data.x_0.shape[1] if hasattr(data, "x_0") and data.x_0 is not None else 1
    data = ensure_x0(data, feat_dim=feat_dim)

    N = data.x_0.size(0)
    device = data.x_0.device

    # 添加虚拟节点
    v_feat = data.x_0.mean(dim=0, keepdim=True)
    data.x_0 = torch.cat([data.x_0, v_feat], dim=0)

    if hasattr(data, "pos") and data.pos is not None:
        v_pos = data.pos.mean(dim=0, keepdim=True)
        data.pos = torch.cat([data.pos, v_pos], dim=0)

    data.virtual_node_id = torch.tensor([N], dtype=torch.long, device=device)

    # 扩展 mask
    for mask_name in ("training_mask", "validation_mask", "test_mask", "observed_mask"):
        if hasattr(data, mask_name):
            mask = getattr(data, mask_name)
            pad = torch.zeros(1, dtype=torch.bool, device=device)
            setattr(data, mask_name, torch.cat([mask, pad]))

    # 扩展 y（仅当是 per-node label 时）
    if hasattr(data, "y") and data.y is not None:
        y = data.y
        if y.dim() >= 1 and y.size(0) == N:
            pad_shape = (1,) + tuple(y.shape[1:]) if y.dim() > 1 else (1,)
            y_pad = torch.zeros(pad_shape, dtype=y.dtype, device=device)
            data.y = torch.cat([y, y_pad], dim=0)

    return data



def randomize(data: CombinatorialComplexData, keys=["x_0"]) -> CombinatorialComplexData:
    # permute the x_0
    for key, val in data.items():
        if key in keys:
            new_val = torch.randn(val.shape).to(val.device) * 0.001
            setattr(data, key, new_val)
            # perm = torch.randperm(val.shape[0]).to(val.device)
            # setattr(data, key, val[perm])
    return data


def x1_labels(data: CombinatorialComplexData) -> CombinatorialComplexData:
    # add a label to x_1
    data.y = data.x_1[data.index_1][:, :1]
    return data
