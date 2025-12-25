"""
大模型相关
"""
import numpy as np
from sentence_transformers import CrossEncoder

# 方法1: 使用预训练的Cross-Encoder进行重排序
class Reranker:
    def __init__(self, model_name):
        """
        初始化重排序模型
        model_name可以是:
        - 'BAAI/bge-reranker-large' (中文优化)
        - 'cross-encoder/ms-marco-MiniLM-L-6-v2'
        
        example:
        model = Reranker('BAAI/bge-reranker-large')
                
        import pandas as pd
        df_topk_path = "/ai/wks/tousu/v4/data/tmp/top_k_bm25.csv"
        df25 = pd.read_csv(df_topk_path)
        
        # 进行重排序，针对两列重排序计算分数
        reranked_score = model.rerank_score(df25, use_cols=['query_text','sim_text'],batch_size=100)
        df25['reranked_score'] = reranked_score

        """
        self.model = CrossEncoder(model_name)
    
    def rerank_topk(self, query, texts, labels, top_k=5):
        """
        对候选文本进行重排序,一对多
        
        Args:
            query: 查询文本
            candidates: 候选文本列表
            candidate_labels: 候选标签列表
            top_k: 返回前k个结果
        
        Returns:
            排序后的结果列表
        """
        candidates = np.array(texts)
        candidate_labels = np.array(labels)
        # 创建query-candidate对
        pairs = [[query, candidate] for candidate in candidates]
        
        # 获取相似度分数
        scores = self.model.predict(pairs)
        
        # 组合结果并排序
        results = []
        for i, score in enumerate(scores):
            results.append({
                'text': candidates[i],
                'label': candidate_labels[i],
                'score': score
            })
        
        # 按分数降序排序
        results.sort(key=lambda x: x['score'], reverse=True)
        
        return results[:top_k]

    def rerank_score(self, df, use_cols=[], batch_size = 100):
        """
        对候选文本进行重排序;多对多
        
        Args:
            use_cols:有两个列，第一个是查询文本，第二个是候选文本
        
        Returns:
            得分列表
        """
        df_tmp = df[use_cols]
        pairs = []
        for tup in df_tmp.itertuples(index=False):   # index=True 把索引也带出来
            query = tup[0]
            text = tup[1]
            pairs.append([query,text])
        print(f"总共需要处理 {len(pairs)} 个文本对")
        print(f"第一个样本: {pairs[0]}")

        # 按batch获取相似度分数，每次处理batch_size=100
        scores = []

        try:
            for i in range(0, len(pairs), batch_size):
                batch_pairs = pairs[i:i + batch_size]
                batch_num = i // batch_size + 1
                total_batches = (len(pairs) + batch_size - 1) // batch_size

                print(f"处理批次 {batch_num}/{total_batches}，单个批次大小: {len(batch_pairs)}")

                # 预测当前batch的分数
                batch_scores = self.model.predict(batch_pairs)
                scores.extend(batch_scores)

                # 显示进度
                if (i + batch_size) % 500 == 0 or (i + batch_size) >= len(pairs):
                    processed = min(i + batch_size, len(pairs))
                    progress = processed / len(pairs) * 100
                    print(f"已处理: {processed}/{len(pairs)} ({progress:.1f}%)")

                # 内存清理
                if batch_num % 10 == 0:
                    import gc
                    gc.collect()

            # 转换为numpy数组以便后续处理
            scores = np.array(scores)
            print(f"预测完成，总共处理 {len(scores)} 个样本，分数范围: [{scores.min():.4f}, {scores.max():.4f}]")

        except Exception as e:
            print(f"批量预测过程中发生错误: {str(e)}")
            raise e
        
        return scores




from modelscope import AutoTokenizer, AutoModel
import torch


class TextEmbedding:
    def __init__(self):
        pass

    def init_bge(self,model_path):
        # Load model from HuggingFace Hub
        self.bge_tokenizer = AutoTokenizer.from_pretrained(model_path)
        self.bge_model = AutoModel.from_pretrained(model_path)
        self.bge_model.eval()
    
    def embedding_bge(self, texts, is_norm=True):
        encoded_input = self.bge_tokenizer(texts, padding=True, truncation=True, return_tensors='pt')

        with torch.no_grad():
            model_output = self.bge_model(**encoded_input)
            sentence_embeddings = model_output[0][:, 0]
        if is_norm:
            sentence_embeddings = torch.nn.functional.normalize(sentence_embeddings, p=2, dim=1)
        return sentence_embeddings
    
    @staticmethod
    def normalize(embeddings, p=2, dim=1):
        return torch.nn.functional.normalize(embeddings, p=p, dim=dim)







