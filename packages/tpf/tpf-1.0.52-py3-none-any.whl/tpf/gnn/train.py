

# graph_trainer.py
import torch
import torch.nn.functional as F
from torch_geometric.transforms import RandomNodeSplit
from torch.utils.data import WeightedRandomSampler
from torch_geometric.loader import NeighborLoader
from tpf.data.tu11 import GraphDataBuilder  # 使用新 builder
import os
import numpy as np 
import pandas as pd 
from tpf.conf.common import ParamConfig 
from tpf.mlib import ModelEval as me 

class GraphTrainer:
    """
    图神经网络训练器（GNN Trainer）
    职责：模型训练、验证、预测、保存/加载
    """

    def __init__(self, pc:ParamConfig, model_cls=None):
        """
        初始化图神经网络训练器

        Args:
            pc: 参数配置对象，包含数据列名、模型路径等配置信息
            model_cls: 可选的自定义模型类，如果未提供则使用默认的GAT模型

        Attributes:
            pc: 参数配置对象
            model_cls: 使用的模型类
            builder: 图数据构建器实例，用于从原始数据构建图结构
        """
        self.pc = pc
        self.lg = pc.lg
        self.model_cls = model_cls or self._default_model
        self.builder = GraphDataBuilder(
            account_id_col=pc.tu.nodeid,
            account_label_col=pc.tu.label_name,
            account_feature_cols=pc.tu.feature_cols,
            trans_from_col=pc.tu.from_col,
            trans_to_col=pc.tu.to_col,
            trains_time_col=pc.tu.time_col
        )

    @staticmethod
    def _default_model(in_channels, out_channels=1, **kwargs):
        # from torch_geometric.nn import GAT
        from tpf.gnn.gat import GAT
        return GAT(in_channels=in_channels, hidden_channels=512, out_channels=out_channels, heads=8)

    def build_graph_data(self, acc_file=None, tra_file=None, file_type='csv',df_acc=None,df_tra=None,debug=False):
        """使用 GraphDataBuilder 构建图数据"""
        
        data, meta = self.builder.load_and_build(
            account_file=acc_file,
            transaction_file=tra_file,
            file_type=file_type,
            df_acc=df_acc,
            df_tra=df_tra,
            debug=debug
        )
        return data, meta

    def train(self, data, epoch=300, continuation=True,
              batch_size=256,layer_num=3,num_neighbors=10,
              model_params=None,threshold=0.5008, me_interval=10):
        """
        训练图神经网络模型

        Args:
            data: 图数据对象
            epoch: 训练轮数，默认30
            continuation: 是否继续训练，默认True
            batch_size: 批大小，默认256
            layer_num: 图层数，默认3
            num_neighbors: 邻居节点数，默认10
            model_params: 模型参数，可选
            threshold: 分类阈值，默认0.5

        Returns:
            model: 训练好的模型
        """
        device = 'cuda' if torch.cuda.is_available() else 'cpu'
        print(f"Using device: {device}")

        # 模型初始化
        if model_params is None:
            model = self.model_cls(in_channels=data.num_features, out_channels=1).to(device)
        else:
            model = self.model_cls(**model_params)
        criterion = torch.nn.BCELoss()
        optimizer = torch.optim.SGD(model.parameters(), lr=0.0005)

        # 划分训练/验证集
        split = RandomNodeSplit(split='train_rest', num_val=0.1, num_test=0.1)
        data = split(data)
        data = data.to(device)

        # 加权采样器（处理类别不平衡）
        y_train = data.y[data.train_mask].long()
        class_weights = 1. / torch.bincount(y_train).float()
        sample_weights = class_weights[y_train]
        sampler = WeightedRandomSampler(sample_weights, num_samples=len(y_train), replacement=True)

        # 数据加载器
        train_loader = NeighborLoader(
            data,
            num_neighbors=[num_neighbors] * layer_num,
            batch_size=batch_size,
            input_nodes=data.train_mask,
            sampler=sampler
        )
        val_loader = NeighborLoader(
            data,
            num_neighbors=[num_neighbors] * layer_num,
            batch_size=batch_size,
            input_nodes=data.val_mask,
            shuffle=False
        )

        # 是否继续训练
        if continuation and os.path.exists(self.pc.model_param_path()):
            print(f"Loading pretrained model from {self.pc.model_param_path()}")
            model.load_state_dict(torch.load(self.pc.model_param_path(), map_location=device))

        # 训练循环
        for i in range(epoch):
            self.lg(f"Epoch {i:03d}...")
            model.train()
            total_loss = 0
            pred_list = []
            y_list = []
            for batch in train_loader:
                batch = batch.to(device)
                optimizer.zero_grad()
                out = model(batch.x, batch.edge_index, batch.edge_attr)
                pred = torch.sigmoid(out).view(-1)
                loss = criterion(pred, batch.y.float())
                loss.backward()
                optimizer.step()
                total_loss += loss.item()
                pred_list.extend(pred.detach().cpu().numpy())
                y_list.extend(batch.y.detach().cpu().numpy())
            with torch.no_grad():
                if i % 10 == 0:
                    val_acc, val_recall, val_precision, f1 = self._evaluate(model, val_loader, device, threshold)
                    self.lg(f"Epoch {i:03d}, Loss: {total_loss:.4f}, Val Acc: {val_acc:.4f}, Recall: {val_recall:.4f},Precision: {val_precision:.4f}, F1: {f1:.4f}")
                    pred_arr = np.array(pred_list)
                    y_arr    = np.array(y_list)
                    self.lg(f"pre_arr.shape={pred_arr.shape},y_arr.shape={y_arr.shape}")
                    count_max_list, interval_width = me.interval_distribution(y_probs=pred_arr, y_test=y_arr, interval=me_interval)
                    
                    self.lg(f"interval_width:{interval_width},count_max_list:\n{count_max_list}")
            
        # 保存模型
        torch.save(model.state_dict(), self.pc.model_param_path())
        self.lg(f"训练 结束....\nModel saved to {self.pc.model_param_path()}")
        
        return model

    def _evaluate(self, model, loader, device, threshold=0.5):
        """
        评估模型性能

        Args:
            model: 要评估的模型
            loader: 数据加载器
            device: 计算设备
            threshold: 分类阈值，默认0.5

        Returns:
            acc: 准确率
            recall: 召回率
            precision: 精确率
            f1: F1分数
        """
        model.eval()
        tp = tn = fp = fn = 0
        with torch.no_grad():
            for batch in loader:
                batch = batch.to(device)
                out = model(batch.x, batch.edge_index, batch.edge_attr)
                pred = (torch.sigmoid(out) > threshold).int().view(-1)
                true = batch.y.int()

                tp += ((pred == 1) & (true == 1)).sum().item()
                tn += ((pred == 0) & (true == 0)).sum().item()
                fp += ((pred == 1) & (true == 0)).sum().item()
                fn += ((pred == 0) & (true == 1)).sum().item()

        acc = (tp + tn) / (tp + tn + fp + fn + 1e-8)
        recall = tp / (tp + fn + 1e-8)
        precision = tp / (tp + fp + 1e-8)
        f1 = 2 * (precision * recall) / (precision + recall + 1e-8)
        return acc, recall, precision, f1

    def predict(self, data, df_acc, batch_size=256,layer_num=3,num_neighbors=10):
        device = 'cuda' if torch.cuda.is_available() else 'cpu'
        model = self.model_cls(in_channels=data.num_features, out_channels=1).to(device)
        model.load_state_dict(torch.load(self.pc.model_param_path(), map_location=device))
        model.eval()

        loader = NeighborLoader(
            data,
            num_neighbors=[num_neighbors] * layer_num,
            batch_size=batch_size,
            input_nodes=None,
            shuffle=False
        )

        all_scores = []
        all_ids = []

        with torch.no_grad():
            for batch in loader:
                batch = batch.to(device)
                out = model(batch.x, batch.edge_index, batch.edge_attr)
                scores = torch.sigmoid(out).view(-1).cpu().numpy()
                node_ids = batch.n_id.cpu().numpy()

                all_scores.append(scores)
                all_ids.append(node_ids)

        # 拼接结果
        scores = np.concatenate(all_scores)
        node_ids = np.concatenate(all_ids)

        # 创建DataFrame并去重，确保每个节点只保留一个预测结果
        df_pred_raw = pd.DataFrame({
            'global_node_id': node_ids,
            'pred_score': scores
        })

        # 按节点ID分组，取每个节点的平均预测分数
        df_pred = df_pred_raw.groupby('global_node_id')['pred_score'].mean().reset_index()
        df_pred = df_pred.sort_values('global_node_id')

        # 关联原始账户信息（如 Account）
        df_pred = pd.concat([
            df_acc.iloc[df_pred['global_node_id']].reset_index(drop=True),
            df_pred[['pred_score']].reset_index(drop=True)
        ], axis=1)
        
        col0 = df_acc.columns[0]
        
        return df_pred[[col0,'pred_score']]