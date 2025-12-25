import os,datetime
import numpy as np
import pandas as pd
from sklearn import preprocessing
import torch
from typing import Callable, Optional
from torch_geometric.data import (
    Data,
    InMemoryDataset
)

from tpf import pkl_load,pkl_save



class AMLtoGraph(InMemoryDataset):

    def __init__(self, root: str, edge_window_size: int = 10,
                 transform: Optional[Callable] = None,
                 pre_transform: Optional[Callable] = None,
                 raw_file_names=None,processed_file_names=None,mp=None):
        """
        - mp: 数据列映射关系及数据处理
        
        """
        self.edge_window_size = edge_window_size
        self._raw_file_names = raw_file_names
        self._processed_file_names=processed_file_names
        super().__init__(root, transform, pre_transform)
        self.data, self.slices = torch.load(self.processed_paths[0], weights_only=False)
        

    @property
    def raw_file_names(self) -> str:
        return self._raw_file_names 

    @property
    def processed_file_names(self) -> str:
        return self._processed_file_names

    @property
    def num_nodes(self) -> int:
        return self._data.edge_index.max().item() + 1

    def process(self):

        tu_save_path = self.raw_paths[0]
        print("tu_save_path:",tu_save_path)
        node_attr, node_label, edge_attr, edge_index = pkl_load(tu_save_path, weights_only=False)

        data = Data(x=node_attr,
                    edge_index=edge_index,
                    y=node_label,
                    edge_attr=edge_attr)
        
        data_list = [data] 
        if self.pre_filter is not None:
            data_list = [d for d in data_list if self.pre_filter(d)]

        if self.pre_transform is not None:
            data_list = [self.pre_transform(d) for d in data_list]

        data, slices = self.collate(data_list)
        torch.save((data, slices), self.processed_paths[0])



