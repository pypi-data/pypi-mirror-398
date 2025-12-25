"""特定格式的数据处理
11个字段，第1步就要对应这11个字段
    
（机构，账户，金额，币种）* 2 = 8个字段 
支付方式：现金，ATM,支票，转账，电汇，网银，手机支付，其他
标签

"""
import numpy as np  
import pandas as pd
import torch

from tpf.conf.common import ParamConfig

class mp:
    #字段列
    time14    = "Timestamp"
    id11      = 'Account'  #账户
    id12      = 'Account.1'     #账户
    bank11    = 'From Bank'  #机构
    bank12    = 'To Bank'     #机构
    amt1      = 'Amount Received'  #原币交易金额,付
    amt2      = 'Amount Paid'  #原币交易金额,收
    amt3      = "CNY_AMT"
    amt4      = "USD_AMT"
    currency1 = 'Receiving Currency'  #币种
    currency2 = 'Payment Currency'  #币种
    channel   = 'Payment Format' #渠道
    label     = 'Is Laundering'  #标签
    
    drop_cols        = []
    dict_file = "dict_file.txt"


class GraphDataDeal:
    def __init__(self, mp):
        """图数据处理"""
        self._mp = mp

    def preprocess(self, df):
        """
        - 将机构与账户合并为账户，对于df的处理只是账户合并了机构，其他未变，机构字段仍然保留
        - 提取账户节点属性：账户名称，金额，币种；若有新增类型，可以简化为多种分类的合并
        - 在这里将账户分为了两类，一类是付款账户，一类是收款账户；这两类账户有会有重复账户的，是有交叉的，即一个账户自转就即是收付双方
        """
        df[self._self._mp.id11] = df[self._self._mp.bank11].astype(int).astype(str) + '_' + df[self._self._mp.id11]
        df[self._self._mp.id12] = df[self._self._mp.bank12].astype(int).astype(str) + '_' + df[self._self._mp.id12]
        df = df.sort_values(by=[self._self._mp.id11])

        #付款收款账户的行数与df是一致的 
        receiving_df = df[[self._self._mp.id12, self._self._mp.amt2, self._self._mp.currency2]]
        paying_df = df[[self._self._mp.id11, self._self._mp.amt1, self._self._mp.currency1]]
        receiving_df = receiving_df.rename({self._self._mp.id12: self._self._mp.id11}, axis=1)

        #币种
        currency_ls = sorted(df[self._self._mp.currency2].unique())

        return df, receiving_df, paying_df, currency_ls


    def get_all_account(self, df):
        """所有不重复账户，一条交易为可疑，则对应的两个账户皆为可疑
        """
        ldf = df[[self._self._mp.id11, self._self._mp.bank11]]
        rdf = df[[self._self._mp.id12, self._self._mp.bank12]]
        
        suspicious = df[df[self._self._mp.label]==1]
        s1 = suspicious[[self._self._mp.id11, self._self._mp.label]]
        s2 = suspicious[[self._self._mp.id12, self._self._mp.label]]
        s2 = s2.rename({self._self._mp.id12: self._self._mp.id11}, axis=1)
        suspicious = pd.concat([s1, s2], join='outer')
        suspicious = suspicious.drop_duplicates()

        ldf = ldf.rename({self._self._mp.bank11: 'Bank'}, axis=1)
        rdf = rdf.rename({self._self._mp.id12: self._self._mp.id11, self._self._mp.bank12: 'Bank'}, axis=1)
        print(ldf.shape,rdf.shape)
        df = pd.concat([ldf, rdf], join='outer')
        print("df.shape:",df.shape)
        df = df.drop_duplicates()
        print("df.shape:",df.shape)
        print(df[:3])

        df[self._self._mp.label] = 0
        df.set_index(self._self._mp.id11, inplace=True)
        df.update(suspicious.set_index(self._self._mp.id11))
        df = df.reset_index()
        return df

    def paid_currency_aggregate(self, currency_ls, paying_df, accounts):
        """为付款账户增加付款特征
        - 
        """
        for i in currency_ls:
            temp = paying_df[paying_df[self._self._mp.currency1] == i]
            accounts['avg paid '+str(i)] = temp[self._self._mp.amt1].groupby(temp[self._self._mp.id11]).transform('mean')
            
            # # 按 id11 分组计算均值，得到 Series (索引为 id11 的值)
            # avg_by_account = paying_df[paying_df[self._self._mp.currency1] == i] \
            #                 .groupby(self._self._mp.id11)[self._self._mp.amt1].mean()
            # # 将均值映射到 accounts 表中
            # accounts['avg paid '+str(i)] = accounts[self._self._mp.id11].map(avg_by_account).fillna(0)
            
        return accounts

    def received_currency_aggregate(self, currency_ls, receiving_df, accounts):
        for i in currency_ls:
            temp = receiving_df[receiving_df[self._self._mp.currency2] == i]
            accounts['avg received '+str(i)] = temp[self._self._mp.amt2].groupby(temp[self._self._mp.id11]).transform('mean')
            
            # # 按 id11 分组计算均值，得到 Series (索引为 id11 的值)
            # avg_by_account = receiving_df[receiving_df[self._self._mp.currency2] == i] \
            #                 .groupby(self._self._mp.id11)[self._self._mp.amt2].mean()
            # # 将均值映射到 accounts 表中
            # accounts['avg received '+str(i)] = accounts[self._self._mp.id11].map(avg_by_account).fillna(0)
            
        accounts = accounts.fillna(0)
        return accounts

    def get_node_attr(self, currency_ls, paying_df,receiving_df, accounts):
        #账户的付款特征
        node_df = self.paid_currency_aggregate(currency_ls, paying_df, accounts)
        #账户的收款特征
        node_df = self.received_currency_aggregate(currency_ls, receiving_df, node_df)
        #账户的标签
        node_label = torch.from_numpy(node_df[self._self._mp.label].values).to(torch.float)
        
        #形成数据与标签
        node_df = node_df.drop([self._self._mp.id11, self._self._mp.label], axis=1)
        node_df["Bank"] = node_df["Bank"].astype("float32") / 10000.0
        print(node_df[:3],node_df.shape)
        node_df = torch.from_numpy(node_df.values).to(torch.float)
        return node_df, node_label

    def get_edge_df(self, accounts, df):
        accounts = accounts.reset_index(drop=True)
        accounts['ID'] = accounts.index
        mapping_dict = dict(zip(accounts[self._self._mp.id11], accounts['ID']))
        df['From'] = df[self._self._mp.id11].map(mapping_dict)
        df['To'] = df[self._self._mp.id12].map(mapping_dict)
        df = df.drop([self._self._mp.id11, self._self._mp.id12, self._self._mp.bank11, self._self._mp.bank12], axis=1)

        edge_index = torch.stack([torch.from_numpy(df['From'].values), torch.from_numpy(df['To'].values)], dim=0)

        df = df.drop([self._self._mp.label, 'From', 'To'], axis=1)
        print(df[:3])

        edge_attr = torch.from_numpy(df.values).to(torch.float)
        print("edge_attr:\n",edge_attr[:3])
        return edge_attr, edge_index
    

    def deal(self, df, save_path):
        df, receiving_df, paying_df, currency_ls = self.preprocess(df)
        accounts = self.get_all_account(df)
        print("accounts.shape:",accounts.shape)
        node_attr, node_label = self.get_node_attr(currency_ls, paying_df,receiving_df, accounts)
        edge_attr, edge_index = self.get_edge_df(accounts, df)
        pkl_save((node_attr, node_label,edge_attr, edge_index),file_path=save_path, weights_only=False)



class Tu:
    def __init__(self,mp=mp):
        self._mp = mp 

    def preprocess(self,df):
        """原始交易数据分类及类别统计
        - 交易：按账户排序
        - 付款账户：ID，金额，类别等特征，后续会单独进行特征处理
        - 收款账户：ID, 金额，类别等特征，后续会单独进行特征处理
        - 币种类别：后续会统计账户在该类别上的金额特征
        
        """
        # if len(self._mp.drop_cols)>0:
        #     df = df.drop(columns=self._mp.drop_cols)
        df[self._mp.id11] = df[self._mp.bank11].astype(str) + '_' + df[self._mp.id11]
        df[self._mp.id12] = df[self._mp.bank12].astype(str) + '_' + df[self._mp.id12]
        df = df.sort_values(by=[self._mp.id11])
        print(df[:3])
        receiving_df = df[[self._mp.id12, self._mp.amt2, self._mp.currency2]]
        paying_df = df[[self._mp.id11, self._mp.amt1, self._mp.currency1]]
        receiving_df = receiving_df.rename({self._mp.id12: self._mp.id11}, axis=1)
        currency_ls = sorted(df[self._mp.currency2].unique())

        return df, receiving_df, paying_df, currency_ls

    def get_all_account(self,df):
        ldf = df[[self._mp.id11, self._mp.bank11]]
        rdf = df[[self._mp.id12, self._mp.bank12]]
        suspicious = df[df[self._mp.label]==1]
        s1 = suspicious[[self._mp.id11, self._mp.label]]
        s2 = suspicious[[self._mp.id12, self._mp.label]]
        s2 = s2.rename({self._mp.id12: self._mp.id11}, axis=1)
        suspicious = pd.concat([s1, s2], join='outer')
        suspicious = suspicious.drop_duplicates()

        ldf = ldf.rename({self._mp.bank11: 'Bank'}, axis=1)
        rdf = rdf.rename({self._mp.id12: self._mp.id11, self._mp.bank12: 'Bank'}, axis=1)
        df = pd.concat([ldf, rdf], join='outer')
        df = df.drop_duplicates()

        df[self._mp.label] = 0
        df.set_index(self._mp.id11, inplace=True)
        df.update(suspicious.set_index(self._mp.id11))
        df = df.reset_index()
        return df

    def add_acc_label(self,df):
        ldf = df[[self._mp.id11, self._mp.bank11]]
        rdf = df[[self._mp.id12, self._mp.bank12]]
        suspicious = df[df[self._mp.label]==1]
        s1 = suspicious[[self._mp.id11, self._mp.label]]
        s2 = suspicious[[self._mp.id12, self._mp.label]]
        s2 = s2.rename({self._mp.id12: self._mp.id11}, axis=1)
        suspicious = pd.concat([s1, s2], join='outer')
        suspicious = suspicious.drop_duplicates()

        ldf = ldf.rename({self._mp.bank11: 'Bank'}, axis=1)
        rdf = rdf.rename({self._mp.id12: self._mp.id11, self._mp.bank12: 'Bank'}, axis=1)
        df = pd.concat([ldf, rdf], join='outer')
        df = df.drop_duplicates()

        df[self._mp.label] = 0
        df.set_index(self._mp.id11, inplace=True)
        df.update(suspicious.set_index(self._mp.id11))
        df = df.reset_index()
        return df

    def get_edge_df(self,accounts, df):
        accounts = accounts.reset_index(drop=True)
        accounts['ID'] = accounts.index
        mapping_dict = dict(zip(accounts[self._mp.id11], accounts['ID']))
        df['From'] = df[self._mp.id11].map(mapping_dict)
        df['To'] = df[self._mp.id12].map(mapping_dict)
        df = df.drop([self._mp.id11, self._mp.id12, self._mp.bank11, self._mp.bank12], axis=1)

        edge_index = torch.stack([torch.from_numpy(df['From'].values), torch.from_numpy(df['To'].values)], dim=0)

        df = df.drop([self._mp.label, 'From', 'To'], axis=1)
        # 删除所有非数字列
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        df = df[numeric_cols]
        print(df.columns)

        
        # 删除所有非数字列
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        df = df[numeric_cols]
        print(df.columns)
        
        edge_attr = torch.from_numpy(df.values).to(torch.float)
        return edge_attr, edge_index

    def paid_currency_aggregate(self,currency_ls, paying_df, accounts):
        for i in currency_ls:
            # temp = paying_df[paying_df[self._mp.currency1] == i]
            # accounts['avg paid '+str(i)] = temp[self._mp.amt1].groupby(temp[self._mp.id11]).transform('mean')

            # 按 id11 分组计算均值，得到 Series (索引为 id11 的值)
            avg_by_account = paying_df[paying_df[self._mp.currency1] == i] \
                            .groupby(self._mp.id11)[self._mp.amt1].mean()
            # 将均值映射到 accounts 表中
            accounts['avg paid '+str(i)] = accounts[self._mp.id11].map(avg_by_account).fillna(0)
            
        return accounts

    def received_currency_aggregate(self,currency_ls, receiving_df, accounts):
        for i in currency_ls:
            # temp = receiving_df[receiving_df[self._mp.currency2] == i]
            # accounts['avg received '+str(i)] = temp[self._mp.amt2].groupby(temp[self._mp.id11]).transform('mean')

            # 按 id11 分组计算均值，得到 Series (索引为 id11 的值)
            avg_by_account = receiving_df[receiving_df[self._mp.currency2] == i] \
                            .groupby(self._mp.id11)[self._mp.amt2].mean()
            # 将均值映射到 accounts 表中
            accounts['avg received '+str(i)] = accounts[self._mp.id11].map(avg_by_account).fillna(0)
            
        accounts = accounts.fillna(0)
        return accounts

    def get_node_attr(self, currency_ls, paying_df,receiving_df, accounts):
        node_df = self.paid_currency_aggregate(currency_ls, paying_df, accounts)
        node_df = self.received_currency_aggregate(currency_ls, receiving_df, node_df)
        node_label = torch.from_numpy(node_df[self._mp.label].values).to(torch.float)
        node_df = node_df.drop([self._mp.id11, self._mp.label], axis=1)
        node_df = torch.from_numpy(node_df.values).to(torch.float)
        return node_df, node_label
    



import pandas as pd
import torch
from torch_geometric.data import Data
import os


class GraphDataBuilder:
    """
    图数据构建器：支持从两个文件构建图数据
        - 账户文件: 包含每个账户的特征与标签 (node_attr, node_label)
        - 交易文件: 包含转账记录 (用于 edge_index 和 edge_attr)

    要求：
        - 账户文件中的 ID 必须能覆盖交易文件中的所有涉及账户
        - ID 建议格式为 "Bank_Account" 或已拼接的唯一标识
    """

    def __init__(self, 
                    account_id_col='Account', 
                    account_label_col=None,
                    account_feature_cols=None,
                    trans_from_col='From', 
                    trans_to_col='To',
                    trains_time_col=None,
                    pc:ParamConfig=None):
        """
        参数：
            account_id_col: 账户文件中表示账户ID的列名（也用于交易中的发送方/接收方）
            account_label_col: 账户文件中标签列名
            account_feature_cols: 账户特征列列表。若为None，则使用除ID、label外的所有数值列
            trans_from_col: 交易文件中“付款方”列名
            trans_to_col: 交易文件中“收款方”列名
            trains_time_col: 时间列（可选，用于排序或分组）
            
        example:
        --------------------------------------
        from tpf.data.tu11 import GraphDataBuilder

        builder = GraphDataBuilder(
            account_id_col='Account',
            account_label_col='Is Laundering',
            account_feature_cols=['avg_paid_CNY', 'avg_received_USD', 'risk_score'],
            trans_from_col='From',
            trans_to_col='To',
            trains_time_col='Timestamp'
        )

        acc_file = "/wks/datasets/txt/jiaoyi/account11.csv"
        tra_file = "/wks/datasets/txt/jiaoyi/transaction11.csv"
        data, meta = builder.load_and_build(
            account_file=acc_file,
            transaction_file=tra_file,
            file_type='csv'
        )

        """
        self.account_id_col = account_id_col
        self.from_col = trans_from_col
        self.to_col = trans_to_col
        self.label_col = account_label_col
        self.feature_cols = account_feature_cols
        self.time_col = trains_time_col
        
        # 存储中间结果
        self.accounts_df = None
        self.transactions_df = None
        self.node_mapping = None
        self.pc = pc
    def lg(self,msg):
        if self.pc is None:
            print(msg)
        else:
            self.pc.lg(msg)


    def load_and_build(self, df_acc = None, account_file=None, 
                       df_tra=None, transaction_file=None, file_type='csv',debug=False):
        """
        主接口：加载两个文件并生成 PyG 的 Data 对象

        Args:
            account_file: 账户特征文件路径
            transaction_file: 交易流水文件路径
            file_type: 文件类型 ('csv', 'xlsx', 'pkl' 等)

        Returns:
            data (Data): PyG Data 对象
            metadata (dict): 包含 mapping、accounts_df 等调试信息
        """
        # --- 1. 加载文件 ---
        if df_acc is None:
            self.accounts_df = self._read_file(account_file, file_type)
        else:
            self.accounts_df = df_acc
        if df_tra is None:
            self.transactions_df = self._read_file(transaction_file, file_type)
        else:
            self.transactions_df = df_tra
     

        # --- 2. 预处理 & 校验 ---
        self.lg("预处理 & 校验 ---...")
        self._validate_data()
        self._normalize_account_ids()  # 统一格式

        # --- 3. 构建节点映射表 ---
        self.lg("构建节点映射表...")
        self.node_mapping = {acc: idx for idx, acc in enumerate(self.accounts_df[self.account_id_col])}
        
        # 检查交易中是否有不在账户文件中的账户
        all_involved_accounts = set(self.transactions_df[self.from_col].unique()) | \
                                set(self.transactions_df[self.to_col].unique())
        known_accounts = set(self.accounts_df[self.account_id_col])
        unknown = all_involved_accounts - known_accounts
        
        if unknown:
            self.lg(f"以下账户出现在交易中但未在账户文件中找到: {list(unknown)[:3]}...")
            
            if debug:
                # 删除交易中未存在于账户文件中的账户数据
                valid_transactions = self.transactions_df[
                    self.transactions_df[self.from_col].isin(known_accounts) &
                    self.transactions_df[self.to_col].isin(known_accounts)
                ]
                removed_count = len(self.transactions_df) - len(valid_transactions)
                if removed_count > 0:
                    self.lg(f"Debug模式：已删除 {removed_count} 条包含未知账户的交易记录")
                self.transactions_df = valid_transactions 
            else:
                raise ValueError(f"以下账户出现在交易中但未在账户文件中找到: {list(unknown)[:3]}")
        # --- 4. 构建节点特征和标签 ---
        self.lg("正在构建节点特征和标签...")
        node_attr = self._build_node_attr()
        
        self.lg("正在构建节点标签...")
        
        # --- 5. 构建边索引和边特征 ---
        self.lg("正在构建边索引和边特征...")
        edge_index = self._build_edge_index()
        edge_attr = self._build_edge_attr()

        # --- 6. 返回图数据 ---
        self.lg("返回图数据...")
        if self.label_col is not None:
            node_label = torch.from_numpy(self.accounts_df[self.label_col].values).float()

            data = Data(
                x=node_attr,
                y=node_label,
                edge_index=edge_index,
                edge_attr=edge_attr
            )
        else:
            data = Data(
                x=node_attr,
                edge_index=edge_index,
                edge_attr=edge_attr
            )

        metadata = {
            'acc_df': self.accounts_df,
            'tra_df': self.transactions_df,
            'node_mapping': self.node_mapping,
            'num_nodes': len(self.accounts_df),
            'num_edges': len(self.transactions_df)
        }

        return data, metadata


    def _read_file(self, filepath, file_type):
        """通用文件读取"""
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"文件不存在: {filepath}")
        
        if file_type == 'csv':
            return pd.read_csv(filepath)
        elif file_type == 'xlsx':
            return pd.read_excel(filepath)
        elif file_type == 'pkl':
            return pd.read_pickle(filepath)
        else:
            raise ValueError(f"不支持的文件类型: {file_type}")


    def _validate_data(self):
        """校验字段是否存在"""
        if self.label_col is None:
            required_cols_acc = [self.account_id_col]
        else:
            required_cols_acc = [self.account_id_col, self.label_col]
        
        missing_acc = [col for col in required_cols_acc if col not in self.accounts_df.columns]
        if missing_acc:
            raise KeyError(f"账户文件缺少必要列: {missing_acc}")

        required_cols_trans = [self.from_col, self.to_col]
        missing_trans = [col for col in required_cols_trans if col not in self.transactions_df.columns]
        if missing_trans:
            raise KeyError(f"交易文件缺少必要列: {missing_trans}")


    def _normalize_account_ids(self):
        """确保所有 ID 列都转为字符串并去空格"""
        def clean_id(series):
            return series.astype(str).str.strip()

        self.accounts_df[self.account_id_col] = clean_id(self.accounts_df[self.account_id_col])
        self.transactions_df[self.from_col] = clean_id(self.transactions_df[self.from_col])
        self.transactions_df[self.to_col] = clean_id(self.transactions_df[self.to_col])


    def _build_node_attr(self):
        """从账户文件提取节点特征"""
        if self.feature_cols is None:
            # 默认选择数值型特征（排除 ID 和 label）
            exclude_cols = {self.account_id_col, self.label_col}
            numeric_cols = self.accounts_df.select_dtypes(include=['number']).columns
            self.feature_cols = [c for c in numeric_cols if c not in exclude_cols]

        if not self.feature_cols:
            raise ValueError("没有可用的节点特征列，请指定 feature_cols")

        _feature_cols = sorted(self.feature_cols)
        X = self.accounts_df[_feature_cols].fillna(0).values
        
        return torch.from_numpy(X).to(torch.float)


    def _build_edge_index(self):
        """构造 edge_index [2, num_edges]"""
        src = self.transactions_df[self.from_col].map(self.node_mapping)
        dst = self.transactions_df[self.to_col].map(self.node_mapping)

        if src.isna().any() or dst.isna().any():
            raise ValueError("映射失败：某些账户未在 node_mapping 中")

        edge_index = torch.stack([
            torch.from_numpy(src.values),
            torch.from_numpy(dst.values)
        ], dim=0)

        return edge_index.to(torch.long)


    def _build_edge_attr(self):
        """从交易数据中提取边特征（仅数值列）"""
        drop_cols = [self.from_col, self.to_col]
        if self.time_col:
            # 检查time_col列是否为数字类型，如果是数字类型则不删除
            if self.time_col in self.transactions_df.columns and not pd.api.types.is_numeric_dtype(self.transactions_df[self.time_col]):
                drop_cols.append(self.time_col)

        feature_df = self.transactions_df.drop(columns=drop_cols, errors='ignore')
        numeric_df = feature_df.select_dtypes(include=[float, int])

        if numeric_df.empty:
            # 若无有效数值列，则返回 None 或全零向量
            print("警告：未找到有效的边特征，edge_attr 将设为 None")
            return None

        # 按列的升序处理numeric_df数据列
        numeric_df = numeric_df[sorted(numeric_df.columns)]
        edge_attr = torch.from_numpy(numeric_df.fillna(0).values).to(torch.float)

        return edge_attr