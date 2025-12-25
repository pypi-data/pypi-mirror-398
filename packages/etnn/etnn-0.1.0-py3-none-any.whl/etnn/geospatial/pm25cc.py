import os
import json
import pandas as pd
import requests
import torch
import numpy as np
from torch_geometric.data import InMemoryDataset
from etnn.combinatorial_data import CombinatorialComplexData

class PM25CC(InMemoryDataset):
    def __init__(
        self,
        root,
        transform=None,
        pre_transform=None,
        pre_filter=None,
        force_reload=False,
    ):
        # 手动删除旧缓存
        if force_reload and os.path.exists(os.path.join(root, "processed", "geospatialcc.pt")):
            print(">>> [PM25CC] force_reload=True, deleting old cache...")
            os.remove(os.path.join(root, "processed", "geospatialcc.pt"))

        super().__init__(root, transform, pre_transform, pre_filter)
        self.load(self.processed_paths[0])

    @property
    def raw_file_names(self):
        return ["geospatialcc.json"]

    @property
    def processed_file_names(self):
        return ["geospatialcc.pt"]

    def download(self):
        url = "https://raw.githubusercontent.com/NSAPH-Projects/topological-equivariant-networks/main/data/input/geospatialcc.json"
        path = os.path.join(self.raw_dir, self.raw_file_names[0])
        response = requests.get(url)
        with open(path, "wb") as f:
            f.write(response.content)

    def process(self):
        print(">>> [PM25CC] process() started")
        path = os.path.join(self.raw_dir, self.raw_file_names[0])
        with open(path, "r") as f:
            ccdict = json.load(f)
            print(">>> [PM25CC] ccdict keys:", ccdict.keys())

        data = CombinatorialComplexData.from_ccdict(ccdict)

        # === 记录 points_to_cells（有就加上） ===
        import pandas as pd
        if "points_to_cells" in ccdict:
            node_cell_indicator = pd.DataFrame(ccdict["points_to_cells"])
            data.index_1 = node_cell_indicator.road
            data.index_2 = node_cell_indicator.tract

        # === 预处理阶段 ===
        if self.pre_filter is not None:
            data = [d for d in [data] if self.pre_filter(d)]
        if self.pre_transform is not None:
            data = [self.pre_transform(d) for d in [data]]
        else:
            data = [data]

        # ? 在这里添加 mask 生成逻辑（非常关键）
        from etnn.geospatial import transforms
        print(">>> [PM25CC] creating train/val/test mask ...")
        data[0] = transforms.create_mask(data[0])  # ? 调用 create_mask 并写入 data

        # === 保存数据 ===
        print(">>> [PM25CC] saving processed data:", self.processed_paths[0])
        print(">>> [PM25CC] data_list[0] attributes:", data[0].__dict__.keys())

        data, slices = self.collate(data)
        torch.save((data, slices), self.processed_paths[0])
        print(">>> [PM25CC] saved (data, slices) via torch.save ")







# if __name__ == "__main__":
#     from torch.utils.data import DataLoader
#     from etnn_spatial.combinatorial_complexes import CombinatorialComplexCollater
#     from torch_geometric.transforms import Compose

#     # quick test
#     dataset = GeospatialCC(
#         root="data",
#         transform=create_mask,
#         pre_transform=Compose([standardize_cc, squash_cc]),
#         force_reload=True,
#     )
#     follow_batch = ["cell_0", "cell_1", "cell_2"]
#     collate_fn = CombinatorialComplexCollater(dataset, follow_batch=follow_batch)
#     loader = DataLoader(dataset, collate_fn=collate_fn, batch_size=1)
#     for batch in loader:
#         pass
