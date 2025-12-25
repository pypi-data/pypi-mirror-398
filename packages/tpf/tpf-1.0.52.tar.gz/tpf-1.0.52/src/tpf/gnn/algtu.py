import os 
from leadingtek.conf.common import CommonConfig
cm = CommonConfig()

#--------------------------------------------------
## 模型定义
#--------------------------------------------------
import torch
import torch.nn as nn
import torch.nn.functional as F
import torch_geometric.transforms as T
from torch_geometric.nn import GATConv, Linear
from leadingtek.conf.common import CommonConfig
cm = CommonConfig()

class GAT(torch.nn.Module):
    def __init__(self, in_channels, hidden_channels, out_channels, heads):
        super().__init__()
        self.conv1 = GATConv(in_channels, hidden_channels, heads, dropout=0.1)
        self.conv2 = GATConv(hidden_channels * heads, hidden_channels, heads=1, concat=False, dropout=0.1)
        self.conv3 = GATConv(hidden_channels, int(hidden_channels/4), heads=1, concat=False, dropout=0.1)
        self.lin = Linear(int(hidden_channels/4), out_channels)
        self.sigmoid = nn.Sigmoid()

    def forward(self, x, edge_index, edge_attr):
        x = F.dropout(x, p=0.1, training=self.training)
        x = F.elu(self.conv1(x, edge_index, edge_attr))
        x = F.dropout(x, p=0.1, training=self.training)
        x = F.elu(self.conv2(x, edge_index, edge_attr))
        x = F.elu(self.conv3(x, edge_index, edge_attr))
        x = self.lin(x)
        x = self.sigmoid(x)
        
        return x


#--------------------------------------------------
# 数据
##-------------------------------------------------
class ParamConfig:
    #字段列
    time14    = "DT_TIME"
    id11      = "ACCT_NUM"
    id12      = "TCAC"
    bank11    = "ORGANKEY"
    bank12    = "CFIC"
    amt1      = "CRAT"  #原币交易金额,付
    amt2      = "CRAT"  #原币交易金额,收
    amt3      = "CNY_AMT"
    amt4      = "USD_AMT"
    currency1 = "CRTP"  #币种
    currency2 = "CRTP"
    channel   = "TSTP"
    label     = "VOUCHER_NO"
    
    drop_cols        = ["TICD","CB_PK","TX_NO","CNY_AMT","USD_AMT"]
    dict_file        = os.path.exists(cm.alg_model_dir,"gnn_dict_file23.txt")
    num_scaler_file  = os.path.exists(cm.alg_model_dir,"gnn_scaler_num23.pkl")
    date_scaler_file = os.path.exists(cm.alg_model_dir,"gnn_scaler_date23.pkl")
    max_date         = '2035-01-01'
    model_param_path = os.path.exists(cm.alg_model_dir,"gnn_model_23.pkl")

    def __init__(self):
        """
        - identity:标识列,需要转str
        - date_type:日期列
        - classify_type:类型别，需要需要转str
        - num_type:数字列，转float64 
        
        """
        #字段列分类 
        self.identity       = [self.id11,self.id12,self.bank11,self.bank12]  #数据标识
        self.date_type      = [self.time14]
        self.classify_type  = [self.channel,self.currency1]
        self.classify_type2 = [[self.bank11,self.bank12]]  #一组类别使用同一个字典
        self.classify_type_pre = [self.channel, self.currency1, self.bank11, self.bank12]  #预测时的类别列
        self.num_type       = [self.amt1]
        self.bool_type      = []
        self.time_group     = 'time_group'
        self.identity_agg   = [self.id11,self.id12,self.bank11,self.bank12]  #分组标识
        self.classify_agg   = self.identity_agg + self.classify_type + [self.time_group]
        self.is_agg_by_day  = True  
        
pc = ParamConfig()



#--------------------------------------------------
## 训练
#--------------------------------------------------
import os 
import pandas as pd 
import numpy as np
from datetime import date, timedelta
from tpf.link.datadeal import Tu 
from tpf.link import data_pre_update
from torch_geometric.data import (
    Data,
    InMemoryDataset
)
from torch.utils.data import WeightedRandomSampler
from torch_geometric.loader import NeighborLoader

class TrainTu:
    def __init__(self,cm=cm):
        self.cm = cm 

    @staticmethod
    def data_obser(df):
        """
        数据观察 
        """
        cm.lg("null value show:df.isna().sum()")
        cm.lg(f"df.isna().sum():\n{df.isna().sum()}")
        cm.lg(f"df.info():\n{df.info()}")

    
    @staticmethod
    def acc_stats(data):
        """账户统计"""
        # 假设你的 DataFrame 名为 df
        df = data.copy()
        # 计算各列的不重复值个数
        unique_counts = {
            'ORGANKEY': df['ORGANKEY'].nunique(),
            'ACCT_NUM': df['ACCT_NUM'].nunique(),
            'CFIC': df['CFIC'].nunique(),
            'TCAC': df['TCAC'].nunique()
        }
        
        # 创建组合列并计算不重复值个数
        df['ORGANKEY_ACCT_NUM'] = df['ORGANKEY'].astype(str) + '_' + df['ACCT_NUM'].astype(str)
        df['CFIC_TCAC'] = df['CFIC'].astype(str) + '_' + df['TCAC'].astype(str)
        
        # 计算组合列的不重复值个数
        combined_counts = {
            'ORGANKEY_ACCT_NUM': df['ORGANKEY_ACCT_NUM'].nunique(),
            'CFIC_TCAC': df['CFIC_TCAC'].nunique()
        }
        
        print("各列不重复值个数:")
        print(unique_counts)
        print("\n组合列不重复值个数:")
        print(combined_counts)
    
    
        # 合并两列的所有值，然后计算唯一值个数
        unique_values = pd.concat([df['ORGANKEY_ACCT_NUM'], df['CFIC_TCAC']]).nunique()
        
        cm.lg(f"ACCT_NUM 和 TCAC 以及机构合并后 所有不重复值的总数: {unique_values}")
        

    @staticmethod 
    def data_pre_deal(df,pc):
        df = data_pre_update(df, pc.identity, pc.date_type, pc.num_type, pc.classify_type, 
                        classify_type2=pc.classify_type2, bool_type=[],
                        save_file=None, dict_file=pc.dict_file, is_num_std=True, 
                        is_pre=False, num_scaler_file=pc.num_scaler_file,
                        date_scaler_file=pc.date_scaler_file, max_date=pc.max_date)
        
        print(df[:3])
        return df 

    @staticmethod 
    def data_pre_deal2(df,pc):
        df_pre = data_pre_update(df, pc.identity, pc.date_type, pc.num_type, classify_type=pc.classify_type_pre, 
                classify_type2=[], bool_type=[],
                save_file=None, dict_file=pc.dict_file, is_num_std=True, 
                is_pre=True,num_scaler_file=pc.num_scaler_file,
                date_scaler_file=pc.date_scaler_file, max_date=pc.max_date)
        print(f"df_pre:\n{df_pre}")
        return df_pre

    @staticmethod 
    def tu_process(df, pc):
        tu = Tu(pc)
        df, receiving_df, paying_df, currency_ls = tu.preprocess(df)
        cm.lg(f"df1 before node attr=\n{df[:3]}")
        accounts = tu.get_all_account(df)   
        cm.lg(f"acc lable:\n{accounts[:3]}")
        node_attr, node_label = tu.get_node_attr(currency_ls, paying_df,receiving_df, accounts)
        cm.lg(f"df2 before node attr=\n{df[:3]}")
        cm.lg(f"df.info():\n{df.info()}")
        edge_attr, edge_index = tu.get_edge_df(accounts, df)
        cm.lg(f"acc lable:\n{accounts[:3]}")

        data = Data(x=node_attr,
                    edge_index=edge_index,
                    y=node_label,
                    edge_attr=edge_attr
                    )
        
        return data,accounts

    @staticmethod 
    def _train(data,model=None, epoch = 30,):
        device= 'cpu'
        if model is None:
            model = GAT(in_channels=data.num_features, hidden_channels=32, out_channels=1, heads=8)    
        model = model.to(device)
        criterion = torch.nn.BCELoss()
        optimizer = torch.optim.SGD(model.parameters(), lr=0.0005)
        
        split = T.RandomNodeSplit(split='train_rest', num_val=0.1, num_test=0)
        data = split(data)
        
        # 计算样本权重
        train_mask = data.train_mask
        y_train = data.y[train_mask].long()  # 确保 y_train 是整数类型
        class_counts = torch.bincount(y_train)
        class_weights = 1. / class_counts
        sample_weights = class_weights[y_train]
        
        # 创建加权采样器
        sampler = WeightedRandomSampler(
            sample_weights,
            num_samples=len(y_train),  # 或调整为batch_size的倍数
            replacement=True
        )
        
        # 修改train_loader使用采样器
        train_loader = NeighborLoader(
            data,
            num_neighbors=[10] * 2,
            batch_size=256,
            input_nodes=data.train_mask,
            sampler=sampler  # 添加采样器
        )
        
        # train_loader = loader = NeighborLoader(
        #     data,
        #     num_neighbors=[10] * 2,
        #     batch_size=256,
        #     input_nodes=data.train_mask,
        # )
        
        test_loader = loader = NeighborLoader(
            data,
            num_neighbors=[10] * 2,
            batch_size=256,
            input_nodes=data.val_mask,
        )
        
        for i in range(epoch):
            total_loss = 0
            model.train()
            for data in train_loader:
                optimizer.zero_grad()
                data.to(device)
                pred = model(data.x, data.edge_index, data.edge_attr)
                ground_truth = data.y
                _min = pred.min().item()
                _max = pred.max().item()
                if _min< 0 or _max>1:
                    print(pred)
                    break
                error_list = list(set(torch.unique(ground_truth).tolist()) - set([0,1]))
                if len(error_list)>0:
                    print("Unique labels:", torch.unique(ground_truth))  # Should only show 0 and/or 1
                    break
                    
                loss = criterion(pred, ground_truth.unsqueeze(1))
                loss.backward()
                optimizer.step()
                total_loss += float(loss)
            if epoch%10 == 0:
                # print(f"Epoch: {i:03d}, Loss: {total_loss:.4f}")
                msg = f"Epoch: {i:03d}, Loss: {total_loss:.4f}"
                cm.lg(msg)
                # model.eval()
                # acc = 0
                # total = 0
                # for test_data in test_loader:
                #     test_data.to(device)
                #     pred = model(test_data.x, test_data.edge_index, test_data.edge_attr)
                #     ground_truth = test_data.y
                #     correct = (pred == ground_truth.unsqueeze(1)).sum().item()
                #     total += len(ground_truth)
                #     acc += correct
                # acc = acc/total
                # print('accuracy:', acc)
        
                model.eval()
                acc = 0
                total = 0
                tp = 0  # 真正例
                fn = 0  # 假反例
                fp = 0  # 假正例（如果需要计算精确率Precision）
                
                list_pre = []
                list_label = []
                
                for test_data in test_loader:
                    test_data.to(device)
                    pred = model(test_data.x, test_data.edge_index, test_data.edge_attr)
                    # pred = torch.sigmoid(pred)  # 如果模型输出未经过sigmoid
                
                    list_pre.extend(pred.view(-1).tolist())
                    
                    pred_labels = (pred > 0.1).int()  # 二分类阈值设为0.5
                    
                    ground_truth = test_data.y.int()
                    # print(pred_labels.shape,ground_truth.shape)
                    list_label.extend(ground_truth.view(-1).tolist())
                    
                    # 确保形状匹配
                    if ground_truth.dim() == 1:
                        ground_truth = ground_truth.unsqueeze(1)
                    # print(pred_labels.shape,ground_truth.shape)
                    # 计算准确率
                    correct = (pred_labels == ground_truth).sum().item()
                    total += ground_truth.size(0)
                    acc += correct
                    
                    # 计算真正例和假反例（用于召回率）
                    tp += ((pred_labels == 1) & (ground_truth == 1)).sum().item()
                    fn += ((pred_labels == 0) & (ground_truth == 1)).sum().item()
                    
                    # 如果需要精确率Precision，可以计算假正例
                    fp += ((pred_labels == 1) & (ground_truth == 0)).sum().item()
                
                # 计算指标
                accuracy = acc / total
                recall = tp / (tp + fn + 1e-8)     # 添加小量避免除以0
                precision = tp / (tp + fp + 1e-8)  # 可选：计算精确率
        
                f1 = 2*(recall*precision)/(recall+precision+1e-7)
        
                list_pre = np.array(list_pre)
                list_label = np.array(list_label)
                
                # 找到 label==1 的索引
                idx = np.where(list_label == 1)[0]
                
                # 取出 list_pre 中对应的元素
                pre_at_1 = list_pre[idx]
                
                # print(f'Accuracy: {accuracy:.4f}',f'Recall: {recall:.4f}',f'Precision: {precision:.4f}',f"f1={f1}",np.round(pre_at_1.max(),5))
                msg = f'Accuracy: {accuracy:.4f} Recall: {recall:.4f}, Precision: {precision:.4f}, f1={f1} max score:{np.round(pre_at_1.max(),5)}'
                cm.lg(msg)
        return model 

    @staticmethod 
    def model_save(data,model,pc):
        model_param_path = pc.model_param_path
        torch.save(model.state_dict(), model_param_path)

        model = GAT(in_channels=data.num_features, hidden_channels=32, out_channels=1, heads=8)
        model.load_state_dict(torch.load(model_param_path))
        return model 

    @staticmethod 
    def model_load(data,pc):
        model = GAT(in_channels=data.num_features, hidden_channels=32, out_channels=1, heads=8)
        model.load_state_dict(torch.load(pc.model_param_path)) 
        return model

    

    @staticmethod 
    def train(df, pc, epoch=10,
              continuation=True  #是否在之前训练的基础上进行训练
             ):
        
        ## 数据观察 
        TrainTu.data_obser(df)

        ##账户统计
        # TrainTu.acc_stats(df)

        ##数据预处理
        cm.lg("数据预处理----------------")
        cm.lg(f"df:\n{df[:3]}")
        df = TrainTu.data_pre_deal(df,pc)
        print(df[:3])
        print(df.info())

        ##图处理
        print("图处理-------------------")
        data,accounts = TrainTu.tu_process(df, pc)
        print(data)

        if continuation:#从文件中加载模型
            if os.path.exists(pc.model_param_path):
                model = TrainTu.model_load(data,pc)
            else:
                model = None 
        else:
            model = None 

        ##训练
        print("训练---------------------")
        model = TrainTu._train(data, model=model, epoch=epoch)

        ##模型保存
        print("模型保存-----------------")
        TrainTu.model_save(data, model, pc)

    @staticmethod 
    def _pre(data,pc, model, df):
        
        df_pre = df[[pc.id11,"Bank"]].copy()
        device='cpu'
        model = model.to(device)
        
        data_loader = loader = NeighborLoader(
            data,
            num_neighbors=[10] * 3,
            batch_size=256,
            input_nodes=None,  # 不限制输入节点，推理所有节点
            shuffle=False,     # 推理时不打乱
        )

        model.eval()
        acc = 0
        total = 0
        tp = 0  # 真正例
        fn = 0  # 假反例
        fp = 0  # 假正例（如果需要计算精确率Precision）
        
        list_pre = []
        list_label = []
        all_nid = []   # 存放每个 batch 的节点全局 id
        all_pred = []  # 存放预测分数
        with torch.no_grad():
            for test_data in data_loader:
                test_data.to(device)
                pred = model(test_data.x, test_data.edge_index, test_data.edge_attr)
                # pred = torch.sigmoid(pred)  # 如果模型输出未经过sigmoid
                
                # global_node_id = test_data.n_id.cpu()   # 全局节点 id
                # df_pred = df_pre.iloc[global_node_id].copy()
                # df_pred['pred_score'] = pred.cpu().numpy()
                # cm.lg(f"df_pred:\n{df_pred[:5]}")
                
                # 收集
                all_nid.append(test_data.n_id.cpu().numpy())  # ndarray 一维
                all_pred.append(pred.view(-1).cpu().numpy())  # ndarray 一维

                list_pre.extend(pred.view(-1).tolist())
                
            
                pred_labels = (pred > 0.1).int()  # 二分类阈值设为0.5
                
                ground_truth = test_data.y.int()
                # print(pred_labels.shape,ground_truth.shape)
                list_label.extend(ground_truth.view(-1).tolist())
                
                # 确保形状匹配
                if ground_truth.dim() == 1:
                    ground_truth = ground_truth.unsqueeze(1)
                # print(pred_labels.shape,ground_truth.shape)
                # 计算准确率
                correct = (pred_labels == ground_truth).sum().item()
                total += ground_truth.size(0)
                acc += correct
                
                # 计算真正例和假反例（用于召回率）
                tp += ((pred_labels == 1) & (ground_truth == 1)).sum().item()
                fn += ((pred_labels == 0) & (ground_truth == 1)).sum().item()
                
                # 如果需要精确率Precision，可以计算假正例
                fp += ((pred_labels == 1) & (ground_truth == 0)).sum().item()
            
        # 计算指标
        accuracy = acc / total
        recall = tp / (tp + fn + 1e-8)     # 添加小量避免除以0
        precision = tp / (tp + fp + 1e-8)  # 可选：计算精确率
        
        print(f'Accuracy: {accuracy:.4f}')
        print(f'Recall: {recall:.4f}')
        print(f'Precision: {precision:.4f}')  # 可选输出
        
        
        # 把列表拼成两个一维 ndarray
        nid = np.concatenate(all_nid)   # shape [N_total]
        score = np.concatenate(all_pred)  # shape [N_total]

        # 一次性构造结果表
        df_pred = pd.DataFrame({
            'global_node_id': nid,
            'pred_score': score
        })

        # 如需回到原始 df
        df_pred = df_pred.sort_values('global_node_id')  # 保证顺序
        df_pred = pd.concat([
            df_pre.iloc[df_pred['global_node_id']].reset_index(drop=True),
            df_pred[['pred_score']].reset_index(drop=True)
        ], axis=1)

        return df_pred,accuracy,recall,precision,fp

    @staticmethod 
    def pre(df,pc):
        ## 数据观察 
        print("数据观察---------------------")
        TrainTu.data_obser(df)

        ##账户统计
        print("账户统计---------------------")
        TrainTu.acc_stats(df)

        ##数据预处理
        print("数据预处理-------------------")
        df = TrainTu.data_pre_deal2(df,pc)
        print(df[:3])

        ##图处理
        print("图数据处理-------------------")
        data,accounts = TrainTu.tu_process(df,pc)
        print(data)

        ##模型加载
        print("模型加载---------------------")
        model = TrainTu.model_load(data,pc)

        ##模型预测
        print("模型预测---------------------")
        df_pre,accuracy,recall,precision,fp = TrainTu._pre(data, pc, model,accounts)
        return df_pre,accuracy,recall,precision,fp
        
        







