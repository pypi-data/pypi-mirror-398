import os
import numpy as np
import pandas as pd

# Check if torch is available
try:
    import torch
    from torch import nn
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

# Define IndexEmbed only if torch is available
if TORCH_AVAILABLE:
    class IndexEmbed(nn.Module):
        def __init__(self, file_pre=None, log_func=None):
            """使用文件保存编码，第二次加载时默认从文件中读取;因为要固定参数，因此不参与梯度计算
            <=10：  2，
            <=100： 3，
            <=1000：4，
            <=100W: 5
            - num_embeddings与embedding_dim不为None时，则手工指定
            - file_pre:最终文件保存格式为 f"embed_{num_embeddings}_{embedding_dim}",为None则表示不记录文件

            """
            super().__init__()
            torch.manual_seed(73)
            self.file_pre = file_pre

            with torch.no_grad():
                self._embed2 = self._gen_embedding(num_embeddings=10,     embedding_dim=2,padding_idx=0)
                self._embed3 = self._gen_embedding(num_embeddings=100,    embedding_dim=3,padding_idx=0)
                self._embed4 = self._gen_embedding(num_embeddings=1000,   embedding_dim=4,padding_idx=0)
                self._embed5 = self._gen_embedding(num_embeddings=1000000,embedding_dim=5,padding_idx=0)
            self._log_func = log_func

        def lg(self,msg):
            if self._log_func is not None:
                self._log_func(msg)

        def _gen_embedding(self,num_embeddings=8,
                            embedding_dim=3,
                            padding_idx=0):
            using_file = True
            if self.file_pre is None:
                # embed_path = f"embed_{num_embeddings}_{embedding_dim}"
                using_file = False
            else:
                embed_path = f"{self.file_pre}_{num_embeddings}_{embedding_dim}"

            if using_file and os.path.exists(embed_path):
                # 从磁盘加载
                # embedding = joblib.load(embed_path)
                embedding = torch.load(embed_path, weights_only=False)
                return embedding

            with torch.no_grad():
                embedding = nn.Embedding(num_embeddings=num_embeddings,
                                embedding_dim=embedding_dim,
                                padding_idx=padding_idx)

            # joblib.dump(embedding, embed_path)
            if using_file:
                torch.save(embedding, embed_path)
            return embedding


        def embedding(self,data_index, embedding_dim=2, num_embeddings=None):
            """
            - 映射到2，3，4，5维度时固定了最大索引个数，不需要手工指定；相当于固定了最常用的几个映射方法；
            - 若需要更加灵活的方式，指定num_embeddings即可
            - 所有编码方式都会记录到文件，若存在文件则尤其加载文件
            """
            # self.lg(f"embedding func:embedding_dim={embedding_dim},num_embeddings={num_embeddings}")
            if not isinstance(data_index,torch.Tensor):
                data_index = torch.tensor(data_index)

            embed = None
            # self.lg(f"embedding_dim={embedding_dim},num_embeddings=10:{embedding_dim==2}")
            with torch.no_grad():
                if embedding_dim==2:
                    # self.lg(f"num_embeddings=10")
                    embed = self._embed2(data_index)
                elif embedding_dim==3:
                    embed = self._embed3(data_index)
                elif embedding_dim==4:
                    embed = self._embed4(data_index)
                elif embedding_dim==5:
                    embed = self._embed5(data_index)
                elif num_embeddings is not None:
                    _embed_model = self._gen_embedding(num_embeddings=num_embeddings, embedding_dim=embedding_dim,padding_idx=0)
                    embed = _embed_model(data_index)
            return embed

        def forward(self, data_index, embedding_dim=2, num_embeddings=None):
            embed = self.embedding(data_index, embedding_dim=embedding_dim, num_embeddings=num_embeddings)
            return embed
else:
    # Fallback placeholder class when torch is not available
    class IndexEmbed:
        def __init__(self, file_pre=None, log_func=None):
            raise ImportError("PyTorch is not installed. Please install torch to use IndexEmbed embedding class.")

        def embedding(self, data_index, embedding_dim=2, num_embeddings=None):
            raise ImportError("PyTorch is not installed. Please install torch to use IndexEmbed embedding class.")

        def forward(self, data_index, embedding_dim=2, num_embeddings=None):
            raise ImportError("PyTorch is not installed. Please install torch to use IndexEmbed embedding class.")

# Define ClsIndexEmbed only if torch is available
if TORCH_AVAILABLE:
    class ClsIndexEmbed(nn.Module):
        def __init__(self, file_pre=None, log_func=None, nan_to_zero=False):
            """类别索引Embedding"""
            super().__init__()

            # 初始化embedding工具
            self._embed = IndexEmbed(file_pre=file_pre,log_func=log_func)
            self._log_func = log_func
            self._nan_to_zero = nan_to_zero

        def lg(self,msg):
            if self._log_func is not None:
                self._log_func(msg)


        # 定义embedding函数
        def _embed_classify_type(self, indices, embedding_dim=3, num_embeddings=None, nan_to_zero=False):
            """定义embedding函数
            - 将所有的类别+1，然后将空值替换为0，以及未来的所有未知的值，编码为0
            """
            #所有类别+1，NaN值以及未来的所有未知的值，编码为0
            if nan_to_zero:
                indices += 1
                indices = np.nan_to_num(indices, nan=0)  # 替换 NaN

            indices_array = np.array(indices, dtype=np.int64)

            try:
                embedded = self._embed(indices_array, embedding_dim=embedding_dim, num_embeddings=num_embeddings)
            except  Exception as e:
                self.lg(f"{e}")
                self.lg(f"<=10:2,<=100:3,<=1000:4,<=100W:5,其余需要手工指定embedding_dim，num_embeddings,实际index={indices_array},embedding_dim={embedding_dim}，请检查类别划分是否正确")
            return embedded.tolist()  # 转换为list以便存储在DataFrame中


        def cls_index_embeding(self, df, cls_dim_dict, num_embeddings=None,nan_to_zero=False):
            """将数据表中的类别按指定的维度embedding
            - cls_vec_dict：{'is_feature_value_535': 2}表示将df数表中的is_feature_value_535 embedding到2维向量中
              - 同时删除is_feature_value_535，添加新列，删除旧列
            - 默认规则
              - <=10:2,<=100:3,<=1000:4,<=100W:5,其余需要手工指定embedding_dim，num_embeddings
              - num_embeddings：默认为None时(没有num_embeddings时)走上面的规则，指定具体数字则指定的数字处理
            """
            drop_cols = []
            df_cols = df.columns.tolist()
            for col_name,dim in cls_dim_dict.items():

                if col_name not in df_cols:
                    continue
                if not isinstance(dim,int):
                    dim = int(dim)
                msg = f"begin deal {col_name,dim}"
                self.lg(msg)
                # 应用embedding并添加到数据表
                tmp_embedd_col = f"{col_name}_embedded"
                drop_cols.append(tmp_embedd_col)

                df_tmp1 = df[col_name]
                self.lg(f"embedding start ... len:{len(df_tmp1)},embeding dim:{dim,type(dim)}")

                df[tmp_embedd_col] = df_tmp1.apply(
                    lambda x: self._embed_classify_type(x, embedding_dim=dim, num_embeddings=num_embeddings,nan_to_zero=nan_to_zero)
                )

                # 将embedding结果拆分成单独的列
                split_cols = []
                for i in range(1,dim+1):
                    split_cols.append(f"{col_name}_{i}")
                embedded_cols = pd.DataFrame(
                    df[tmp_embedd_col].tolist(),
                    columns = split_cols
                )
                df = pd.concat([df, embedded_cols], axis=1)
                drop_cols = [col_name]+drop_cols
            df = df.drop(columns=drop_cols)
            return df

        def forward(self, df, cls_dim_dict, num_embeddings=None):
            """将数据表中存在于cls_dim_dict的类别按指定的维度embedding
            - cls_vec_dict：{'is_feature_value_535': 2}表示将df数表中的is_feature_value_535 embedding到2维向量中
              - 同时删除is_feature_value_535，添加新列，删除旧列
            - nan_to_zero:默认为False，不对空值做处理；非None，将所有的类别+1，然后将空值替换为0，以及未来的所有未知的值，编码为0

            - 默认规则
              - <=10:2,<=100:3,<=1000:4,<=100W:5,其余需要手工指定embedding_dim，num_embeddings
              - num_embeddings：默认为None时(没有num_embeddings时)走上面的规则，指定具体数字则指定的数字处理



            examples
            ---------------------------------
            from tpf.nlp import ClsIndexEmbed
            cls_dim_dict = {
                'is_feature_value_535': 3,
                'is_feature_value_536': 2
            }

            cie = ClsIndexEmbed(file_pre=embed_file_pre, log_func=lg, nan_to_zero=True)
            cie = ClsIndexEmbed()
            df =cie(df,cls_dim_dict)

            """
            df = self.cls_index_embeding(df, cls_dim_dict, num_embeddings=num_embeddings,nan_to_zero=self._nan_to_zero)
            return df
else:
    # Fallback placeholder class when torch is not available
    class ClsIndexEmbed:
        def __init__(self, file_pre=None, log_func=None, nan_to_zero=False):
            raise ImportError("PyTorch is not installed. Please install torch to use ClsIndexEmbed class.")

        def cls_index_embeding(self, df, cls_dim_dict, num_embeddings=None, nan_to_zero=False):
            raise ImportError("PyTorch is not installed. Please install torch to use ClsIndexEmbed class.")

        def forward(self, df, cls_dim_dict, num_embeddings=None):
            raise ImportError("PyTorch is not installed. Please install torch to use ClsIndexEmbed class.")