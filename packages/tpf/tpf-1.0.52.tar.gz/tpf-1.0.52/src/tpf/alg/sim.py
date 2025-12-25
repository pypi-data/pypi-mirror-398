
import numpy as np
import torch
from torch import nn

class MaxSimilarity(nn.Module):
    def __init__(self):
        """计算矩阵x1中每个行向量与矩阵x2中每个行向量的相似度，并提取x2中最相似行的相似度大小

        """
        super().__init__()

    def forward(self, x1, x2):
        """计算矩阵x1中每个行向量与矩阵x2中每个行向量的相似度，并提取x2中最相似行的相似度大小
        - x1:要求相似度的数据
        - x2:被求相似度的数据
        
        return
        -------------------------
        1维列表：x1中的每个行向量都有一个分值，它是该行向量与x2中每个行向量相似度中的最大值
        
        examples 
        -------------------------
        import torch
        from tpf.alg.sim import MaxSimilarity

        X = torch.tensor([
            [0.3745, 0.9507, 0.7320],
            [0.5987, 0.1560, 0.1560],
            [0.0581, 0.8662, 0.6011],
            [0.7081, 0.0206, 0.9699],
            [0.8324, 0.2123, 0.1818],
            [0.1834, 0.3042, 0.5248],
            [0.4319, 0.2912, 0.6119]]).float()

        x1 = X[:2,:]
        x2 = X[2:,:]

        model = MaxSimilarity()
        sim = model(x1,x2)
        sim  #tensor([0.9684, 0.9992])

        
        """
        if not isinstance(x1,torch.Tensor):
            x1 = torch.tensor(x1)
        if not isinstance(x2,torch.Tensor):  
            x2 = torch.tensor(x2)
        if x1.ndim !=2 or x2.ndim != 2:
            raise Exception(f"要求输入数据的维度皆为2，实际数据维x1:{x1.ndim},x2:{x2.ndim}")
        
        # 计算 x1 和 x2 的行向量的余弦相似度矩阵，x1要让行向量成为(1,n)的矩阵,于是x2为了对上x1中的元素就在0位置上新增维度
        cosine_sim_matrix = torch.cosine_similarity(x1.unsqueeze(1), x2.unsqueeze(0), dim=2)

        # 提取 x1 中每个行向量与 x2 中最相似行的相似度大小
        max_similarities, _ = torch.max(cosine_sim_matrix, dim=1)
        return max_similarities
            


# 计算 x1 和 x2 的行向量的余弦相似度矩阵
def cosine_similarity_matrix(x1, x2):
    """numpy求解余弦相似度"""
    # 计算 x1 和 x2 的行向量的模
    norm_x1 = np.linalg.norm(x1, axis=1, keepdims=True)
    norm_x2 = np.linalg.norm(x2, axis=1, keepdims=True)
    
    # 计算 x1 和 x2 的行向量的点积
    dot_product = np.dot(x1, x2.T)
    
    # 计算余弦相似度矩阵
    cosine_sim_matrix = dot_product / (norm_x1 * norm_x2.T)
    return cosine_sim_matrix



class TopSim(nn.Module):
    def __init__(self):
        """计算矩阵x1中每个行向量与矩阵x2中每个行向量的相似度，并提取x2中最相似行的相似度及索引 
        
        examples 
        -------------------------
        import torch
        from tpf.alg.sim import TopSim

        X = torch.tensor([
            [0.3745, 0.9507, 0.7320],
            [0.5987, 0.1560, 0.1560],
            [0.0581, 0.8662, 0.6011],
            [0.7081, 0.0206, 0.9699],
            [0.8324, 0.2123, 0.1818],
            [0.1834, 0.3042, 0.5248],
            [0.4319, 0.2912, 0.6119]]).float()

        x1 = X[:2,:]
        x2 = X[2:,:]

        model = TopSim()
        sim,index = model(x1,x2,n=1)
        
        sim_data = x2[index] # 3维数据，sim_data[0]存放的是x1中索引为0的数据对就的x2中的最相似的n个数据列表,sim_data[0][0]是最相似的，sim_data[0][1]是第2个最相似的
        
        """
        super().__init__()

    def forward(self, x1, x2, n=3):
        """计算矩阵x1中每个行向量与矩阵x2中每个行向量的相似度，并提取x2中最相似行的相似度及索引
        - x1:要求相似度的数据
        - x2:被求相似度的数据
        
        return
        -------------------------
        相似度列表：x1中的每个行向量都有一个分值，它是该行向量与x2中每个行向量相似度中的top n个值 
        数据列表：x2中对应的相似的数据
       
        """
        if not isinstance(x1,torch.Tensor):
            x1 = torch.tensor(x1)
        if not isinstance(x2,torch.Tensor):  
            x2 = torch.tensor(x2)
        if x1.ndim !=2 or x2.ndim != 2:
            raise Exception(f"要求输入数据的维度皆为2，实际数据维x1:{x1.ndim},x2:{x2.ndim}")
        
        # 计算 x1 和 x2 的行向量的余弦相似度矩阵，x1要让行向量成为(1,n)的矩阵,于是x2为了对上x1中的元素就在0位置上新增维度
        cosine_sim_matrix = torch.cosine_similarity(x1.unsqueeze(1), x2.unsqueeze(0), dim=2)

        # 获取前n个最相似的相似度值和索引
        topk_similarities, topk_indices = torch.topk(cosine_sim_matrix, k=n, dim=1)

        return topk_similarities, topk_indices
            