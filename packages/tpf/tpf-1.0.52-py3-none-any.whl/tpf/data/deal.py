# -*- coding:utf-8 -*-

import os
import random
import re
import string
import pandas as pd
import numpy as np
import pandas as pd
import numpy as np
import json
import joblib 
from pathlib import Path
from typing import List, Dict, Optional, Callable, Tuple, Any 
from sklearn import preprocessing
from sklearn.model_selection import train_test_split
from sklearn.utils import resample
from tpf.d1 import DataDeal as dt
from tpf.data.read import get_features

from tpf import pkl_save,pkl_load
from tpf.d1 import DataDeal as dt
from tpf.d1 import read,write
from tpf.box.fil import  parentdir
# from tpf.link.toolml import str_pd
# from tpf.link.feature import FeatureEval
# from tpf.link.toolml import null_deal_pandas
# from tpf.link.toolml import std7

from tpf.conf.common import ParamConfig, CommonConfig
from tpf import pkl_save,pkl_load

# Check if torch is available
try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

from tpf import pkl_load,pkl_save
from datetime import date, timedelta
# from tpf.nlp.text import TextEmbedding as tte 

from sklearn.base import BaseEstimator, TransformerMixin

class MinMaxScalerCustom(BaseEstimator, TransformerMixin):
    """自定义 MinMaxScaler，支持动态更新 min/max"""
    def __init__(self):
        self.min_ = None
        self.max_ = None

    def fit(self, X):
        self.min_ = X.min()
        self.max_ = X.max()
        return self

    def transform(self, X):
        return (X - self.min_) / (self.max_ - self.min_)

    def partial_fit(self, X):
        """增量更新 min/max"""
        if self.min_ is None:
            self.min_ = X.min()
            self.max_ = X.max()
        else:
            self.min_ = min(self.min_, X.min())
            self.max_ = max(self.max_, X.max())


class DataDeal():
    def __init__(self):
        """ 
        1. s1_data_classify,字段分类，区分出标识，数字，字符，日期等分类的列 ，不同的列按不同的方式处理
        2. s2_pd_split,s2_data_split,训练集测试集按标签拆分 
        3. s3_min_max_scaler,数字类型归一化处理
        """
        pass
    
    @staticmethod
    def append_csv(new_data, file_path):
        """追加写csv文件，适合小数据量
        
        """
        if os.path.exists(file_path):
            # 读取现有的 CSV 文件
            existing_df = pd.read_csv(file_path)
        
            # 将新数据追加到现有的 DataFrame
            updated_df = pd.concat([existing_df, new_data], ignore_index=True)
        else:
            updated_df = new_data
        
        # 将更新后的 DataFrame 写回到 CSV 文件
        updated_df.to_csv(file_path, index=False)
    
    @staticmethod
    def append_txt(data_base_path,
                    data_new_path=None,row=None):
        """
        以文本方式读取两个CSV文件，并将新文件内容追加到基础文件尾部

        参数:
        data_base_path: 基础CSV文件路径
        data_new_path: 要追加的新CSV文件路径
        row: 要直接追加的单行数据（列表或字符串）

        返回:
        bool: 成功返回True，失败返回False
        """
        try:
            # 当row不为None时，直接将一行数据追加到文件尾部
            if row is not None:
                with open(data_base_path, 'a', encoding='utf-8', newline='') as file:
                    if isinstance(row, list):
                        # 如果是列表，转换为CSV格式字符串
                        line = ','.join(str(item) for item in row)
                    else:
                        # 如果是字符串，直接使用
                        line = str(row)

                    # 确保不以换行符结尾的情况下添加换行符
                    if not line.endswith('\n'):
                        line += '\n'

                    file.write(line)

                print(f"成功将数据行追加到 {data_base_path}")
                return True

            # 如果row为None，按原有逻辑处理文件追加
            if data_new_path is None:
                print("错误: 未提供要追加的数据源")
                return False

            # 检查基础文件是否存在
            import os
            if not os.path.exists(data_base_path):
                # 如果基础文件不存在，确保目录存在并直接复制新文件内容到基础文件
                base_dir = os.path.dirname(data_base_path)
                if base_dir and not os.path.exists(base_dir):
                    os.makedirs(base_dir, exist_ok=True)
                    pc.lg(f"创建目录: {base_dir}")

                pc.lg(f"基础文件 {data_base_path} 不存在，将创建新文件")
                with open(data_new_path, 'r', encoding='utf-8') as new_file:
                    new_content = new_file.read()
                with open(data_base_path, 'w', encoding='utf-8') as output_file:
                    output_file.write(new_content)
                pc.lg(f"成功将 {data_new_path} 复制到 {data_base_path}")
                return True

            # 读取基础文件内容
            with open(data_base_path, 'r', encoding='utf-8') as base_file:
                base_content = base_file.read()

            # 读取新文件内容
            with open(data_new_path, 'r', encoding='utf-8') as new_file:
                new_content = new_file.read()

            # 分离基础文件的标题行和数据行
            base_lines = base_content.split('\n')
            if len(base_lines) < 2:
                print("基础文件格式错误或为空")
                return False

            header = base_lines[0]
            base_data = '\n'.join(base_lines[1:])

            # 分离新文件的标题行和数据行
            new_lines = new_content.split('\n')
            if len(new_lines) < 2:
                print("新文件格式错误或为空")
                return False

            new_header = new_lines[0]
            new_data = '\n'.join(new_lines[1:])

            # 验证标题行是否一致
            if header.strip() != new_header.strip():
                print(f"警告: 文件标题不一致\n基础文件: {header}\n新文件: {new_header}")
                return False

            # 合并内容
            combined_content = header + '\n'
            if base_data.strip():
                combined_content += base_data + '\n'
            if new_data.strip():
                combined_content += new_data + '\n'

            # 写回基础文件
            with open(data_base_path, 'w', encoding='utf-8') as output_file:
                output_file.write(combined_content)

            print(f"成功将 {data_new_path} 内容追加到 {data_base_path}")
            return True

        except FileNotFoundError as e:
            print(f"文件未找到: {e}")
            return False
        except Exception as e:
            print(f"文件追加过程中出现错误: {e}")
            return False

    @staticmethod
    def csv_quchong(col_name,df=None, data_path=None, is_save=False):
        """
        🚀 CSV数据去重处理工具 - 按指定列消除重复记录,保留最后一次出现的列

        ⚡ 核心功能：
        智能化去重工具，支持DataFrame和CSV文件两种输入方式
        通过指定列的值来识别重复记录，保留最后出现的记录
        实现"新数据覆盖旧数据"的增量更新策略，确保数据时效性

        🎯 输入方式（二选一）：
        🔹 DataFrame直处理: 直接传入DataFrame对象，内存操作
        🔹 CSV文件读取: 传入data_path路径，自动读取文件

        ⚙️ 参数配置：

        📊 df (pandas.DataFrame, 可选)
            要去重的DataFrame对象
            与data_path二选一，优先使用df
            常用: deduplicate_csv_data(df=my_dataframe)

        📁 data_path (str, 可选)
            CSV文件路径，当df为None时使用
            支持相对路径和绝对路径
            示例: "data.csv", "/path/to/file.csv"

        💾 is_save (bool)
            是否将结果写回原文件（仅对CSV文件有效）
            False: 内存处理，仅返回DataFrame（推荐用于测试）
            True: 覆盖原文件（生产环境使用）
            默认: False

        🎯 col_name (str)
            去重基准列，必须是数据中存在的列名
            默认: 'text'（适用于文本去重）
            常用: 'text', 'label', 'id', 'user_id', 'order_id'

        📈 算法原理：
        采用 pandas.groupby(col_name).last() 高效算法：
        1. 按 col_name 对数据进行分组
        2. 每组保留最后一条记录（最新数据）
        3. 重置索引保持数据结构完整
        4. 时间复杂度: O(n), 空间复杂度: O(k) (k为唯一值数量)


        📊 返回值：
        ✅ 成功: pandas.DataFrame（已去重的完整数据集）
        ❌ 失败: None（错误信息会打印到控制台）


        💡 使用示例：

        🔧 方式1: DataFrame直处理（推荐）
        >>> import pandas as pd
        >>> # 已有DataFrame
        >>> df_data = pd.read_csv("complaints.csv")
        >>> df_clean = deduplicate_csv_data(df=df_data, col_name='text')
        >>> print(f"去重后: {len(df_clean)} 条记录")

        🔧 方式2: CSV文件处理
        >>> # 直接处理文件
        >>> df_clean = deduplicate_csv_data(data_path="complaints.csv")
        >>> print(f"文件去重后: {len(df_clean)} 条记录")

        🔧 生产环境保存
        >>> # 处理并保存结果
        >>> df_clean = deduplicate_csv_data(
        ...     data_path="complaints.csv",
        ...     col_name='label',
        ...     is_save=True
        ... )
        >>> # 原文件已被更新

        🔧 批量处理模式
        >>> files = ["day1.csv", "day2.csv", "day3.csv"]
        >>> for file in files:
        ...     df = deduplicate_csv_data(data_path=file, col_name='text')
        ...     if df is not None:
        ...         print(f"{file}: {len(df)} 条唯一记录")

        🔧 数据管道集成
        >>> def process_data_pipeline(raw_df):
        ...     # 步骤1: 去重
        ...     df_dedup = deduplicate_csv_data(df=raw_df, col_name='user_id')
        ...
        ...     # 步骤2: 进一步处理
        ...     if df_dedup is not None:
        ...         return df_dedup.groupby('category').agg({
        ...             'amount': 'sum',
        ...             'count': 'len'
        ...         })
        ...     return None

        ⚠️ 注意事项：
        • 去重操作不可逆，重要数据请先备份
        • 大数据量处理时注意内存使用情况
        • 确保去重列的数据质量，避免None值影响
        • is_save=True 会直接覆盖原文件，请谨慎使用
        • DataFrame和data_path同时提供时，优先使用DataFrame
        """
        try:
            if df is None:
                # 读取合并后的CSV文件
                df = pd.read_csv(data_path)
            print(f"原有: {len(df)} 条记录")

            # 按指定列去重，保留最后一次出现的记录(新数据覆盖旧数据)
            if col_name not in df.columns:
                print(f"错误：列 '{col_name}' 不存在于文件中，可用列：{list(df.columns)}")
                return None

            df_deduplicated = df.groupby(col_name, as_index=False).last()
            print(f"去重后记录数: {len(df_deduplicated)}")

            if is_save:
                # 保存去重后的数据
                df_deduplicated.to_csv(data_path, index=False)
                print(f"去重后的数据已保存到: {data_path}")

            return df_deduplicated

        except FileNotFoundError:
            print(f"文件未找到: {data_path}")
            return None
        except Exception as e:
            print(f"去重处理过程中出现错误: {e}")
            return None

    
    @staticmethod
    def columns_by_max_value(df: pd.DataFrame, 
                           condition: str = 'less', 
                           threshold: float = 100,
                           include_numeric_only: bool = True,
                           skipna: bool = True) -> List[str]:
        """
        根据最大值条件获取列名称
        
        参数:
        df: pandas DataFrame
            输入的数据框
        condition: str, 可选 'less', 'less_equal', 'greater', 'greater_equal', 'equal'
            比较条件
        threshold: float, 默认 100
            阈值
        include_numeric_only: bool, 默认 True
            是否只包含数字列
        skipna: bool, 默认 True
            是否忽略NaN值
        
        返回:
        List[str]: 符合条件的列名称列表
        
        
        示例:
        
        # 创建示例数据
        import pandas as pd 
        df = pd.DataFrame({
            'small_values': [10, 20, 30, 40],       # 最大值40 < 100
            'large_values': [150, 200, 50, 300],    # 最大值300 > 100
            'mixed_values': [5, 15, 25, 35],        # 最大值35 < 100
            'string_col': ['a', 'b', 'c', 'd'],     # 非数字列
            'edge_case': [80, 90, 95, 99],          # 最大值99 < 100
            'exactly_100': [10, 50, 100, 30],       # 最大值100 = 100
            'with_nan': [10, np.nan, 30, 40],       # 包含NaN，最大值40 < 100
            'all_nan': [np.nan, np.nan, np.nan, np.nan]     # 全为NaN
        })
        
  
    from tpf.data.deal import DataDeal as dtl
    
    # 使用增强版本
    print("\n使用增强版本:")
    result_less = dtl.columns_by_max_value(df, condition='less', threshold=100)
    result_less_equal = dtl.columns_by_max_value(df, condition='less_equal', threshold=100)
    result_greater = dtl.columns_by_max_value(df, condition='greater', threshold=50)

    print(f"最大值小于100的列: {result_less}")
    print(f"最大值小于等于100的列: {result_less_equal}")
    print(f"最大值大于50的列: {result_greater}")
    
    使用增强版本:
    最大值小于100的列: ['small_values', 'mixed_values', 'edge_case', 'with_nan']
    最大值小于等于100的列: ['small_values', 'mixed_values', 'edge_case', 'exactly_100', 'with_nan']
    最大值大于50的列: ['large_values', 'edge_case', 'exactly_100']
            
        
        """
        
        # 验证条件参数
        valid_conditions = ['less', 'less_equal', 'greater', 'greater_equal', 'equal']
        if condition not in valid_conditions:
            raise ValueError(f"condition must be one of {valid_conditions}")
        
        try:
            # 如果只处理数字列
            if include_numeric_only:
                numeric_df = df.select_dtypes(include=[np.number])
                if numeric_df.empty:
                    return []
                max_values = numeric_df.max(skipna=skipna)
            else:
                max_values = df.apply(lambda x: pd.to_numeric(x, errors='coerce').max(skipna=skipna) 
                                    if x.dtype == 'object' else x.max(skipna=skipna))
            
            # 根据条件筛选
            if condition == 'less':
                mask = max_values < threshold
            elif condition == 'less_equal':
                mask = max_values <= threshold
            elif condition == 'greater':
                mask = max_values > threshold
            elif condition == 'greater_equal':
                mask = max_values >= threshold
            elif condition == 'equal':
                mask = max_values == threshold
            
            result_columns = max_values[mask].index.tolist()
            if result_columns is None or len(result_columns) == 0:
                return []
            
            return result_columns
            
        except Exception as e:
            print(f"Error occurred: {e}")
            return []

    @staticmethod
    def col_split(df, col='key', sep='_', maxsplit=1, prefix=None, suffix=None,
                  drop_original=False, handle_missing='ignore'):
        """
        列拆分，将列按指定分隔符拆分为多个列（优化版本）

        Args:
            df: pandas DataFrame
            col: 要拆分的列名
            sep: 分隔符，支持字符串或正则表达式
            maxsplit: 最大拆分次数，-1表示拆分所有
            prefix: 新列名前缀，默认使用原列名
            suffix: 新列名后缀，默认使用数字序号
            drop_original: 是否删除原列
            handle_missing: 处理缺失值的方式 ('ignore', 'fill_empty', 'drop')

        Returns:
            pandas DataFrame: 拆分后的数据框

        Raises:
            ValueError: 当列不存在或参数无效时
        """
        import pandas as pd
        import numpy as np

        # 输入验证
        if col not in df.columns:
            raise ValueError(f"列 '{col}' 不存在")
        if not isinstance(sep, str):
            raise ValueError("分隔符必须是字符串")
        if handle_missing not in ['ignore', 'fill_empty', 'drop']:
            raise ValueError("handle_missing 必须是 'ignore', 'fill_empty' 或 'drop'")

        # 处理缺失值
        if handle_missing == 'drop':
            df = df.dropna(subset=[col]).copy()
        elif handle_missing == 'fill_empty':
            df = df.fillna({col: ''}).copy()
        else:
            df = df.copy()

        # 优化的拆分逻辑
        if maxsplit == -1:
            # 拆分所有可能的分隔符
            split_data = df[col].str.split(sep, expand=True)
        else:
            # 限制拆分次数，提高性能
            split_data = df[col].str.split(sep, n=maxsplit, expand=True)

        # 设置列名
        num_cols = len(split_data.columns)
        if prefix is None:
            prefix = col

        if suffix is None:
            new_columns = [f"{prefix}_{i+1}" for i in range(num_cols)]
        else:
            new_columns = [f"{prefix}{suffix}" for suffix in range(1, num_cols + 1)]

        split_data.columns = new_columns

        # 合并到原数据框
        result = pd.concat([df, split_data], axis=1)

        # 删除原列（如果需要）
        if drop_original:
            result = result.drop(columns=[col])

        return result
        
    
    
        
    @staticmethod
    def col2index(df, identity=[], classify_type=[], classify_type2=[],
                  dict_file="dict_file.dict", is_pre=False, 
                  word2id=None, start_index=1):
        """类别特征编码：将文本类别转换为数值索引

        该方法是对TextEmbedding.col2index的封装，提供类别特征的数值编码功能。
        支持独立编码和共享编码两种模式，适用于数据预处理和特征工程。
        标识列不会被编码，保持原始值用于数据追踪。

        Args:
            df: 输入数据表，包含需要编码的类别列
            identity: list, 标识列名列表，这些列不会被编码，用于唯一标记数据行
            classify_type: 独立编码的列名列表，如果为空或None则自动推断除数值、日期和标识列外的所有列
            classify_type2: 共享编码组列表，如[['From', 'To']]表示两列共享编码空间
            dict_file: 编码字典保存路径
            is_pre: 是否为推理模式（True=加载已有字典，False=创建新字典）
            word2id: 预加载的编码字典
            start_index: 编码起始索引，默认为1

        Returns:
            DataFrame: 编码后的数据表，类别列替换为数值索引，标识列保持不变，列顺序与输入一致

        Example:
            # 基础使用 - 自动推断类别列，排除标识列
            df_encoded = DataDeal.col2index(
                df,
                identity=['id', 'account_number'],
                dict_file='categories.dict'
            )

            # 独立编码 + 标识列保护
            df_encoded = DataDeal.col2index(
                df,
                identity=['user_id', 'transaction_id'],
                classify_type=['currency', 'payment_type'],
                dict_file='category.dict'
            )

            # 共享编码 + 标识列保护
            df_encoded = DataDeal.col2index(
                df,
                identity=['record_id'],
                classify_type=['transaction_type'],
                classify_type2=[['from_account', 'to_account']],
                dict_file='shared.dict'
            )

            # 完全自动推断 - 自动排除数值列、日期列和标识列
            df_encoded = DataDeal.col2index(
                df,
                identity=['id', 'timestamp'],
                dict_file='auto_inferred.dict'
            )

        Note:
            - 标识列不会被编码，保持原始值用于数据追踪
            - 支持完全自动推断或部分手动指定类别列
            - 列顺序保持：方法会自动保持输入DataFrame的列顺序，确保输出结果的列顺序与输入一致
            - 自动推断时会排除数值类型、日期类型和标识列
        """
        # 初始化参数，确保为列表类型
        identity = identity or []

        # 自动推断类别列：如果classify_type为空或None，则选择除数值类型、日期类型和标识列外的所有列
        if classify_type is None or len(classify_type) == 0:
            # 获取数值类型列
            numeric_cols = df.select_dtypes('number').columns.tolist()
            # 获取日期类型列
            date_cols = df.select_dtypes(['datetime', 'datetimetz', 'datetime64']).columns.tolist()
            # 从所有列中排除数值列、日期列和标识列，剩余的作为类别列
            all_cols = df.columns.tolist()
            classify_type = [col for col in all_cols if col not in numeric_cols and col not in date_cols and col not in identity]
        else:
            # 如果指定了classify_type，则需要从中排除标识列
            classify_type = [col for col in classify_type if col not in identity]

        # 处理共享编码组：从classify_type2的每个组中移除标识列
        if classify_type2:
            filtered_classify_type2 = []
            for group in classify_type2:
                filtered_group = [col for col in group if col not in identity]
                if filtered_group:  # 只保留非空的组
                    filtered_classify_type2.append(filtered_group)
            classify_type2 = filtered_classify_type2

        # 保存原始列顺序，确保返回结果的列顺序与输入一致
        original_columns = df.columns.tolist()

        # 调用TextEmbedding进行实际的编码处理
        TextEmbedding.col2index(df, classify_type=classify_type,
            classify_type2=classify_type2,
            dict_file=dict_file,
            is_pre=is_pre,
            word2id=word2id,
            start_index=start_index)

        # 恢复原始列顺序
        df = df[original_columns] 
        return df

    
    @staticmethod
    def data_classify(data, col_type, pc, dealnull=False,dealstd=False,deallowdata=False,lowdata=10,deallog=False):
        """将pandas数表的类型转换为特定的类型
        - float64转换为float32
        - 布尔转为int64
        - 字符串日期转为pandas日期
        
        
        数据分类处理
        - 日期处理：字符串日期转为pandas 日期
        - object转string
        - 空值处理：数字空全部转为0，字符空全部转为'<PAD>'
        - 布尔处理：布尔0与1全部转为int64
        - 数字处理
            - 格式：全部转float32
            - 边界：极小-舍弃10￥以下交易，极大-重置超过7倍均值的金额
            - 分布：Log10后标准化
            - 最终的数据值不大，并且是以0为中心的正态分布

        - 处理后的数据类型：数字，日期，字符
        -
        
        params
        --------------------------------
        - data:pandas数表
        - col_type:pc参数配置中的col_type
        - pc:参数配置
        - dealnull:是否处理空值
        - dealstd:是否标准化处理
        - deallog:是否对数字列log10处理
        - deallowdata:金额低于10￥的数据全置为0
        
        example
        ----------------------------------
        data_classify_deal(data,pc.col_type_nolable,pc)
        
        """
        column_all = data.columns
        
        
        ### 日期
        date_type = [col for col in col_type.date_type if col in column_all] 
        data = DataDeal.str_pd(data, date_type)
        for col in date_type:
            data[col] = pd.to_datetime(data[col], errors='coerce')  

        ### 数字
        num_type = [col for col in col_type.num_type if col in column_all] 
        data[num_type] = data[num_type].astype(np.float32)
        
        
        bool_type = [col for col in col_type.bool_type if col in column_all]
        data[bool_type] = (data[bool_type].astype(np.float32)).astype(int)  # 为了处理'0.00000000'

        ### 字符-身份标识类
        cname_str_identity = pc.cname_str_identity 
        str_identity = [col for col in column_all if col in cname_str_identity]
        col_type.str_identity = str_identity
        data = DataDeal.str_pd(data,str_identity)

        ### 字符-分类，用于分类的列，比如渠道，交易类型,商户，地区等
        str_classification = [col for col in data.columns if col not in str_identity and col not in num_type and col not in date_type and col not in bool_type]
        col_type.str_classification = str_classification
        data = DataDeal.str_pd(data,str_classification)

        #空值处理
        if dealnull:
            data = DataDeal.null_deal_pandas(data,cname_num_type=num_type,cname_str_type=str_classification,num_padding=0, str_padding = '<PAD>')

        if len(num_type)>0:
            if deallowdata:
                #数字特征-极小值处理
                #将小于10￥的金额全部置为0，即不考虑10￥以下的交易
                for col_name in num_type:
                    data.loc[data[col_name]<lowdata,col_name] = lowdata
            
                #将lowdata以下交易剔除
                data.drop(data[data.CNY_AMT.eq(10)].index, inplace=True)
            if deallog:
                #防止后面特征组合时，两个本来就很大的数据相乘后变为inf
                data[num_type] = np.log10(data[num_type])
        
            if dealstd:
                # 数字特征-归一化及极大值处理
                #需要保存，预测时使用
                means = data[num_type].mean()
                stds = data[num_type].std()
                
                data = DataDeal.std7(data, num_type, means, stds)
        

        return data
        
        
    @staticmethod
    def data_pre_deal(df,fe,date_type,num_type,classify_type,classify_type2=[],bool_type=[],
                  save_file=None,dict_file=None,is_num_std=True, 
                  is_pre=False,num_scaler_file="scaler_num.pkl",
                  date_scaler_file="scaler_date.pkl",max_date='2035-01-01'):
        """相比普通的数据预处理，本方法多了一个类别类型编码；同时数字归一化时，会自动将数字列的极值更新为训练时使用的极值；更适用于批量训练
        - 日期归一化，有文件会自动应用
        - 类型编码，需要指定is_pre=False
        - classify_type2:多列共用一个字典时，其元素为共用同一个字典的列的列表
        - num_scaler_file:如果文件已存在且是训练阶段，则更新元素的极值 
        - fe:特征处理类
        """
        #如果保存过数据，则直接读取
        if save_file and os.path.exists(save_file):
            df = pd.read_csv(save_file)
            return df 


        #字段分类
        print("---------------------------")
        print(f"classify_type={classify_type}")
        df = DataDeal.data_type_change(df, num_type=num_type,classify_type=classify_type,date_type=date_type)

        print("---------------------------")
        print(f"字段分类之后 ,\n{df.info()}")

        
        #类型字段索引编码
        fe.col2index(df,classify_type=classify_type,
                    classify_type2=classify_type2,
                    dict_file=dict_file,
                    is_pre=is_pre,
                    word2id=None)

        print(f"字段索引编码之后 \n{df[:3]}")

        ## 数字归一化
        if is_num_std:
            fe.min_max_scaler(df, num_type=num_type, model_path=num_scaler_file, reuse=True,log10=True)

        ## 日期归一化
        if date_scaler_file is not None or max_date is not None:
            df = DataDeal.min_max_scaler_dt(df,
                date_type=date_type,
                scaler_file=date_scaler_file,
                max_date=max_date,
                adjust=True)
        
        #保存数据
        if save_file:
            df.to_csv(save_file,index=False)
        
        return df 

        
    

    @staticmethod
    def data_dl_deal(df, date_type, num_type, 
                        classify_type, classify_type2=[], bool_type=[],
                    save_file=None,dict_file=None,is_num_std=True, 
                    is_pre=False,num_scaler_file="scaler_num.pkl",
                    date_scaler_file="scaler_date.pkl", max_date='2035-01-01'):
        """对于数字及类别编码，在训练阶段是会自动更新字典的;适用于数据集不全，不断收集批次数据的极值
        - 日期归一化，有文件会自动应用
        - 类型编码，需要指定is_pre=False
        - classify_type2:多列共用一个字典时，其元素为共用同一个字典的列的列表
        - num_scaler_file:如果文件已存在且是训练阶段，则更新元素的极值 
        
        """
        if save_file and os.path.exists(save_file):
            df = pd.read_csv(save_file)
            return df 
        
        if dict_file is None:
            raise Exception("请输入字典文件dict_file的路径")

        
        #字段分类
        print(f"classify_type={classify_type}")
        df = DataDeal.data_type_change(df, num_type=num_type,classify_type=classify_type,date_type=date_type)
        print(df.info())
        

        #类型字段索引编码,如果是训练则保存字典
        DataDeal.col2index(df,classify_type=classify_type,
                    classify_type2=classify_type2,
                    dict_file=dict_file,
                    is_pre=is_pre,
                    word2id=None)


        ## 数字归一化
        if is_num_std:
            # fe.min_max_scaler(df, num_type=pc.col_type.num_type, model_path=num_scaler_file, reuse=True,log10=True)
            DataDeal.min_max_update(df, num_type=num_type,num_scaler_file=num_scaler_file, is_pre=is_pre,log10=True)

        if date_scaler_file is not None or max_date is not None:
            ## 日期归一化
            df = DataDeal.min_max_scaler_dt(df,
                date_type=date_type,
                scaler_file=date_scaler_file,
                max_date=max_date,
                adjust=True)

        if save_file:
            df.to_csv(save_file,index=False)
        
        return df 

    
    @staticmethod
    def data_split_pd(X, y,test_split=0.2, random_state=42):
        """按标签类别等比随机采样，确保测试集中每类标签的数据与训练集保持等比"""
        copied_index = X.index.copy()
        X_test = pd.DataFrame(columns=X.columns)
        y_test = pd.DataFrame()
        unique_labels = y.unique()
        
        for label in unique_labels:
            label_indices = y[y == label].index
            num_samples_to_select = int(len(label_indices) * test_split)
            resampled_indices = resample(label_indices, replace=False, n_samples=num_samples_to_select, random_state=random_state)
            copied_index = copied_index.difference(resampled_indices)
            
            X_label_test = X.loc[resampled_indices]
            y_label_test = y.loc[resampled_indices]
            
            if X_test.shape[0] == 0:
                X_test = X_label_test
                y_test = y_label_test
            else:
                X_test = pd.concat([X_test, X_label_test], ignore_index=True)
                y_test = pd.concat([y_test, y_label_test], ignore_index=True)
                
        X_train = X.loc[copied_index]
        y_train = y.loc[copied_index]
        return X_train, y_train, X_test, y_test

    @staticmethod
    def data_type_change(data,num_type=None,classify_type=None,date_type=None):
        """
        将pandas数表的类型转换为特定的类型

        Args:
            data: pandas DataFrame, 输入的数据表
            num_type: list, 需要转换为数值类型的列名列表，如果为空或None则自动推断所有数值列
            classify_type: list, 需要转换为类别类型的列名列表，如果为空或None则自动推断剩余非数值非日期列
            date_type: list, 需要转换为日期类型的列名列表

        Returns:
            DataFrame: 类型转换后的数据表，列顺序与输入一致

        该方法是特征工程数据预处理的核心步骤，负责统一数据类型：
        - 类别特征列转换为pandas string类型，便于后续的编码处理
        - 数值特征列转换为float64类型，确保数值计算的精度
        - 日期特征列转换为datetime类型，支持时间序列分析


        处理逻辑：
        1. 自动推断数值列：如果num_type为空或None，则自动推断
           - 使用data.select_dtypes('number')选择所有数值类型的列
           - 包括int, float, bool等数值类型，确保数值数据统一处理

        2. 自动推断类别列：如果classify_type为空或None，则自动推断
           - 从所有列中排除num_type和date_type列，剩余的作为类别列
           - 这种方式可以简化调用，无需手动指定所有类别列

        3. 类别列处理：将指定的类别列转换为pandas string类型
           - 使用astype("string")而不是astype(str)，以获得更好的内存效率
           - 通过集合操作确保只处理实际存在的列

        4. 数值列处理：将指定的数值列转换为float64类型
           - float64提供了足够的数值精度，适用于大多数机器学习算法
           - 统一数值类型有助于后续的归一化和标准化处理

        5. 日期列处理：将指定的日期列转换为datetime类型
           - 首先检查是否已经是datetime类型，避免重复转换
           - 使用errors='coerce'参数，无效日期转为NaT而非报错
           - 支持多种日期格式的自动识别和转换

        Note:
            - 该方法不会修改原始DataFrame，而是返回处理后的副本
            - 类型转换是数据清洗和特征工程的重要前置步骤
            - 统一的数据类型有助于提高机器学习模型的稳定性
            - 列顺序保持：方法会自动保持输入DataFrame的列顺序，确保输出结果的列顺序与输入一致

        Example:
            # 定义各类型列
            num_cols = ['amount', 'age', 'score']
            cat_cols = ['gender', 'city', 'product_type']
            date_cols = ['transaction_date', 'birth_date']

            # 执行类型转换
            df_processed = DataDeal.data_type_change(
                df, num_cols, cat_cols, date_cols
            )
        """
        # 初始化参数，确保为列表类型
        date_type = date_type or []

        # 保存原始列顺序，确保返回结果的列顺序与输入一致
        original_columns = data.columns.tolist()

        # 初始化一个空的DataFrame，用于存储处理后的数据
        df = pd.DataFrame()

        # 获取所有列名，用于后续的集合操作
        col_all = data.columns.tolist()

        # 自动推断数值列：如果num_type为空或None，则选择所有数值类型的列
        if num_type is None or len(num_type) == 0:
            num_type = data.select_dtypes('number').columns.tolist()

        # 自动推断类别列：如果classify_type为空或None，则从所有列中排除数值列和日期列
        if classify_type is None or len(classify_type) == 0:
            # 使用集合操作，从所有列中排除数值列和日期列
            exclude_cols = set(num_type) | set(date_type)
            classify_type = list(set(col_all) - exclude_cols)

        # 处理类别类型列 - 转换为string类型
        if len(classify_type)>0:
            # 将类别列转换为pandas string类型（比str类型更节省内存）
            df[classify_type] = data[classify_type].astype("string")

        # 处理数值类型列 - 转换为float64类型
        if len(num_type)>0:
            df[num_type] = data[num_type].astype(np.float64)

        # 处理日期类型列 - 转换为datetime类型
        if len(date_type)>0:
            for col in date_type:
                # 只有当列不是datetime类型时才进行转换，避免重复操作
                if not pd.api.types.is_datetime64_any_dtype(data[col]):
                    # errors='coerce'将无效日期转为NaT(Not a Time)，而不是抛出异常
                    df[col] = pd.to_datetime(data[col], errors='coerce')
                else:
                    # 如果已经是datetime类型，直接复制
                    df[col] = data[col]

        # 恢复原始列顺序
        df = df[original_columns]

        # 返回处理后的DataFrame
        return df

    @staticmethod
    def date_deal(data,date_type=[]):
        """to_datetime处理日期列
        """
        column_all = data.columns
        
        ### 日期
        date_type = [col for col in date_type if col in column_all] 
        # data = str_pd(data, date_type)
        for col in date_type:
            if pd.api.types.is_datetime64_any_dtype(data[col]):
                continue
            data[col] = pd.to_datetime(data[col], errors='coerce') 

    @staticmethod
    def drop_cols(df_all, columns=["dt"]):
        """多余字段删除"""
        # 多了一个dt日期 这里做删除处理
        df_all.drop(columns=columns,inplace=True)

    @staticmethod
    def file_counter(file_path, add_num=0.01, reset0=False, format_float=None, return_int=False, max_float_count=4):
        """临时文件计数器
        - file_path:文本文件路径
        - add_num: 每次读取增加的数值
        - reset0:为True会将文件的数字置为0
        - format_float:指定小数位格式，比如，".2f"，效果类似0.10，最后一位是0也会保留
        -return_int:返回整数
        - max_float_count:最大小数位，最多保留几位小数

        examples
        -------------------------
        file_path = '.tmp_model_count.txt'
        count = file_counter(file_path, add_num=0.01, reset0=False)

        count = file_counter(file_path, add_num=0.01, reset0=False, format_float=".2f")
        """
        if reset0:
            write(0, file_path)

        # 检查文件是否存在
        if not os.path.exists(file_path):
            # 如果文件不存在，则创建文件并写入0
            write(0, file_path)
            current_count = 0
        else:
            # 如果文件存在，则读取文件中的数字，然后+1
            current_count = read(file_path)
            current_count += add_num
            # 将+1后的数字写入文件
            current_count=round(current_count, max_float_count)
            write(current_count, file_path)
        if return_int:
            return round(current_count)
        elif format_float is not None:
            return  f"{current_count:.2f}"

        # 返回+1后的数字
        return  current_count




    @staticmethod
    def getXy(data_path: str,
            label_name: str,
            identity_cols: List[str],
            sep: str = '~',
            is_train: bool = True,
            usecols: Optional[List[str]] = None,
            drop_columns: Optional[List[str]] = None,
            dtype_mapping: Optional[Dict[str, Any]] = None,
            is_categorical_func: Optional[Callable[[str], bool]] = None,
            date_type=[],
            bool_type = [],
            ) -> Tuple[pd.DataFrame, Optional[pd.Series]]:
        
        """
        数据加载与特征提取：从原始数据文件中加载特征数据、标签和字段分类信息
        返回标识列+升序的特征列
        
        该方法是对 get_features 函数的封装，提供简化的接口用于常见的数据加载场景
        
        Parameters:
        -----------
        data_path : str
            数据文件路径，支持 CSV 格式
        label_name : str  
            标签列名，用于提取目标变量
        identity_cols : List[str]
            身份标识列列表，这些列不参与建模但需要保留在结果中
        sep : str, default='~'
            数据文件分隔符，默认为 '~'
        is_train : bool, default=True
            是否为训练模式，True 时提取标签 y，False 时不提取
        usecols : List[str], optional
            指定要读取的列名列表，如果为 None 则读取所有列
        drop_columns : List[str], optional  
            要明确丢弃的列名列表，如临时字段或不需要的列
        dtype_mapping : Dict[str, Any], optional
            强制指定某些列的数据类型，如 {"Amount": "float32", "age": "int32"}
        is_categorical_func : Callable[[str], bool], optional
            判断列是否为类别型的函数，输入列名返回布尔值
            如果为 None，默认使用 "is_" 开头的列作为类别列
            
        Returns:
        --------
        Tuple[pd.DataFrame, Optional[pd.Series]]
            训练模式 (is_train=True): (X, y, col_types) - 特征 DataFrame、标签 Series 和字段类型字典
            预测模式 (is_train=False): (X, NOne,col_types) - 特征 DataFrame 和字段类型字典
            
        Notes:
        ------
        - 返回的 X 包含 identity_cols 列
        - 内部自动推断字段类型：数值型、类别型、布尔型等
        - 支持自定义类别判断逻辑，适应不同数据集的特点
        - 标签列自动从特征中分离，不包含在 X 中
        
        Examples:
        ---------
        # 1. 基本使用 - 训练数据加载
        X, y, col_types = DataDeal.getXy(
            data_path="train_data.csv",
            label_name="Is_Fraud", 
            identity_cols=["Account", "Bank"],
            sep='~',
            is_train=True
        )
        
        # 2. 预测数据加载  
        X_pred, col_types = DataDeal.getXy(
            data_path="test_data.csv",
            label_name="Is_Fraud",
            identity_cols=["Account"], 
            sep='~',
            is_train=False
        )
        
        # 3. 自定义类别判断 + 类型映射
        X, y, col_types = DataDeal.getXy(
            data_path="data.csv",
            label_name="Target",
            identity_cols=["ID"],
            usecols=["ID", "Amount", "risk_flag", "Target"],
            dtype_mapping={"Amount": "float32"},
            is_categorical_func=lambda col: col.endswith("_flag") or col.startswith("is_")
        )
        
        print("Numeric columns:", col_types['num_type'])
        print("Categorical columns:", col_types['classify_type'])
        """

        X, y, col_types = get_features(
            data_path=data_path,
            label_name=label_name,
            identity_cols=identity_cols,
            sep=sep,
            is_categorical_func=is_categorical_func or (lambda c: c.lower().startswith("is_")),
            date_type=date_type,
            bool_type=bool_type,
            usecols=usecols,
            drop_columns=drop_columns,
            dtype_mapping=dtype_mapping,
            is_train=is_train
        )
        return (X, y, col_types) if is_train else (X, None, col_types)

    @staticmethod
    def min_max_scaler(X, num_type=[], model_path=f"min_max_scaler.pkl", 
                       reuse=False, col_sort=True, force_rewrite=False):
        """
        MinMaxScaler归一化处理：将数值特征缩放到[0,1]区间，支持模型复用和自动保存。

        Args:
            X: pandas DataFrame, 输入的数据表
            num_type: list, 需要归一化的数值列名列表，如果为空则自动选择所有数值类型的列
            model_path: str, 归一化模型保存路径，默认为'min_max_scaler.pkl'
            reuse: bool, 是否复用已有模型，False时不保存文件，True时支持模型持久化
            col_sort: bool, 是否对列名进行排序，确保处理顺序的一致性
            force_rewrite: bool, 是否强制重写模型文件，True时总是重新训练并保存模型

        Returns:
            DataFrame: 归一化处理后的数据表

        处理逻辑：
        1. 列选择与验证：
           - 如果num_type为空，自动选择所有数值类型的列
           - 可选列名排序，确保处理顺序的一致性

        2. 模型复用策略：
           - reuse=False：每次重新训练，不保存模型，适用于临时分析
           - reuse=True：检查model_path是否存在，存在则加载复用，不存在则训练并保存
           - force_rewrite=True：强制重新训练并覆盖已有模型，忽略reuse的复用逻辑

        3. 目录安全检查：
           - 确保模型保存目录存在，避免写入失败

        4. 归一化处理：
           - 使用MinMaxScaler将数据缩放到[0,1]区间
           - 保持原始数据的分布特征，仅进行线性变换

        参数详细说明：
        - num_type: 支持自动推断数值列，使用select_dtypes('number')自动识别
        - reuse: False=临时模式(不保存)，True=生产模式(保存/复用)
        - model_path: 模型文件路径，支持自定义命名和路径管理
        - col_sort: 排序确保列处理顺序一致，提高结果的可重现性
        - force_rewrite: True=强制重写模式(总是重新训练)，False=正常模式(遵循reuse逻辑)

        Examples:
            # 基础使用 - 自动选择所有数值列
            X_normalized = DataDeal.min_max_scaler(X)

            # 指定特定列进行归一化
            X_normalized = DataDeal.min_max_scaler(
                X,
                num_type=['amount', 'age', 'score'],
                model_path='financial_scaler.pkl'
            )

            # 训练阶段 - 保存模型供后续使用
            X_train_normalized = DataDeal.min_max_scaler(
                X_train,
                num_type=['feature1', 'feature2'],
                model_path='model/scaler.pkl',
                reuse=True  # 首次训练并保存
            )

            # 测试阶段 - 复用已有模型
            X_test_normalized = DataDeal.min_max_scaler(
                X_test,
                num_type=['feature1', 'feature2'],
                model_path='model/scaler.pkl',
                reuse=True  # 加载已有模型
            )

            # 临时分析 - 不保存模型
            X_temp_normalized = DataDeal.min_max_scaler(
                X,
                reuse=False  # 临时使用，不保存
            )

            # 强制重写 - 重新训练并覆盖已有模型
            X_retrained = DataDeal.min_max_scaler(
                X,
                num_type=['feature1', 'feature2'],
                model_path='model/scaler.pkl',
                reuse=True,
                force_rewrite=True  # 强制重新训练，忽略已有模型
            )

            # 模型更新 - 当数据分布发生变化时强制重写
            X_updated = DataDeal.min_max_scaler(
                X_new_data,
                model_path='model/old_scaler.pkl',
                force_rewrite=True  # 使用新数据重新训练并覆盖
            )

        Note:
            - 归一化后的数据范围在[0,1]之间，保留了原始数据的分布特征
            - 模型复用确保训练集和测试集使用相同的缩放参数，避免数据泄露
            - 建议在生产环境中使用reuse=True以确保数据预处理的一致性
            - force_rewrite=True适用于数据分布变化、模型参数调整或需要重新训练的场景
            - force_rewrite参数优先级高于reuse，当force_rewrite=True时会忽略reuse的复用逻辑
            - 列顺序保持：方法会自动保持输入DataFrame的列顺序，确保输出结果的列顺序与输入一致
        """
        # 调试信息：输出数据类型和形状（注释掉，需要时可取消注释）
        # print(type(X),X.shape)

        # 自动推断数值列：如果未指定，则选择所有数值类型的列
        if len(num_type) == 0:
            num_type = X.select_dtypes('number').columns.tolist()

        # 列名排序：确保处理顺序的一致性，提高结果的可重现性
        if col_sort:
            num_type = sorted(num_type)

        # 目录安全检查：确保模型保存目录存在，避免写入失败
        p_dir = parentdir(model_path)
        if not os.path.exists(p_dir):
            raise Exception(f"The file directory {p_dir} does not exist, unable to write files to it ")

        # 模型复用策略：根据reuse和force_rewrite参数决定模型处理方式
        if force_rewrite:
            # 强制重写模式：总是重新训练并覆盖已有模型
            scaler_train = preprocessing.MinMaxScaler().fit(X[num_type])
            if reuse:  # 只有在reuse=True时才保存模型
                pkl_save(scaler_train, file_path=model_path, use_joblib=True)
        elif reuse:
            if os.path.exists(model_path):
                # 复用模式：加载已保存的归一化模型
                scaler_train = pkl_load(file_path=model_path, use_joblib=True)
            else:
                # 训练模式：拟合新的归一化模型并保存
                scaler_train = preprocessing.MinMaxScaler().fit(X[num_type])
                pkl_save(scaler_train, file_path=model_path, use_joblib=True)
        else:
            # 临时模式：每次重新训练，不保存模型
            scaler_train = preprocessing.MinMaxScaler().fit(X[num_type])

        # 应用归一化转换：将指定列缩放到[0,1]区间
        X[num_type] = scaler_train.transform(X[num_type])

        return X

    @staticmethod 
    def min_max_scaler_log(df, num_type=[], model_path=f"min_max_scaler.pkl", reuse=False,
                       log=False,log2=False,log10=False):
        """针对指定的数字数据类型做min max scaler，通常是float32，float64,int64类型的数据
        
        params
        ---------------------------
        - num_type:需要做归一化的数字列，如果为空，则取数据X的所有列
        - reuse:False就不需要复用，也不会保存文件，此时model_path参数不起作用，比如一些无监督，特征选择等场景
        
        examples
        -------------------------------------------------
        # 训练集数字类型归一化, reuse=True时，首次执行因model_path不存在会保存preprocessing.MinMaxScaler().fit的结果
        ddl.s3_min_max_scaler(X, num_type=pc.col_type.num_type, model_path=pc.scale_path, reuse=True)

        #reuse=True且model_path存在时，直接加载文件，然后transform
        ddl.s3_min_max_scaler(X_test, num_type=pc.col_type.num_type,model_path=pc.scale_path, reuse=True)
        
        """
        
        if log:
            df[num_type] = df[num_type].clip(lower=1)
            if TORCH_AVAILABLE:
                df.loc[:,num_type] = torch.log(torch.tensor(df[num_type].values, dtype=torch.float32)).numpy()
            else:
                df.loc[:,num_type] = np.log(df[num_type].values)
        if log2:
            df[num_type] = df[num_type].clip(lower=1)
            if TORCH_AVAILABLE:
                df.loc[:,num_type] = torch.log2(torch.tensor(df[num_type].values, dtype=torch.float32)).numpy()
            else:
                df.loc[:,num_type] = np.log2(df[num_type].values)
        if log10:
            df[num_type] = df[num_type].clip(lower=1)
            if TORCH_AVAILABLE:
                df.loc[:,num_type] = torch.log10(torch.tensor(df[num_type].values, dtype=torch.float32)).numpy()
            else:
                df.loc[:,num_type] = np.log10(df[num_type].values)
        
        DataDeal.min_max_scaler(df, num_type=num_type, model_path=model_path, reuse=reuse)


    @staticmethod
    def min_max_scaler_dt(X, date_type=[], scaler_file=None, max_date=None, adjust=True):
        """
        对pandas数据表中的日期列进行归一化处理;每段日期都是从0到1的区间内，将一段时间纳入[0,1]
        
        参数:
        - X: pandas DataFrame, 需要处理的数据表
        - date_type: list, 需要归一化的日期列名列表
        - scaler_file: str, 用于保存或加载归一化参数的json文件路径
        - max_date: str, 指定归一化使用的最大日期（如'2099-01-01'）;因为预测时的日期是未来的，在训练时是没有，因此支持指定
        - adjust:将过于小的数，调整大一点，只有使用了max_date才会生效，这是缓冲max_date设置过大带来的归一化后数值过小的影响
        
        返回:
        - 处理后的DataFrame

        examples
        -----------------------------------------
        # 不使用max_date（使用数据实际最大值）
        df_normalized = dt_min_max_scaler(df, date_type=['date_column'])
        
        # 使用max_date指定最大日期
        df_normalized = dt_min_max_scaler(df, date_type=['date_column'], max_date='2099-01-01')
        
        # 同时使用scaler_file和max_date
        df_normalized = dt_min_max_scaler(df, 
                                        date_type=['date_column'], 
                                        scaler_file='scaler_params.json',
                                        max_date='2099-01-01')
                                    
        """
        
        # 如果date_type为空，直接返回原数据
        if not date_type:
            return X
        
        # 如果提供了scaler_file且文件存在，则加载归一化参数
        if scaler_file and Path(scaler_file).exists():
            # with open(scaler_file, 'r') as f:
                # scaler_params = json.load(f)
            scaler_params = read(scaler_file)
        else:
            scaler_params = {}
 
        # 复制数据避免修改原DataFrame
        df = X.copy()
        
        # 将max_date转换为时间戳数值（如果提供了）
        max_date_value = pd.to_datetime(max_date).value if max_date else None
        
        for col in date_type:
            # 确保列存在
            if col not in df.columns:
                continue
                
            # 转换为datetime类型
            df[col] = pd.to_datetime(df[col])
            
            # 转换为时间戳数值
            df[col] = df[col].apply(lambda x: x.value)
            
            # 如果scaler_file存在且包含当前列的参数，则使用保存的参数
            adjust_val = 1
            if scaler_params and (col in scaler_params):
                min_val = scaler_params[col]['min']
                max_val = scaler_params[col]['max']
            else:
                min_val = df[col].min()
                # 如果提供了max_date则使用它，否则使用数据的最大值
                max_val = max_date_value if max_date_value else df[col].max()
                scaler_params[col] = {'min': min_val, 'max': max_val}
            
            # 执行归一化
            range_val = max_val - min_val
            if range_val > 0:  # 避免除以0
                df[col] = (df[col] - min_val) / range_val
            else:
                df[col] = 0.0  # 如果所有值相同，归一化为0

            if max_date and adjust:
                if "adjust_val" in scaler_params[col].keys():
                    adjust_val = scaler_params[col]["adjust_val"]
                    df[col] = df[col]*adjust_val
                else:
                    df_col_max = df[col].max()
                    df_col_max = np.abs(df_col_max)
                    if df_col_max<0.00001:
                        adjust_val = 100000
                        df[col] = df[col]*adjust_val
                    elif df_col_max<0.0001:
                        adjust_val = 10000
                        df[col] = df[col]*adjust_val
                    elif df_col_max<0.001:
                        adjust_val = 1000
                        df[col] = df[col]*adjust_val
                    elif df_col_max<0.01:
                        adjust_val = 100
                        df[col] = df[col]*adjust_val
                    scaler_params[col]["adjust_val"] = float(adjust_val)
                
        # 如果指定了scaler_file，则保存归一化参数
        if scaler_file:
            write(scaler_params,file_path=scaler_file)
        return df
    
    @staticmethod
    def min_max_scale_sample(df, col, min_val, max_val):
        """Min-max scale a column"""
        return (df[col] - min_val) / (max_val - min_val)
    
    @staticmethod
    def min_max_update(df, num_type=[],num_small=[], 
                       is_pre=False, num_scaler_file=None,
                       log=False,log2=False,log10=False):
        """
        MinMaxScalerCustom类每次partial_fit时更新min-max值，因此每次fit时都保存min-max值
        - 每个列都需单独处理，一个单独的MinMaxScalerCustom实例
        
        Parameters:
        - df: DataFrame to process
        - dict_file: Not used in this implementation (kept for compatibility)
        - is_pre: Whether in preprocessing mode
        - num_scaler_file: File to store/load min-max scaler values (using joblib)
        - log: Whether to apply log transformation
        - log2: Whether to apply log2 transformation
        - log10: Whether to apply log10 transformation
        - num_small: List of column names to exclude from log transformations
        
        Returns:
        - Processed DataFrame
        """
        
        if num_scaler_file is None:
            raise ValueError("num_scaler_file must be specified")
        
        # 收集所有需要log变换的列，一次性处理避免DataFrame碎片化
        log_transformations = []
        
        if log:
            log_cols = [col for col in num_type if col not in num_small]
            if log_cols:
                df[log_cols] = df[log_cols].clip(lower=1)
                if TORCH_AVAILABLE:
                    log_transformations.append((log_cols, torch.log))
                else:
                    log_transformations.append((log_cols, np.log))

        if log2:
            log_cols = [col for col in num_type if col not in num_small]
            if log_cols:
                df[log_cols] = df[log_cols].clip(lower=1)
                if TORCH_AVAILABLE:
                    log_transformations.append((log_cols, torch.log2))
                else:
                    log_transformations.append((log_cols, np.log2))

        if log10:
            log_cols = [col for col in num_type if col not in num_small]
            if log_cols:
                df[log_cols] = df[log_cols].clip(lower=1)
                if TORCH_AVAILABLE:
                    log_transformations.append((log_cols, torch.log10))
                else:
                    log_transformations.append((log_cols, np.log10))
        
        # 一次性处理所有log变换，避免多次drop/add操作导致的碎片化
        if log_transformations:
            # 创建新的列数据字典
            new_columns = {}
            for log_cols, log_func in log_transformations:
                if TORCH_AVAILABLE:
                    df_tmp = log_func(torch.tensor(df[log_cols].values, dtype=torch.float32)).numpy()
                else:
                    df_tmp = log_func(df[log_cols].values)
                for i, col in enumerate(log_cols):
                    if df_tmp.ndim == 1:
                        new_columns[col] = df_tmp
                    else:
                        new_columns[col] = df_tmp[:, i]
            
            # 一次性移除旧列并添加新列
            cols_to_remove = [col for log_cols, _ in log_transformations for col in log_cols]
            df = df.drop(columns=cols_to_remove)
            
            # 使用concat一次性添加所有新列，避免碎片化
            if new_columns:
                new_df = pd.DataFrame(new_columns, index=df.index)
                df = pd.concat([df, new_df], axis=1)
            
        
        # Initialize scaler dictionary (column_name -> MinMaxScalerCustom)
        scaler_dict = {}
        
        # If not preprocessing mode, we need to update scaler values
        if not is_pre:
            # Load existing scaler values if file exists
            if os.path.exists(num_scaler_file):
                scaler_dict = joblib.load(num_scaler_file)
            
            # Update scaler values with new data
            if len(num_type) == 0:
                num_type = df.select_dtypes(include=['number']).columns
            for col in num_type:
                col_data = df[col].values
                
                if col in scaler_dict:
                    # Update min/max if current is lower/higher
                    scaler_dict[col].partial_fit(col_data)
                else:
                    # Initialize new column scaler
                    scaler = MinMaxScalerCustom()
                    scaler.fit(col_data)
                    scaler_dict[col] = scaler
            
            # Save updated scaler values
            joblib.dump(scaler_dict, num_scaler_file)
        
        else:
            # In preprocessing mode, just load the scaler values
            if not os.path.exists(num_scaler_file):
                raise FileNotFoundError(f"Scaler file {num_scaler_file} not found for preprocessing")
            
            scaler_dict = joblib.load(num_scaler_file)
        # print(scaler_dict)
        # Apply min-max scaling
        processed_df = df.copy()
        for col, scaler in scaler_dict.items():
            if col in processed_df.columns:
                if scaler.max_ != scaler.min_:  # Avoid division by zero
                    processed_df[col] = scaler.transform(processed_df[col].values)
                else:
                    processed_df[col] = 0.0  # Default value for constant columns
        
        return processed_df

    
    @staticmethod
    def num_deal(data, num_type):
        column_all = data.columns
        ### 数字
        num_type = [col for col in num_type if col in column_all] 
        data[num_type] = data[num_type].astype(np.float32)
    
    @staticmethod
    def num_describe(df,pc:ParamConfig=None):
        # 只检查数值列
        numeric_cols = df.select_dtypes(include='number').columns
        
        # 删除值全为0的数值列
        tmp_num_df = df[numeric_cols]
        df_with_nan = tmp_num_df.copy()

        # 删除全为0或NaN的列
        df_cleaned_nan = df_with_nan.loc[:, df_with_nan.notna().any() & (df_with_nan != 0).any()]
        
        if pc:
            pc.lg(f"df_cleaned_nan.shape={df_cleaned_nan.shape}")
            pc.lg(f"num describe:\n{df_cleaned_nan[:3]}")
            pc.lg(f"num fenbu:\n{df_cleaned_nan.describe()}")
            
        return df_cleaned_nan
            
    @staticmethod
    def null_deal_pandas(data,cname_num_type=[], cname_str_type=[], num_padding=0, str_padding = '<PAD>'):
        """
        params
        ----------------------------------
        - data:pandas数表
        - cname_num_type：数字类型列表
        - cname_str_type：字符类型列表
        - num_padding:数字类型空值填充
        - str_padding:字符类型空值填充
        
        example
        -----------------------------------
        #空值处理
        data = null_deal_pandas(data,cname_num_type=num_type,cname_str_type=str_classification,num_padding=0,str_padding = '<PAD>')

        """
        if len(cname_num_type)>0:
            # 数字置为0
            for col in cname_num_type:
                data.loc[data[col].isna(),col]=num_padding
        
        if len(cname_str_type)>0:
            #object转str，仅处理分类特征，身份认证类特征不参与训练
            data[cname_str_type] = data[cname_str_type].astype(str)
            data[cname_str_type] = data[cname_str_type].astype("string")
            
            for col in cname_str_type:
                data.loc[data[col].isna(),col]=str_padding

            # nan被转为了字符串，但在pandas中仍然是个特殊存在，转为特定字符串，以防Pandas自动处理
            # 创建一个替换映射字典  
            type_mapping = {  
                'nan': str_padding,   
                '': str_padding
            }  
                
            # 使用.replace()方法替换'列的类型'列中的值  
            data[cname_str_type] = data[cname_str_type].replace(type_mapping)  
                
            nu = data[cname_str_type].isnull().sum()
            for col_name,v in nu.items():
                if v > 0 :
                    print("存在空值的列:\n")
                    print(col_name,v)
            return data


    
    
    @staticmethod
    def rolling_windows(data_path=None, df=None,col_time='DT_TIME',
                    interval=7, win_len=10):
        """
        生成器：每次 yield (window_start, window_end, sub_df)
        从最早日期开始，每隔 interval 天取一个 win_len 天的窗口
        """
        if df is None:
            df = pd.read_csv(data_path, parse_dates=[col_time])
        DataDeal.date_deal(df,date_type=[col_time])
        date_col = df[col_time].dt.date

        min_date = date_col.min()
        max_date = date_col.max()

        # 当前窗口起点
        cur_start = min_date
        while cur_start + timedelta(days=win_len-1) <= max_date:
            cur_end = cur_start + timedelta(days=win_len-1)
            mask = date_col.between(cur_start, cur_end)
            yield cur_start, cur_end, df[mask]
            cur_start += timedelta(days=interval)
    
    @staticmethod
    def std7(df, cname_num, means=None, stds=None, set_7mean=True):
        if set_7mean: #将超过7倍均值的数据置为7倍均值
            # 遍历DataFrame的每一列,
            for col in cname_num:  
                # 获取当前列的均值  
                mean_val = means[col]  
                # 创建一个布尔索引，用于标记哪些值超过了均值的7倍  
                mask = df[col] > (7 * mean_val)  
                # 将这些值重置为均值的7倍  
                df.loc[mask, col] = 7 * mean_val  

        df[cname_num] = (df[cname_num] - means)/stds  #标准化
        
        return df  

    
    @staticmethod
    def str_deal(data, pc, classify_type=[]):
        """标识列及类别列处理
        - classify_type:指定值则类别列为指定的值，否则使用排除法，排除数字，布尔，标识列，剩下的列为类别列
        
        """
        column_all = data.columns
        identity = pc.col_type.identity
        ### 字符-身份标识类
        str_identity = [col for col in column_all if col in identity]
        print("str_identity:",str_identity)
        DataDeal.str_pd(data,str_identity)

        ### 字符-分类，用于分类的列，比如渠道，交易类型,商户，地区等
        if len(classify_type)==0:
            str_classification = [col for col in data.columns if col not in str_identity and col not in pc.col_type.num_type and col not in pc.col_type.date_type and col not in pc.col_type.bool_type]
        else:
            str_classification = classify_type
        pc.col_type.classify_type = str_classification
        DataDeal.str_pd(data,str_classification)
    
    @staticmethod
    def str_pd(data,cname_date_type):
        """pandas数表列转字符类型"""
        data[cname_date_type] = data[cname_date_type].astype(str)
        data[cname_date_type] = data[cname_date_type].astype("string")
        return data
    
    @staticmethod
    def time_between(df, start_date, end_date, time_col='key_2', date_format=None,
                    inclusive='both', copy=True, timezone=None,
                    return_mask=False, validate_dates=True):
        """
        筛选指定时间范围内的数据（优化版本）

        Args:
            df: pandas DataFrame
            start_date: 开始日期，支持多种格式 (str, datetime, Timestamp)
            end_date: 结束日期，支持多种格式 (str, datetime, Timestamp)
            time_col: 时间列名
            date_format: 日期格式字符串，如 '%Y-%m-%d %H:%M:%S'
            inclusive: 包含边界 ['both', 'neither', 'left', 'right']
            copy: 是否复制数据框，避免修改原数据
            timezone: 时区设置，如 'Asia/Shanghai'
            return_mask: 是否返回布尔掩码而不是过滤后的数据
            validate_dates: 是否验证日期格式和范围

        Returns:
            pandas DataFrame 或 numpy array: 过滤后的数据框或布尔掩码

        Raises:
            ValueError: 当日期格式无效、列不存在或日期范围错误时
            TypeError: 当输入参数类型错误时
        """
        import pandas as pd
        import numpy as np
        from datetime import datetime
        import warnings

        # 输入验证
        if time_col not in df.columns:
            raise ValueError(f"时间列 '{time_col}' 不存在")
        if inclusive not in ['both', 'neither', 'left', 'right']:
            raise ValueError("inclusive 必须是 'both', 'neither', 'left', 或 'right'")

        if validate_dates:
            if pd.isna(start_date) or pd.isna(end_date):
                raise ValueError("开始和结束日期不能为空")
            if start_date > end_date:
                raise ValueError("开始日期不能晚于结束日期")

        # 复制数据框（避免修改原数据）
        if copy:
            df = df.copy()

        try:
            # 优化的日期转换
            if date_format:
                # 指定格式转换，更快更准确
                time_series = pd.to_datetime(df[time_col], format=date_format, errors='coerce')
                start_ts = pd.to_datetime(start_date, format=date_format)
                end_ts = pd.to_datetime(end_date, format=date_format)
            else:
                # 自动推断格式
                time_series = pd.to_datetime(df[time_col], errors='coerce')
                start_ts = pd.to_datetime(start_date)
                end_ts = pd.to_datetime(end_date)

            # 时区处理
            if timezone:
                if time_series.dt.tz is None:
                    time_series = time_series.dt.tz_localize(timezone)
                else:
                    time_series = time_series.dt.tz_convert(timezone)

                if start_ts.tz is None:
                    start_ts = start_ts.tz_localize(timezone)
                if end_ts.tz is None:
                    end_ts = end_ts.tz_localize(timezone)

            # 处理转换失败的日期
            invalid_dates = time_series.isna()
            if invalid_dates.any():
                if validate_dates:
                    warnings.warn(f"发现 {invalid_dates.sum()} 个无效日期，将被排除")

                # 对于无效日期，在掩码中设为False
                time_series = time_series.fillna(pd.NaT)

            # 创建过滤掩码（性能优化：避免创建中间列）
            if inclusive == 'both':
                mask = (time_series >= start_ts) & (time_series <= end_ts)
            elif inclusive == 'left':
                mask = (time_series >= start_ts) & (time_series < end_ts)
            elif inclusive == 'right':
                mask = (time_series > start_ts) & (time_series <= end_ts)
            else:  # neither
                mask = (time_series > start_ts) & (time_series < end_ts)

            # 确保无效日期不被包含
            mask = mask & ~invalid_dates

            if return_mask:
                return mask.values
            else:
                # 直接使用掩码过滤，避免创建中间列
                return df.loc[mask]

        except Exception as e:
            raise ValueError(f"日期转换失败: {str(e)}") from e

    @staticmethod
    def time_between_multiple(df, date_ranges, time_col='key_2', **kwargs):
        """
        支持多个时间范围的过滤（扩展功能）

        Args:
            df: pandas DataFrame
            date_ranges: 时间范围列表，格式为 [(start1, end1), (start2, end2), ...]
            time_col: 时间列名
            **kwargs: 传递给 time_between 的其他参数

        Returns:
            pandas DataFrame: 过滤后的数据框
        """
        if not date_ranges:
            return df.copy()

        combined_mask = None
        for start_date, end_date in date_ranges:
            mask = DataDeal.time_between(
                df, start_date, end_date, time_col,
                return_mask=True, **kwargs
            )

            if combined_mask is None:
                combined_mask = mask
            else:
                combined_mask = combined_mask | mask

        return df.loc[combined_mask].copy()

    @classmethod
    def get_col_names(cls, df, col_type='object'):
        """
        根据指定的数据类型获取DataFrame中的列名

        Args:
            df: pandas DataFrame
            col_type: 数据类型过滤条件，可选值：
                - 'object': object类型列
                - 'cat': 分类类型列（包括str, string, category）
                - 'num': 数值类型列（包括所有数字类型）
                - 'date': 日期类型列（包括datetime64[ns], datetime64）
                - 'datetime64[ns]': 精确的datetime64[ns]类型
                - 'datetime64': datetime64类型
                - 'int': 整数类型列
                - 'float': 浮点数类型列
                - 'bool': 布尔类型列
                - 'str': 字符串类型列
                - 'category': 分类类型列
                - 'all': 返回所有列名（默认行为）

        Returns:
            list: 符合指定类型的列名列表
        """
        import pandas as pd
        import numpy as np

        # 如果请求所有列，直接返回
        if col_type == 'all':
            return list(df.columns)

        # 定义类型映射关系
        type_mapping = {
            # 数值类型
            'num': ['int8', 'int16', 'int32', 'int64', 'uint8', 'uint16', 'uint32', 'uint64',
                   'float16', 'float32', 'float64', 'number'],
            'int': ['int8', 'int16', 'int32', 'int64', 'uint8', 'uint16', 'uint32', 'uint64', 'integer'],
            'float': ['float16', 'float32', 'float64', 'floating'],

            # 字符串和分类类型
            'cat': ['object', 'string', 'category', 'str'],
            'str': ['object', 'string'],
            'category': ['category'],

            # 日期时间类型
            'date': ['datetime64[ns]', 'datetime64', 'datetime'],
            'datetime64[ns]': ['datetime64[ns]'],
            'datetime64': ['datetime64', 'datetime64[ns]'],

            # 布尔类型
            'bool': ['bool', 'boolean'],

            # 对象类型（保持向后兼容）
            'object': ['object'],
        }

        # 获取请求的类型列表
        target_types = type_mapping.get(col_type, [col_type])

        # 收集符合条件的列名
        result_columns = []

        for col in df.columns:
            col_dtype = str(df[col].dtype).lower()

            # 检查列的数据类型是否匹配目标类型
            for target_type in target_types:
                if target_type.lower() in col_dtype:
                    result_columns.append(col)
                    break

        return result_columns

    @classmethod
    def get_col_names_by_pattern(cls, df, pattern='.*'):
        """
        根据正则表达式模式获取列名

        Args:
            df: pandas DataFrame
            pattern: 正则表达式模式，默认匹配所有列

        Returns:
            list: 匹配模式的列名列表
        """
        import re
        return [col for col in df.columns if re.match(pattern, col)]

    @classmethod
    def get_col_types_summary(cls, df):
        """
        获取DataFrame中各列的数据类型汇总

        Args:
            df: pandas DataFrame

        Returns:
            dict: 数据类型到列名列表的映射
        """
        type_summary = {}
        for col in df.columns:
            dtype = str(df[col].dtype)
            if dtype not in type_summary:
                type_summary[dtype] = []
            type_summary[dtype].append(col)
        return type_summary

class FileDb():
    def __init__(self,path):
        self.path = path

    def read(self):
        return read(self.path)
    
    def write(self,data):
        return write(data,self.path)
    
    def list_append(self,data, del_dup=False):
        ll = self.read()
        if ll is None or len(str(ll)) == 0 or len(ll) == 0:
            ll = []
        ll.append(data)
        if del_dup:
            ll = list(set(ll))
        write(ll,self.path)
        
    
        


# -*- coding:utf-8 -*-
"""
深度学习通用数据预处理
- 把 bank+id 合并成唯一 id
- 数值列归一化 / 标准差
- 类别列 LabelEncoder
- 时间列转距基线天数
- 支持保存/加载 transformer，保证离线/在线一致
"""
import os
import pandas as pd
from sklearn.preprocessing import StandardScaler, LabelEncoder
from typing import List, Optional, Dict, Any
import joblib
import datetime


"""
改进版深度学习数据预处理类
- 支持字段类型转换
- identity 合并（bank + id）
- 类别列：LabelEncoder（支持多列共享编码器）
- 数值列：MinMaxScaler（支持 log10 + 增量更新）
- 日期列：转为距 max_date 的天数后归一化
- 保存/加载所有 transformer，保证离线/在线一致
"""


import os
import pandas as pd
import joblib
from sklearn.preprocessing import MinMaxScaler
from typing import List, Dict, Any, Optional
import numpy as np
import datetime


class DataDealDL:
    def __init__(
        self,
        identity_cols: List[str] = None,
        classify_cols: List[str] = None,
        classify_shared_groups: List[List[str]] = None,
        num_cols: List[str] = None,
        num_small: List[str] = None,
        date_cols: List[str] = None,
        bool_cols: List[str] = None,
        log10_transform: bool = False,
        pc:ParamConfig = None
    ):
        """
        初始化深度学习数据处理器，用于数据预处理和特征工程。
        
        Args:
            identity_cols: 身份标识列名列表，如 ['Bank', 'Account'] 会合并为唯一ID
            classify_cols: 需要独立编码的类别列名列表
            classify_shared_groups: 共享编码器的列组，如 [['From', 'To']] 表示多列共用一个编码器
            num_cols: 需要归一化的数值列名列表
            num_small: 数值列中不进行log10变换的小数值列名列表
            date_cols: 需要转换和归一化的日期列名列表（将转换为天数后归一化）
            bool_cols: 布尔列名列表（转换为0/1）
            cls_dict_file: 类别字典文件路径，用于保存和加载编码器
            log10_transform: 是否对数值列进行log10变换，默认False
            file_num: 文件编号，用于区分同一模型对应的多个文件，默认1
            pc: 参数配置对象，包含模型保存路径、算法类型、模型编号等信息
        """
        self.identity_cols = identity_cols or []
        self.classify_cols = classify_cols or []
        self.classify_shared_groups = classify_shared_groups or []
        self.num_cols = num_cols or []
        self.num_small = num_small or []
        self.date_cols = date_cols or []
        self.bool_cols = bool_cols or []
        
        self.file_num    = pc.file_num
        self.scaler_root = pc.model_save_dir
        self.alg_type    = pc.alg_type
        self.batch_num   = pc.model_num
        
        self.is_merge_identity = pc.is_merge_identity
        self.num_scaler_file   = pc.num_scaler_file()
        self.date_scaler_file  = pc.date_scaler_file()
        self.cls_dict_file     = pc.dict_file()  # 类别字典文件
        
        self.log10_transform   = log10_transform
        self.max_date = pd.to_datetime(pc.max_date).date()
        self._split="_._"

        # 创建保存目录
        os.makedirs(self.scaler_root, exist_ok=True)

        # 存储 encoder 和 scaler
        self._le_dict: Dict[str, Any] = {}  # 单独列的 encoder
        self._shared_le: Dict[str, Any] = {}  # 共享组的 encoder，key 可为 "From_To"
        self._num_scaler = MinMaxScaler()
        self._date_scaler = MinMaxScaler()


    @staticmethod
    def data_deal(df,pc:ParamConfig):
        """
        深度学习数据预处理的统一入口方法

        主要计算逻辑：
        1. 模型加载/初始化策略
           - 首先检查是否存在已保存的预处理模型文件
           - 如果存在：直接加载pickle序列化的DataDealDL对象
           - 如果不存在：创建新的DataDealDL实例，包含所有预处理组件

        2. DataDealDL初始化参数（需要12个核心参数）
           - identity_cols: 身份标识列（如['Bank', 'Account']）会合并为唯一ID
           - classify_cols: 独立编码的类别列列表
           - classify_shared_groups: 共享编码器的列组（如[['From', 'To']]）
           - num_cols: 需要归一化的数值列列表
           - num_small: 不进行log10变换的小数值列列表
           - date_cols: 日期列列表（转换为天数后归一化）
           - bool_cols: 布尔列列表（转换为0/1）
           - log10_transform: 是否对数值列进行log10变换
           - alg_type: 算法类型（用于文件命名）
           - model_save_dir: 模型保存目录
           - model_num: 模型编号
           - file_num: 文件编号

        3. 训练/推理分支处理
           - 训练模式 (pc.is_train=True):
             * 调用fit_transform()：拟合并转换数据
             * 更新数值列的极值范围
             * 保存完整的预处理模型到文件
           - 推理模式 (pc.is_train=False):
             * 调用transform()：仅使用已有模型转换数据
             * 保持预处理参数不变，确保一致性

        4. 预处理流程（在DataDealDL内部）
           - 步骤1: 类型转换和统一
           - 步骤2: 身份标识列合并
           - 步骤3: 布尔列处理（0/1转换）
           - 步骤4: 类别列编码（LabelEncoder）
           - 步骤5: 日期列归一化
           - 步骤6: 数值列归一化（log10 + MinMax）

        Args:
            df: 输入的pandas DataFrame
            pc: ParamConfig参数配置对象，包含所有预处理参数

        Returns:
            DataFrame: 预处理后的数据表，可直接用于深度学习模型训练

        Example:
            # 配置参数
            pc.col_type.identity = ['Bank', 'Account']
            pc.col_type.num_type = ['amount', 'risk_score']
            pc.col_type.classify_type = ['currency', 'payment_type']
            pc.is_train = True

            # 执行预处理
            df_processed = DataDealDL.data_deal(df, pc)

        Note:
            - 该方法支持增量学习，训练时会更新数值极值
            - 所有预处理组件都会保存，确保离线/在线一致性
            - 支持多列共享编码器，适合图神经网络等场景
        """
        # 数据预处理
        # 这里不能直接保存DataDealDL，因为训练时初始化的是训练的参数，预测时需要重新初始化参数
        # if os.path.exists(pc.data_deal_model_path()):
        #     print("模型已存在，加载模型-------1----------")
        #     data_deal = pkl_load(file_path=pc.data_deal_model_path())
        # else :
        #     print("模型不存在，初始化模型-------2----------")
        data_deal = DataDealDL(  # 初始化
            identity_cols=pc.col_type.identity,
            classify_cols=pc.col_type.classify_type,
            classify_shared_groups=pc.col_type.classify_type_pre,
            num_cols=pc.col_type.num_type,
            num_small=pc.col_type.num_small,
            date_cols=pc.col_type.date_type,
            bool_cols=pc.col_type.bool_type,
            log10_transform=True,
            pc=pc
        )

        # 训练阶段
        if pc.is_train:  #数字极值更新训练
            df_processed = data_deal.fit_transform(df)
            # pkl_save(data_deal,file_path=pc.data_deal_model_path())
        else:
            df_processed = data_deal.transform(df)

        return df_processed


    # ---------- public ----------
    def fit_transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """训练阶段：拟合并转换数据"""
        df = df.copy()
        
        df = self._type_conversion(df)
        print(f"self.identity_cols={self.identity_cols}-----------------")
 
        # 1. 合并 identity
        df = self._merge_identity(df)
        # print(1,df[:3])
        

        # 2. 布尔列处理
        df = self._process_bool(df, fit=True)
        # print(2,df[:3])

        # 3. 类别编码（单独 + 共享）
        # df = self._encode_category(df, fit=True)
        df = self._col2index(df, fit=True)
   


        # 4. 日期处理（转天数 + 归一化）
        df = self._scale_date(df, fit=True)

        # 5. 数值归一化（log10 + MinMax）

        df = self._min_max_update(df, fit=True)
 

        return df

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """推理阶段：仅转换，使用已保存的 encoder/scaler"""
        df = df.copy()
        df = self._type_conversion(df)
        # print(df.info())
        
        # 1. 合并 identity
        df = self._merge_identity(df)
        # print(1,df[:3])
        
        # 2. 布尔列
        df = self._process_bool(df, fit=False)
        # print(2,df[:3])

        # 3. 类别编码
        # df = self._encode_category(df, fit=False)
        df = self._col2index(df, fit=False)


        # 4. 日期
        df = self._scale_date(df, fit=False)
  

        # 5. 数值
        # df = self._scale_numeric(df, fit=False)
        df = self._min_max_update(df, fit=False)

        return df
    
        
    
    # ---------- private ----------
    def _type_conversion(self, df: pd.DataFrame) -> pd.DataFrame:
        """统一字段类型"""
        for col in self.num_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        for col in self.date_cols:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')
        for col in self.classify_cols + self.identity_cols:
            if col in df.columns:
                df[col] = df[col].astype(str)
        for group in self.classify_shared_groups:
            for col in group:
                if col in df.columns:
                    df[col] = df[col].astype(str)
        return df

    def _merge_identity(self, df: pd.DataFrame) -> pd.DataFrame:
        """合并 identity 列为一个字段（如 Bank_Account）"""
        if self.is_merge_identity:
            if len(self.identity_cols) <= 1:
                return df
            new_id = df[self.identity_cols[0]].astype(str)
            for c in self.identity_cols[1:]:
                new_id += self._split + df[c].astype(str)
            df[self.identity_cols[0]] = new_id
            
            return df.drop(columns=self.identity_cols[1:])
        else:
            return df

    def _process_bool(self, df: pd.DataFrame, fit: bool = True) -> pd.DataFrame:
        """布尔列转 0/1"""
        for col in self.bool_cols:
            if col in df.columns:
                df[col] = (df[col].astype(bool)).astype(int)
        return df

    def _col2index(self, df: pd.DataFrame, fit: bool = True) -> pd.DataFrame:
        #类型字段索引编码,如果是训练则保存字典
        is_pre = not fit 
        if len(self.classify_cols) == 0 and len(self.classify_shared_groups) == 0:
            return df
        DataDeal.col2index(df,classify_type=self.classify_cols ,
                    classify_type2=self.classify_shared_groups,
                    dict_file=self.cls_dict_file,
                    is_pre=is_pre,
                    word2id=None) 
        return df
    def _encode_category(self, df: pd.DataFrame, fit: bool = True) -> pd.DataFrame:
        """类别编码，支持共享 encoder"""
        # 单独编码列
        for col in self.classify_cols:
            if col not in df.columns:
                continue
            if fit:
                le = joblib.load(self.scaler_root + f"/le_{col}.pkl") if os.path.exists(
                    self.scaler_root + f"/le_{col}.pkl") else None
                if le is None:
                    le = LabelEncoder()
                    # 处理空值
                    df[col] = df[col].fillna("<UNK>")
                    le.fit(df[col])
                    joblib.dump(le, os.path.join(self.scaler_root, f"le_{col}.pkl"))
                self._le_dict[col] = le
            else:
                le = joblib.load(os.path.join(self.scaler_root, f"le_{col}.pkl"))
                self._le_dict[col] = le

            # 转换
            unknown = -1
            df[col] = df[col].fillna("<UNK>").map(
                lambda x: le.transform([x])[0] if x in le.classes_ else unknown
            ).astype(int)

        # 共享编码组
        for group in self.classify_shared_groups:
            name_key = "_".join(group)
            shared_le = None
            if fit:
                if os.path.exists(os.path.join(self.scaler_root, f"le_shared_{name_key}.pkl")):
                    shared_le = joblib.load(os.path.join(self.scaler_root, f"le_shared_{name_key}.pkl"))
                else:
                    shared_le = LabelEncoder()
                    all_vals = pd.concat([df[col].dropna() for col in group if col in df.columns], ignore_index=True)
                    all_vals = pd.Series(all_vals).fillna("<UNK>").astype(str)
                    shared_le.fit(all_vals)
                    joblib.dump(shared_le, os.path.join(self.scaler_root, f"le_shared_{name_key}.pkl"))
                self._shared_le[name_key] = shared_le
            else:
                shared_le = joblib.load(os.path.join(self.scaler_root, f"le_shared_{name_key}.pkl"))
                self._shared_le[name_key] = shared_le

            for col in group:
                if col not in df.columns:
                    continue
                unknown = -1
                df[col] = df[col].fillna("<UNK>").map(
                    lambda x: shared_le.transform([x])[0] if x in shared_le.classes_ else unknown
                ).astype(int)

        return df

    def _scale_date(self, df: pd.DataFrame, fit: bool = True) -> pd.DataFrame:
        """日期处理，使用DataDeal.date_deal方法"""
   
        if not self.date_cols or len(self.date_cols) == 0:
            return df
        
        # 使用DataDeal.min_max_scaler_dt方法处理日期
        df = DataDeal.min_max_scaler_dt(df, 
                                 date_type=self.date_cols,
                                 scaler_file=self.date_scaler_file,
                                 max_date=self.max_date)
        
        
        return df
    
    def _min_max_update(self, df: pd.DataFrame, fit: bool = True) -> pd.DataFrame:
        
        is_pre = not fit
        df = DataDeal.min_max_update(df, 
                                num_type=self.num_cols,
                                num_small=self.num_small,
                                num_scaler_file=self.num_scaler_file, 
                                is_pre=is_pre,
                                log10=self.log10_transform)
        return df
         

    def _scale_numeric(self, df: pd.DataFrame, fit: bool = True) -> pd.DataFrame:
        """数值列：log10 + MinMaxScaler，支持增量更新"""
        if not self.num_cols:
            return df

        # log10 变换
        for col in self.num_cols:
            if col in df.columns:
                # 避免 log(0)
                df[col] = np.log10(df[col] + 1) if self.log10_transform else df[col]

        if fit:
            # 增量更新：如果已有 scaler，加载并更新极值
            scaler_path = os.path.join(self.scaler_root, "scaler_num.pkl")
            if os.path.exists(scaler_path):
                old_scaler = joblib.load(scaler_path)
                old_min = old_scaler.data_min_
                old_max = old_scaler.data_max_
                new_min = df[self.num_cols].min()
                new_max = df[self.num_cols].max()
                # 更新为全局 min/max
                updated_min = np.minimum(old_min, new_min)
                updated_max = np.maximum(old_max, new_max)
                self._num_scaler.data_min_, self._num_scaler.data_max_ = updated_min, updated_max
            else:
                self._num_scaler.fit(df[self.num_cols])
            joblib.dump(self._num_scaler, scaler_path)
        else:
            self._num_scaler = joblib.load(os.path.join(self.scaler_root, "scaler_num.pkl"))

        df[self.num_cols] = self._num_scaler.transform(df[self.num_cols])
        return df
    

#--------------------------------------------------------------
# 数据处理类 - 封装公共功能
#--------------------------------------------------------------

class DataProcessor:
    """
    数据处理类 - 封装数据训练和交易处理的相关方法

    提供统一的数据处理接口，支持通用数据处理和交易特定数据处理
    """

    def __init__(self):
        """初始化数据处理类"""
        pass

    def _get_usecols_from_model_title(self, model_title,sep='~'):
        """
        根据模型标题获取要使用的列

        Args:
            model_title (str): 模型标题，'all'表示使用所有列，否则按'~'分割

        Returns:
            list or None: 要使用的列列表，None表示使用所有列
        """
        if model_title == 'all':
            return None
        else:
            return model_title.split(sep)

    def _create_categorical_function_general(self):
        """
        创建通用的分类列判断函数

        Returns:
            function: 分类列判断函数
        """
        def is_categorical(col: str) -> bool:
            return col.lower().startswith(('is_', 'has_', 'with_'))
        return is_categorical

    def _create_categorical_function_tra(self):
        """
        创建特定于交易的分类列判断函数

        Returns:
            function: 分类列判断函数
        """
        def is_categorical(col: str) -> bool:
            cls_cols = ['Receiving Currency','Payment Currency', 'Payment Format']
            cls_cols2 = [col.lower() for col in cls_cols]
            return col.lower() in cls_cols2
        return is_categorical

    def _load_and_classify_data(self, 
                data_path, label_name, str_identity, is_train, 
                usecols, drop_columns, 
                is_categorical_func, sep='~',date_type=[],bool_type = []):
        """
        加载数据并进行分类的通用方法

        Args:
            data_path (str): 数据文件路径
            label_name (str): 标签列名
            str_identity (str): 标识列
            is_train (bool): 是否为训练数据
            usecols (list): 要使用的列
            drop_columns (list): 要删除的列
            is_categorical_func (function): 分类列判断函数
            sep (str): 分隔符，默认为'~'

        Returns:
            tuple: (DataFrame, label列, 列类型字典)
        """
        df, y, col_types = DataDeal.getXy(data_path, label_name,
                                    identity_cols=str_identity, sep=sep,
                                    is_train=is_train, usecols=usecols,
                                    drop_columns=drop_columns,
                                    dtype_mapping=None,
                                    is_categorical_func=is_categorical_func,
                                    date_type=date_type,
                                    bool_type=bool_type)
        return df, y, col_types

    def _analyze_numeric_columns(self, df, pc, threshold=100):
        """
        分析数值列，找出最大值小于阈值的列

        Args:
            df (DataFrame): 数据框
            pc (ParamConfig): 参数配置对象
            threshold (int): 阈值，默认为100

        Returns:
            list: 小于阈值的列名列表
        """
        num_small = DataDeal.columns_by_max_value(df, condition='less', threshold=threshold)
        pc.lg(f"num_small num:{len(num_small)}")
        if len(num_small) > 0:
            DataDeal.num_describe(df[num_small], pc)
            return num_small
        else:
            return []

    def _setup_param_config(self, pc:ParamConfig, str_identity, col_types, num_small, alg_type,
                           model_ai_dir, model_num, file_num, is_train,
                           label_name, drop_columns, date_type=None,classify_type2 = [[]],bool_type = [] ):
        """
        设置参数配置对象的通用方法

        Args:
            pc (ParamConfig): 参数配置对象
            str_identity (str): 标识列
            col_types (dict): 列类型字典
            num_small (list): 小数值列列表
            alg_type (str): 算法类型
            model_ai_dir (str): 模型保存目录
            model_num (int): 模型编号
            file_num (int): 文件编号
            is_train (bool): 是否为训练
            label_name (str): 标签列名
            drop_columns (list): 要删除的列
            date_type (list, optional): 日期类型列列表
        """
        # DataDealDL.data_deal需要的12个参数
        pc.col_type.identity       = str_identity
        pc.col_type.num_type       = col_types["num_type"]
        pc.col_type.num_small      = num_small
        pc.col_type.classify_type  = col_types["classify_type"]
        pc.col_type.classify_type2 = classify_type2  #一组类别使用同一个字典
        pc.col_type.date_type      = date_type if date_type is not None else []
        pc.col_type.bool_type      = bool_type
        pc.alg_type                = alg_type
        pc.model_save_dir          = model_ai_dir
        pc.model_num               = model_num
        pc.file_num                = file_num   #第几个文件,默认1
        pc.is_train                = is_train

        #其他参数
        pc.label_name              = label_name
        pc.drop_cols               = drop_columns

    def _log_data_info(self, pc:ParamConfig, num_small):
        """
        记录数据信息的通用方法

        Args:
            pc (ParamConfig): 参数配置对象
            num_small (list): 小数值列列表
        """
        pc.lg(pc.col_type.num_type[:3])
        pc.lg(f"num_small num:{len(num_small)},num type num:{len(pc.col_type.num_type)}")
        pc.lg(pc.col_type.classify_type[:3])
        pc.lg(f"is_merge_identity:{pc.is_merge_identity}")

    def _process_data_with_deal_dl(self, df, pc:ParamConfig):
        """
        使用DataDealDL处理数据的通用方法

        Args:
            df (DataFrame): 数据框
            pc (ParamConfig): 参数配置对象

        Returns:
            DataFrame: 处理后的数据框
        """
        df_processed = DataDealDL.data_deal(df, pc)
        return df_processed

    def _common_data_processing_pipeline(self, 
                data_path, model_title, str_identity,
                alg_type, model_ai_dir, model_num, file_num,
                is_train, label_name, pc:ParamConfig, drop_columns,
                is_categorical_func_type='general', date_type=None, 
                sep='~',classify_type2 = [[]],bool_type = []):
        """
        通用数据处理管道

        Args:
            data_path (str): 数据文件路径
            model_title (str): 模型标题
            str_identity (str): 标识列
            alg_type (str): 算法类型
            model_ai_dir (str): 模型保存目录
            model_num (int): 模型编号
            file_num (int): 文件编号
            is_train (bool): 是否为训练
            label_name (str): 标签列名
            pc (ParamConfig): 参数配置对象
            drop_columns (list): 要删除的列
            is_categorical_func_type (str): 分类列判断函数类型，'general'或'tra'
            date_type (list, optional): 日期类型列列表
            sep (str): 分隔符，默认为'~'

        Returns:
            tuple: (处理后的DataFrame, 标签列, 参数配置对象)
        """
        # 1. 获取要使用的列
        usecols = self._get_usecols_from_model_title(model_title)

        # 2. 创建分类列判断函数
        if is_categorical_func_type == 'general':
            is_categorical_func = self._create_categorical_function_general()
        elif is_categorical_func_type == 'tra':
            is_categorical_func = self._create_categorical_function_tra()
        else:
            raise ValueError(f"未知的is_categorical_func_type: {is_categorical_func_type}")

        # 3. 加载数据并分类
        # print("data_path:",data_path)
        df, y, col_types = self._load_and_classify_data(
            data_path, label_name, str_identity, is_train,
            usecols, drop_columns, is_categorical_func, sep, date_type, bool_type
        )
        
        self.lg(f"classify_data----------------------")
        self.lg(f"col_types['date_type'] len = {len(col_types['date_type'])}")
        self.lg(f"col_types['num_type'] len = {len(col_types['num_type'])}")
        self.lg(f"col_types['classify_type'] len = {len(col_types['classify_type'])}")
        self.lg(f"df[:3]:\n{df[:3]}")

        # 4. 分析数值列
        num_small = self._analyze_numeric_columns(df, pc)

        # 5. 设置参数配置
        self._setup_param_config(pc, str_identity, col_types, num_small, alg_type,
                               model_ai_dir, model_num, file_num, is_train,
                               label_name, drop_columns, date_type)

        # 6. 记录数据信息
        self._log_data_info(pc, num_small)

        # 7. 处理数据
        df_processed = self._process_data_with_deal_dl(df, pc)

        return df_processed, y, pc

    def data_deal_train(self, data_path, model_title, str_identity,
                       alg_type, model_ai_dir, model_num, file_num=1,
                       is_train=True, label_name=None, pc:ParamConfig=None,
                       drop_columns=None, date_type=[], sep='~',
                       classify_type2 = [[]],bool_type = []):
        """
        通用数据训练处理方法 - 重构版本

        使用通用数据处理管道来处理训练数据，简化代码并提高可维护性

        Args:
            data_path (str): 数据文件路径
            model_title (str): 模型标题
            str_identity (str): 标识列
            alg_type (str): 算法类型
            model_ai_dir (str): 模型保存目录
            model_num (int): 模型编号
            file_num (int): 文件编号，默认为1
            is_train (bool): 是否为训练，默认为True
            label_name (str): 标签列名
            pc (ParamConfig): 参数配置对象
            drop_columns (list): 要删除的列
            date_type (list, optional): 日期类型列列表
            sep (str): 分隔符，默认为'~'

        Returns:
            tuple: (处理后的DataFrame, 标签列, 参数配置对象)
        """
        self.lg = pc.lg
        return self._common_data_processing_pipeline(
            data_path=data_path,
            model_title=model_title,
            str_identity=str_identity,
            alg_type=alg_type,
            model_ai_dir=model_ai_dir,
            model_num=model_num,
            file_num=file_num,
            is_train=is_train,
            label_name=label_name,
            pc=pc,
            drop_columns=drop_columns,
            is_categorical_func_type='general',
            date_type=date_type,
            sep=sep
        )

    def data_deal_train_tra(self, data_path, model_title, str_identity,
                           alg_type, model_ai_dir, model_num, file_num=1,
                           is_train=True, label_name=None, pc:ParamConfig=None,
                           drop_columns=None, date_type=[], sep='~',
                           classify_type2 = [[]],bool_type = []):
        """
        交易数据训练处理方法 - 重构版本

        使用通用数据处理管道来处理交易训练数据，使用特定的分类列判断逻辑

        Args:
            data_path (str): 数据文件路径
            model_title (str): 模型标题
            str_identity (str): 标识列
            alg_type (str): 算法类型
            model_ai_dir (str): 模型保存目录
            model_num (int): 模型编号
            file_num (int): 文件编号，默认为1
            is_train (bool): 是否为训练，默认为True
            label_name (str): 标签列名
            pc (ParamConfig): 参数配置对象
            drop_columns (list): 要删除的列
            date_type (list, optional): 日期类型列列表
            sep (str): 分隔符，默认为'~'

        Returns:
            tuple: (处理后的DataFrame, 标签列, 参数配置对象)
        """
        self.lg = pc.lg
        return self._common_data_processing_pipeline(
            data_path=data_path,
            model_title=model_title,
            str_identity=str_identity,
            alg_type=alg_type,
            model_ai_dir=model_ai_dir,
            model_num=model_num,
            file_num=file_num,
            is_train=is_train,
            label_name=label_name,
            pc=pc,
            drop_columns=drop_columns,
            is_categorical_func_type='tra',
            date_type=date_type,
            sep=sep
        )


class Data2FeatureBase:
    
    pc = ParamConfig()
    
    def __init__(self):
        """
        主要逻辑
        1. 数据读取  read_csv
        2. 数据类型转换 data_type_change
        3. 数据观察  show_*
        4. 数字化，类别转索引 tonum_*
        5. 归一化  norm_*
        
        
        """

        pass 
        
    @classmethod
    def lg(cls,msg):
        cls.pc.lg(msg)
    
    @classmethod
    def _get_usecols(cls, heads=None, sep='~'):
        """
        根据列名头部字符串获取要使用的列

        Args:
            heads (str or None): 列名头部字符串，'all'表示使用所有列，其他值按分隔符分割
            sep (str): 分隔符，默认为'~'

        Returns:
            list or None: 要使用的列列表，None表示使用所有列
        """
        if heads is None or  heads == 'all':
            return None
        else:
            return heads.split(sep)
        

    @classmethod
    def read_csv(cls,data_path, sep=',', usecols=None, heads=None, heads_sep=None):
        """
        读取CSV文件并返回DataFrame

        Args:
            data_path (str): CSV文件路径
            sep (str, optional): 分隔符，默认为','
            usecols (list, optional): 要使用的列列表，None表示使用所有列
            heads (str, optional): 列名字符串，用分隔符分隔多个列名
            heads_sep (str, optional): 列名的分隔符，默认使用sep的值

        Returns:
            pd.DataFrame: 读取的数据框
        """
        if heads_sep is None:
            heads_sep = sep
        if heads is not None:
            usecols = cls._get_usecols(heads,sep=heads_sep)
        df = pd.read_csv(data_path, sep=sep, usecols=usecols)
        return df 
    
    @classmethod
    def data_type_change(cls,df,num_type=None,classify_type=None,date_type=None):
        """
        转换DataFrame中指定列的数据类型；通常是指定num_type、date_type,将剩下的列转换成classify_type

        该方法用于将DataFrame中的列转换为指定的数据类型，支持数值型、分类型和日期型列的转换。
        主要用于数据预处理阶段，确保数据具有正确的类型以便后续分析。

        Args:
            df (pd.DataFrame): 输入的数据表
            num_type (list): 需要转换为数值型的列名列表，默认为None（不转换）
            classify_type (list): 需要转换为分类型的列名列表，默认为None（不转换）
            date_type (list): 需要转换为日期型的列名列表，默认为None（不转换）

        Returns:
            pd.DataFrame: 数据类型转换后的数据表

        使用示例：
            # 转换指定列的数据类型
            df_converted = Data2Feature.data_type_change(
                df,
                num_type=['age', 'salary'],      # 转换为数值型
                classify_type=['gender', 'city'], # 转换为分类型
                date_type=['create_time', 'update_time']  # 转换为日期型
            )

        注意事项：
        - 转换失败的列会保持原有数据类型
        - 日期转换支持常见的日期格式
        - 数值转换会将无法解析的值设为NaN
        
        处理逻辑：
        1. 自动推断数值列：如果num_type为空或None，则自动推断
           - 使用data.select_dtypes('number')选择所有数值类型的列
           - 包括int, float, bool等数值类型，确保数值数据统一处理

        2. 自动推断类别列：如果classify_type为空或None，则自动推断
           - 从所有列中排除num_type和date_type列，剩余的作为类别列
           - 这种方式可以简化调用，无需手动指定所有类别列

        3. 类别列处理：将指定的类别列转换为pandas string类型
           - 使用astype("string")而不是astype(str)，以获得更好的内存效率
           - 通过集合操作确保只处理实际存在的列

        4. 数值列处理：将指定的数值列转换为float64类型
           - float64提供了足够的数值精度，适用于大多数机器学习算法
           - 统一数值类型有助于后续的归一化和标准化处理

        5. 日期列处理：将指定的日期列转换为datetime类型
           - 首先检查是否已经是datetime类型，避免重复转换
           - 使用errors='coerce'参数，无效日期转为NaT而非报错
           - 支持多种日期格式的自动识别和转换
        """
        df = DataDeal.data_type_change(df,num_type=num_type,classify_type=classify_type,date_type=date_type)
        return df
        
    @classmethod
    def show_col_type(cls, df, numeric_only=False, non_numeric_only=False):
        """
        显示DataFrame列的数据类型

        Args:
            df (pd.DataFrame): 输入的数据表
            numeric_only (bool): 是否只显示数值列，默认为False
            non_numeric_only (bool): 是否只显示非数值列，默认为False

        Note:
            如果numeric_only和non_numeric_only都为False，显示所有列类型
            如果numeric_only为True，只显示数值列类型
            如果non_numeric_only为True，只显示非数值列类型
        """
        if numeric_only and non_numeric_only:
            print("警告：numeric_only和non_numeric_only不能同时为True，将显示所有列类型")
            print(df.dtypes)
        elif numeric_only:
            numeric_cols = df.select_dtypes(include=['number']).columns
            if len(numeric_cols) > 0:
                print("数值列类型：")
                print(df[numeric_cols].dtypes)
            else:
                print("没有数值列")
        elif non_numeric_only:
            non_numeric_cols = df.select_dtypes(exclude=['number']).columns
            if len(non_numeric_cols) > 0:
                print("非数值列类型：")
                print(df[non_numeric_cols].dtypes)
            else:
                print("没有非数值列")
        else:
            print(df.dtypes)
       
    @classmethod
    def show_date_type(cls, df):
        """
        展示日期列的数据类型

        功能:
        1. 识别DataFrame中的日期和时间列
        2. 显示日期列的数据类型
        3. 提供日期列的基本统计信息
        4. 显示日期范围和格式信息

        参数:
        df (pd.DataFrame): 输入的数据表

        返回:
        dict: 日期列类型信息字典，key为日期列名，value为数据类型
              如果没有日期列或DataFrame为空，返回空字典

        输出:
        打印日期列的类型信息和统计数据
        """
        if df is None or df.empty:
            print("DataFrame为空，无法分析日期列")
            return {}

        # 识别日期列的方法
        date_columns = []

        # 方法1: 通过pandas数据类型识别datetime64类型
        datetime_cols = df.select_dtypes(include=['datetime64[ns]', 'datetime64']).columns.tolist()
        date_columns.extend(datetime_cols)

        # 方法2: 通过列名模式识别可能的日期列
        potential_date_patterns = [
            'date', 'time', 'dt', 'timestamp', 'created_at', 'updated_at',
            'start_time', 'end_time', 'year', 'month', 'day'
        ]

        for col in df.columns:
            # 检查列名是否包含日期相关关键词
            if any(pattern in col.lower() for pattern in potential_date_patterns):
                if col not in date_columns:
                    # 进一步检查数据是否真的是日期格式
                    try:
                        # 尝试转换为datetime
                        pd.to_datetime(df[col].dropna().head(100))
                        date_columns.append(col)
                    except:
                        # 如果转换失败，说明不是日期列
                        pass

        # 方法3: 通过数据内容识别字符串格式的日期
        string_cols = df.select_dtypes(include=['object', 'string']).columns
        for col in string_cols:
            if col not in date_columns:
                try:
                    # 检查前几行是否可以解析为日期
                    sample_data = df[col].dropna().head(50)
                    if len(sample_data) > 0:
                        pd.to_datetime(sample_data)
                        date_columns.append(col)
                except:
                    pass

        # 移除重复项并保持顺序
        date_columns = list(dict.fromkeys(date_columns))

        if not date_columns:
            print("未发现日期列")
            print("\n建议:")
            print("1. 检查列名是否包含日期相关关键词")
            print("2. 确认日期列是否已转换为datetime类型")
            print("3. 使用 pd.to_datetime() 手动转换日期列")
            return {}

        print(f"发现 {len(date_columns)} 个日期列:")
        print("-" * 60)

        # 显示每个日期列的详细信息
        for i, col in enumerate(date_columns, 1):
            print(f"\n{i}. 列名: '{col}'")
            print(f"   数据类型: {df[col].dtype}")

            # 显示基本统计信息
            if df[col].notna().sum() > 0:
                # 获取非空的数据
                date_data = df[col].dropna()

                # 转换为datetime进行统计
                try:
                    date_data_dt = pd.to_datetime(date_data)

                    print(f"   非空值数量: {len(date_data_dt)}/{len(df)}")
                    print(f"   缺失值数量: {df[col].isna().sum()}")
                    print(f"   最早日期: {date_data_dt.min()}")
                    print(f"   最晚日期: {date_data_dt.max()}")
                    print(f"   日期范围: {(date_data_dt.max() - date_data_dt.min()).days} 天")

                    # 显示样本数据
                    print(f"   样本数据:")
                    for j, sample in enumerate(date_data.head(3)):
                        print(f"     [{j+1}] {sample}")

                except Exception as e:
                    print(f"   转换为datetime时出错: {e}")
                    print(f"   样本数据:")
                    for j, sample in enumerate(date_data.head(3)):
                        print(f"     [{j+1}] {sample}")
            else:
                print("   全为空值")

        # 显示日期列的总体统计
        print(f"\n{'='*60}")
        print(f"日期列汇总:")
        print(f"  总列数: {len(date_columns)}")
        print(f"  总数据量: {len(df)} 行")

        # 统计不同类型的日期列
        datetime_count = len(df.select_dtypes(include=['datetime64[ns]', 'datetime64']).columns)
        string_date_count = len(date_columns) - datetime_count

        print(f"  datetime类型列: {datetime_count}")
        print(f"  字符串日期列: {string_date_count}")

        if datetime_count > 0:
            print(f"\n建议: 字符串日期列可以使用以下代码转换为datetime:")
            for col in date_columns:
                if df[col].dtype in ['object', 'string']:
                    print(f"  df['{col}'] = pd.to_datetime(df['{col}'])")

        # 创建并返回日期列类型字典
        date_columns_dict = {}
        for col in date_columns:
            date_columns_dict[col] = str(df[col].dtype)
        print(date_columns_dict)
        return date_columns_dict
        
    @classmethod
    def get_col_names(cls, df, col_type='object'):
        """
        根据指定的数据类型获取DataFrame中的列名

        Args:
            df: pandas DataFrame
            col_type: 数据类型过滤条件，可选值：
                - 'object': object类型列
                - 'cat': 分类类型列（包括str, string, category）
                - 'num': 数值类型列（包括所有数字类型）
                - 'date': 日期类型列（包括datetime64[ns], datetime64）
                - 'datetime64[ns]': 精确的datetime64[ns]类型
                - 'datetime64': datetime64类型
                - 'int': 整数类型列
                - 'float': 浮点数类型列
                - 'bool': 布尔类型列
                - 'str': 字符串类型列
                - 'category': 分类类型列
                - 'all': 返回所有列名（默认行为）

        Returns:
            list: 符合指定类型的列名列表
        """
        import pandas as pd
        import numpy as np

        # 如果请求所有列，直接返回
        if col_type == 'all':
            return list(df.columns)

        # 定义类型映射关系
        type_mapping = {
            # 数值类型
            'num': ['int8', 'int16', 'int32', 'int64', 'uint8', 'uint16', 'uint32', 'uint64',
                   'float16', 'float32', 'float64', 'number'],
            'int': ['int8', 'int16', 'int32', 'int64', 'uint8', 'uint16', 'uint32', 'uint64', 'integer'],
            'float': ['float16', 'float32', 'float64', 'floating'],

            # 字符串和分类类型
            'cat': ['object', 'string', 'category', 'str'],
            'str': ['object', 'string'],
            'category': ['category'],

            # 日期时间类型
            'date': ['datetime64[ns]', 'datetime64', 'datetime'],
            'datetime64[ns]': ['datetime64[ns]'],
            'datetime64': ['datetime64', 'datetime64[ns]'],

            # 布尔类型
            'bool': ['bool', 'boolean'],

            # 对象类型（保持向后兼容）
            'object': ['object'],
        }

        # 获取请求的类型列表
        target_types = type_mapping.get(col_type, [col_type])

        # 收集符合条件的列名
        result_columns = []

        for col in df.columns:
            col_dtype = str(df[col].dtype).lower()

            # 检查列的数据类型是否匹配目标类型
            for target_type in target_types:
                if target_type.lower() in col_dtype:
                    result_columns.append(col)
                    break

        return result_columns

    @classmethod
    def get_cat_types(cls, df):
        """
        获取DataFrame中分类类型的列名

        Args:
            df: pandas DataFrame

        Returns:
            list: 分类类型的列名列表
        """
        return cls.get_col_names(df, 'cat')

    @classmethod
    def get_col_names_by_pattern(cls, df, pattern='.*'):
        """
        根据正则表达式模式获取列名

        Args:
            df: pandas DataFrame
            pattern: 正则表达式模式，默认匹配所有列

        Returns:
            list: 匹配模式的列名列表
        """
        import re
        return [col for col in df.columns if re.match(pattern, col)]

    @classmethod
    def get_col_types_summary(cls, df):
        """
        获取DataFrame中各列的数据类型汇总

        Args:
            df: pandas DataFrame

        Returns:
            dict: 数据类型到列名列表的映射
        """
        type_summary = {}
        for col in df.columns:
            dtype = str(df[col].dtype)
            if dtype not in type_summary:
                type_summary[dtype] = []
            type_summary[dtype].append(col)
        return type_summary
        
    @classmethod
    def show_null_count(cls,df):
        print(df.isnull().sum())
        
    @classmethod
    def show_one_row(cls, df=None, row_idx=0, n=10, show_all=False, is_print=False):
        """
        显示DataFrame中指定行的前n个字段

        参数:
        df: DataFrame对象，如果为None则使用全局的df_final_result
        row_idx: 行索引，默认为0（第一行）
        n: 显示的字段数量，默认为10个
        show_all: 是否显示所有字段，如果为True则忽略n参数

        功能:
        1. 显示指定行的前n个字段的键值对
        2. 支持显示DataFrame的基本信息
        3. 提供字段计数和总览信息
        4. 支持显示所有字段或限制显示数量
        """
        import pandas as pd

        # 检查DataFrame是否为空
        if df is None or df.empty:
            cls.pc.lg("DataFrame为空，没有数据可显示")
            return

        # 检查行索引是否有效
        if row_idx < 0 or row_idx >= len(df):
            cls.pc.lg(f"错误: 行索引 {row_idx} 超出范围 [0, {len(df)-1}]")
            return

        # 显示DataFrame基本信息
        cls.pc.lg(f"DataFrame形状: {df.shape}")
        cls.pc.lg(f"显示第 {row_idx} 行（索引: {df.index[row_idx]}）")
        cls.pc.lg(f"总字段数: {len(df.columns)}")

        if show_all:
            cls.pc.lg(f"显示所有字段:")
            display_count = len(df.columns)
        else:
            cls.pc.lg(f"显示前 {n} 个字段:")
            display_count = min(n, len(df.columns))

        cls.pc.lg("-" * 60)

        # 显示指定行的字段
        count = 0
        for k, v in df.iloc[row_idx].items():
            # 格式化显示
            if pd.isna(v):
                value_str = "NaN"
            elif isinstance(v, float):
                if abs(v) < 0.001:
                    value_str = f"{v:.6f}"
                else:
                    value_str = f"{v:.3f}"
            elif isinstance(v, (int, np.integer)):
                value_str = str(v)
            else:
                value_str = str(v)
                # 限制字符串长度
                if len(value_str) > 50:
                    value_str = value_str[:47] + "..."

            cls.pc.lg(f"{k:30}: {value_str}")
            if is_print:
                print(f"{k:30}: {value_str}")
                
            count += 1

            # 如果不显示全部且达到指定数量，则停止
            if not show_all and count >= display_count:
                break

        cls.pc.lg("-" * 60)

        # 如果还有未显示的字段，提示用户
        if not show_all and len(df.columns) > n:
            remaining = len(df.columns) - n
            cls.pc.lg(f"还有 {remaining} 个字段未显示，使用 show_all=True 可显示全部")

            
    @classmethod
    def show_unique_count(cls,df):
        print(df.nunique())
        
        
        
    @classmethod
    def _categorical_not_num_date(cls,df,num_type=[],date_type=[]):
        """
        创建分类列判断函数，判断逻辑为排除数值列和日期列

        如果num_type为空，则选择pandas数表df中类型为number的列，
        如果date_type为空或None，则自动推断df中日期类型的列作为日期列，
        同时排除类型为日期的列以及date_type中指定的列

        Args:
            df (pd.DataFrame): 输入的数据表
            num_type (list): 指定的数值列列表，如果为空则自动推断
            date_type (list): 指定的日期列列表，如果为空则自动推断

        Returns:
            function: 分类列判断函数
        """
        # 如果num_type为空，自动推断数值列
        if num_type is None or len(num_type) == 0:
            num_type = df.select_dtypes('number').columns.tolist()

        # 如果date_type为空或None，自动推断日期列
        if date_type is None or len(date_type) == 0:
            # 使用pd.api.types.is_datetime64_any_dtype自动推断日期列
            date_type = [col for col in df.columns
                        if pd.api.types.is_datetime64_any_dtype(df[col])]

        # 获取所有列名
        col_all = df.columns.tolist()

        # 排除数值列和指定的日期列
        exclude_cols = set(num_type) | set(date_type)
        categorical_cols = list(set(col_all) - exclude_cols)
        return categorical_cols
        
        
        
    @classmethod
    def show_col_diff(cls, df1, df2, show_common=False):
        """显示两个数据表之间列的差异

        Args:
            df1 (pd.DataFrame): 第一个数据表
            df2 (pd.DataFrame): 第二个数据表

        Returns:
            tuple: (cols1, cols2,common_cols)
                cols1 (list): 第一个数据表缺失的列（在df2中有但df1中没有）
                cols2 (list): 第二个数据表缺失的列（在df1中有但df2中没有）
                common_cols:  公共列

        """
        # 获取两个DataFrame的列名
        cols1_set = set(df1.columns)
        cols2_set = set(df2.columns)

        # 找出差异
        # df1缺失的列：在df2中有但df1中没有
        cols1_missing = list(cols2_set - cols1_set)
        # df2缺失的列：在df1中有但df2中没有
        cols2_missing = list(cols1_set - cols2_set)

        # 找出共同的列
        common_cols = list(cols1_set & cols2_set)

        # 打印差异信息
        print(f"\n=== 列差异分析 ===")
        print(f"DataFrame1 列数: {len(cols1_set)}")
        print(f"DataFrame2 列数: {len(cols2_set)}")
        print(f"共同列数: {len(common_cols)}")

        if cols1_missing:
            print(f"\nDataFrame1 缺失的列 ({len(cols1_missing)}个):")
            for col in sorted(cols1_missing):
                print(f"  - {col}")
        else:
            print("\nDataFrame1 没有缺失的列")

        if cols2_missing:
            print(f"\nDataFrame2 缺失的列 ({len(cols2_missing)}个):")
            for col in sorted(cols2_missing):
                print(f"  - {col}")
        else:
            print("\nDataFrame2 没有缺失的列")

        if show_common:
            if common_cols:
                print(f"\n共同列 ({len(common_cols)}个):")
                for col in sorted(common_cols):
                    print(f"  - {col}")
                return cols1_missing, cols2_missing, common_cols
            else:
                print("\n没有共同列")
                return cols1_missing, cols2_missing, []

        return cols1_missing, cols2_missing 
        
    @classmethod
    def tonum_col2index(cls,df, identity=[], classify_type=[], classify_type2=[],
                  dict_file="dict_file.dict", is_pre=False,
                  word2id=None, start_index=1):
        """
        将分类列转换为数值索引，支持训练和预测模式

        该方法将DataFrame中的分类特征列转换为数值索引，便于机器学习模型处理。
        支持单列分类和多列组合分类的转换，并能保存和加载编码字典。

        Args:
            df (pd.DataFrame): 输入的数据表
            identity (list): 标识列列表，不参与编码，默认为空
            classify_type (list): 需要编码的单列分类列名列表，默认为空
            classify_type2 (list): 需要编码的多列组合分类列列表，每个元素为列名列表，默认为空
            dict_file (str): 编码字典保存路径，默认为"dict_file.dict"
            is_pre (bool): 是否为预测模式，默认为False（训练模式）
            word2id (dict): 预定义的词汇到ID映射字典，默认为None
            start_index (int): 索引起始值，默认为1

        Returns:
            pd.DataFrame: 编码后的数据表，分类列已转换为数值索引

        Raises:
            ValueError: 当classify_type2中的元素不是列表类型时抛出

        处理逻辑：
        1. 参数验证：检查classify_type2参数格式，确保每个元素都是列表
        2. 调用底层DataDeal.col2index方法进行实际的编码转换
        3. 支持训练模式和预测模式的不同处理逻辑

        参数说明：
        - classify_type: 单列分类，如["性别", "学历"]
        - classify_type2: 多列组合分类，如 [["省份", "城市"], ["部门", "职位"]]
        - is_pre=True时为预测模式，会加载已有的编码字典
        - is_pre=False时为训练模式，会创建新的编码字典并保存
        """
        # 检验classify_type2参数，如果不为空或None，则其元素必须为列表
        if classify_type2 is not None and classify_type2:
            for i, item in enumerate(classify_type2):
                if not isinstance(item, list):
                    raise ValueError(f"classify_type2的第{i+1}个元素必须是列表，但得到了{type(item)}: {item}")

        # 确保classify_type2为列表类型（避免None值传递给底层方法）
        classify_type2 = classify_type2 or []

        df = DataDeal.col2index(df,
                identity=identity, classify_type=classify_type, classify_type2=classify_type2,
                dict_file=dict_file, is_pre=is_pre,
                word2id=word2id, start_index=start_index)
        return df  
    
    @classmethod
    def tonum_label_encoding(cls, df, identity=[], classify_type=[], file_path=None,
                             is_pre=False, force_rewrite=False):
        """
        对分类列进行LabelEncoder编码，支持训练和预测模式

        Args:
            df (pd.DataFrame): 输入的数据表
            identity (list): 标识列列表，不参与编码，默认为空
            classify_type (list): 需要编码的分类列名列表，如果为空或None则自动推断
            file_path (str): 编码字典保存路径，如果为None则不保存/加载字典
            is_pre (bool): 是否为预测模式，默认为False（训练模式）
            force_rewrite (bool): 是否强制重新训练编码器，默认为False

        Returns:
            pd.DataFrame: 编码后的数据表

        处理逻辑：
        1. 训练模式(is_pre=False)：
           - 如果编码字典文件存在且force_rewrite=False，加载字典并应用
           - 否则重新训练编码器，保存字典并应用

        2. 预测模式(is_pre=True)：
           - 如果force_rewrite=True，则重新训练编码器（忽略is_pre）
           - 否则只加载并应用现有编码器，不重新训练

        3. 如果file_path为None，始终进行训练但不保存字典

        4. 如果classify_type为空或None，自动推断类别列：
           - 选择df中所有非数字列作为类别列
           - 排除identity中指定的标识列
        """
        # 自动推断类别列（如果classify_type为空）
        if not classify_type:
            # 获取所有非数字列
            non_numeric_cols = df.select_dtypes(exclude=['number']).columns.tolist()

            # 排除identity中的列
            identity_set = set(identity) if identity else set()
            classify_type = [col for col in non_numeric_cols if col not in identity_set]

            if classify_type:
                print(f"自动推断类别列：{classify_type}")
            else:
                print("没有找到合适的类别列进行编码")
                return df

        # 检查分类列是否存在于DataFrame中
        valid_cols = [col for col in classify_type if col in df.columns]
        if len(valid_cols) != len(classify_type):
            missing_cols = set(classify_type) - set(valid_cols)
            print(f"警告：以下列不存在于DataFrame中：{missing_cols}")
            classify_type = valid_cols
            if not classify_type:
                return df

        # 根据模式决定处理逻辑
        should_load = (file_path and os.path.exists(file_path) and
                      not force_rewrite and is_pre)

        if should_load:
            # 预测模式：加载现有编码字典
            try:
                label_encoding_dict = pkl_load(file_path)
                cls._apply_existing_encoders(df, classify_type, label_encoding_dict)
                print("预测模式：已加载现有编码字典")
            except Exception as e:
                print(f"加载编码字典失败，重新训练编码器：{e}")
                force_rewrite = True  # 设置为重新训练

        if force_rewrite or not should_load:
            # 训练模式或强制重写：训练新的编码器
            mode = "强制重写" if force_rewrite else ("预测模式（重训练）" if is_pre else "训练模式")
            print(f"{mode}：训练新的编码器")

            label_encoding_dict = cls._train_new_encoders(df, classify_type)

            # 保存编码字典（如果指定了文件路径）
            if file_path:
                try:
                    pkl_save(label_encoding_dict, file_path=file_path)
                    print(f"编码字典已保存至：{file_path}")
                except Exception as e:
                    print(f"保存编码字典失败：{e}")

        return df

    @classmethod
    def _apply_existing_encoders(cls, df, classify_type, label_encoding_dict):
        """应用现有的编码器，将未知类别映射为<UNK>（编码为0）"""
        for col in classify_type:
            if col in label_encoding_dict:
                try:
                    le = preprocessing.LabelEncoder()
                    le.classes_ = label_encoding_dict[col]

                    # 处理新出现的类别（将其映射为0，即<UNK>）
                    unique_values = set(df[col].astype(str).unique())
                    known_values = set(le.classes_)
                    unknown_values = unique_values - known_values

                    if unknown_values:
                        print(f"列 '{col}' 发现未知类别：{unknown_values}，将映射为<UNK>（编码为0）")
                        df[col] = df[col].astype(str).apply(
                            lambda x: le.transform([x])[0] if x in known_values else 0
                        )
                    else:
                        df[col] = le.transform(df[col].astype(str))

                except Exception as e:
                    print(f"应用列 '{col}' 的编码器失败：{e}")
                    # 使用默认值0填充（<UNK>）
                    df[col] = 0
            else:
                print(f"警告：编码字典中不存在列 '{col}'，使用默认值0（<UNK>）")
                df[col] = 0

    @classmethod
    def _train_new_encoders(cls, df, classify_type):
        """训练新的编码器，为每个分类列添加<UNK>标记（编码为0）"""
        label_encoding_dict = {}
        for col in classify_type:
            try:
                # 获取该列的唯一值，过滤掉空值
                unique_values = df[col].astype(str).unique()

                # 添加<UNK>标记到类别列表中，并将其放在第一位（编码为0）
                all_classes = ['<UNK>'] + list(unique_values)

                le = preprocessing.LabelEncoder()
                le.fit(all_classes)

                # 对数据进行编码，将未知值映射为<UNK>（编码为0）
                # 由于训练数据中的值都是已知值，所以直接编码即可
                df[col] = le.transform(df[col].astype(str))

                label_encoding_dict[col] = le.classes_
                print(f"列 '{col}' 编码完成，类别数量：{len(le.classes_)}（包含<UNK>标记）")
            except Exception as e:
                print(f"训练列 '{col}' 的编码器失败：{e}")
                # 使用简单映射作为备用方案，同样添加<UNK>标记
                unique_values = df[col].astype(str).unique()
                all_classes = ['<UNK>'] + list(unique_values)
                value_to_id = {cls: idx for idx, cls in enumerate(all_classes)}

                # 对数据进行编码，已知值从1开始，<UNK>为0
                df[col] = df[col].astype(str).map(value_to_id)
                label_encoding_dict[col] = all_classes
                print(f"列 '{col}' 使用简单映射，类别数量：{len(all_classes)}（包含<UNK>标记）")

        return label_encoding_dict
 
    def _analyze_numeric_columns(self, df, pc, threshold=100):
        """
        分析数值列，找出最大值小于阈值的列

        Args:
            df (DataFrame): 数据框
            pc (ParamConfig): 参数配置对象
            threshold (int): 阈值，默认为100

        Returns:
            list: 小于阈值的列名列表
        """
        num_small = DataDeal.columns_by_max_value(df, condition='less', threshold=threshold)
        pc.lg(f"num_small num:{len(num_small)}")
        if len(num_small) > 0:
            DataDeal.num_describe(df[num_small], pc)
            return num_small
        else:
            return []
 
    @classmethod
    def _setup_param_config(cls, pc:ParamConfig, str_identity, col_types, num_small, alg_type,
                           model_ai_dir, model_num, file_num, is_train,
                           label_name, drop_columns, date_type=None,classify_type2 = [[]],bool_type = [] ):
        """
        设置参数配置对象的通用方法

        Args:
            pc (ParamConfig): 参数配置对象
            str_identity (str): 标识列
            col_types (dict): 列类型字典
            num_small (list): 小数值列列表
            alg_type (str): 算法类型
            model_ai_dir (str): 模型保存目录
            model_num (int): 模型编号
            file_num (int): 文件编号
            is_train (bool): 是否为训练
            label_name (str): 标签列名
            drop_columns (list): 要删除的列
            date_type (list, optional): 日期类型列列表
        """
        # DataDealDL.data_deal需要的12个参数
        pc.col_type.identity       = str_identity
        pc.col_type.num_type       = col_types["num_type"]
        pc.col_type.num_small      = num_small
        pc.col_type.classify_type  = col_types["classify_type"]
        pc.col_type.classify_type2 = classify_type2  #一组类别使用同一个字典
        pc.col_type.date_type      = date_type if date_type is not None else []
        pc.col_type.bool_type      = bool_type
        pc.alg_type                = alg_type
        pc.model_save_dir          = model_ai_dir
        pc.model_num               = model_num
        pc.file_num                = file_num   #第几个文件,默认1
        pc.is_train                = is_train

        #其他参数
        pc.label_name              = label_name
        pc.drop_cols               = drop_columns

    @classmethod
    def _log_data_info(cls, pc:ParamConfig, num_small):
        """
        记录数据信息的通用方法

        Args:
            pc (ParamConfig): 参数配置对象
            num_small (list): 小数值列列表
        """
        pc.lg(pc.col_type.num_type[:3])
        pc.lg(f"num_small num:{len(num_small)},num type num:{len(pc.col_type.num_type)}")
        pc.lg(pc.col_type.classify_type[:3])
        pc.lg(f"is_merge_identity:{pc.is_merge_identity}")

 
 
 
    @classmethod
    def norm_min_max_scaler(cls, X, num_type=[], 
                            model_path=f"min_max_scaler.pkl", 
                            is_train=True):
        if is_train:
            df = DataDeal.min_max_scaler(X, 
                            num_type=num_type, 
                            model_path=model_path, 
                            reuse=True, 
                            col_sort=True, 
                            force_rewrite=True)
        else:
            df = DataDeal.min_max_scaler(X, 
                            num_type=num_type, 
                            model_path=model_path, 
                            reuse=True, 
                            col_sort=True)
        return df  
    
    def _process_data_with_deal_dl(self, df, pc:ParamConfig):
        """
        使用DataDealDL处理数据的通用方法

        Args:
            df (DataFrame): 数据框
            pc (ParamConfig): 参数配置对象

        Returns:
            DataFrame: 处理后的数据框
        """
        df_processed = DataDealDL.data_deal(df, pc)
        return df_processed
    
    @classmethod
    def getXy(cls,
            data_path, heads, str_identity,
            alg_type, model_ai_dir, model_num, file_num,
            is_train, label_name, pc:ParamConfig, drop_columns,
            is_categorical_func_type=None, date_type=None, 
            sep='~',classify_type2 = [[]],bool_type = []):
        df = cls.read_csv(data_path, sep=sep, heads=heads)
        
        pass 
    
    @classmethod
    def processing(cls, 
                df, str_identity,
                alg_type, model_ai_dir, model_num, file_num,
                is_train, label_name, pc:ParamConfig, drop_columns,
                date_type, col_types):
        """
        通用数据处理管道

        Args:
            data_path (str): 数据文件路径
            model_title (str): 模型标题
            str_identity (str): 标识列
            alg_type (str): 算法类型
            model_ai_dir (str): 模型保存目录
            model_num (int): 模型编号
            file_num (int): 文件编号
            is_train (bool): 是否为训练
            label_name (str): 标签列名
            pc (ParamConfig): 参数配置对象
            drop_columns (list): 要删除的列
            is_categorical_func_type (str): 分类列判断函数类型，'general'或'tra'
            date_type (list, optional): 日期类型列列表
            sep (str): 分隔符，默认为'~'

        Returns:
            tuple: (处理后的DataFrame, 标签列, 参数配置对象)
        """
  
        # 4. 分析数值列
        num_small = cls._analyze_numeric_columns(df, pc)

        # 5. 设置参数配置
        cls._setup_param_config(pc, str_identity, col_types, num_small, alg_type,
                               model_ai_dir, model_num, file_num, is_train,
                               label_name, drop_columns, date_type)

        # 6. 记录数据信息
        cls._log_data_info(pc, num_small)

        # 7. 处理数据
        df_processed = cls._process_data_with_deal_dl(df, pc)

        return df_processed, pc
    
    @classmethod
    def deal(cls, 
                data_path, model_title, str_identity,
                alg_type, model_ai_dir, model_num, file_num,
                is_train, label_name, pc:ParamConfig, drop_columns,
                is_categorical_func_type=None, date_type=None, 
                sep='~',classify_type2 = [[]],bool_type = []):
        pass 
        
   



class Data2Feature(Data2FeatureBase):
    
    
    def __init__(self):
        """
        主要逻辑
        1. 数据读取  read_csv
        2. 数据类型转换 data_type_change
        3. 数据观察  show_*
        4. 数字化，类别转索引 tonum_*
        5. 归一化  norm_*
        
        
        """
        super().__init__()

        pass 
        


    @classmethod
    def read_csv(cls,data_path, sep=',', usecols=None, heads=None, heads_sep=None):
        """
        读取CSV文件并返回DataFrame

        Args:
            data_path (str): CSV文件路径
            sep (str, optional): 分隔符，默认为','
            usecols (list, optional): 要使用的列列表，None表示使用所有列
            heads (str, optional): 列名字符串，用分隔符分隔多个列名
            heads_sep (str, optional): 列名的分隔符，默认使用sep的值

        Returns:
            pd.DataFrame: 读取的数据框
        """
        if heads_sep is None:
            heads_sep = sep
        if heads is not None:
            usecols = cls._get_usecols(heads,sep=heads_sep)
        df = pd.read_csv(data_path, sep=sep, usecols=usecols)
        return df 
    
        
    @classmethod
    def data_agg(cls, df,identifys=[['From','time8'],['To','time8']],
                num_type=['Amount'],
                classify_type=['Payment Format', 'Currency'],
                stat_lable=['count','sum','mean','std','min','max','median','q25','q75','skew','kurtosis','cv','iqr','range','se']):
        """
        银行交易流水数据聚合统计方法

        参数:
        df: 输入的交易数据DataFrame
        identifys: 分组标识列列表，默认为[['From','time8'],['To','time8']]
        num_type: 数值类型列名列表，默认为['Amount']
        classify_type: 分类类型列名列表，默认为['Payment Format', 'Currency']
        stat_lable: 需要计算的统计指标列表，支持的指标包括:
                - count: 计数
                - sum: 求和
                - mean: 均值
                - std: 标准差
                - min: 最小值
                - max: 最大值
                - median: 中位数
                - q25: 25%分位数
                - q75: 75%分位数
                - skew: 偏度
                - kurtosis: 峰度
                - cv: 变异系数
                - iqr: 四分位距
                - range: 极差
                - se: 标准误差

        背景:
        1. 银行交易流水数据集，包含From,To,time8,time14,Amount,Payment Format,Currency
        2. From为付款账户，To为收款账户
        3. time8为8位按天的时间，['From','time8']意味着按天对付款账户分类
        4. ['To','time8']意味着将来会按天对收款账户分类

        主要逻辑：
        1. 对于每个identifys[i]：
        - 形成临时df_tmp = num_type + classify_type + identifys[i]的列组合
        - 按identifys[i]分组聚合数据
        - 根据stat_lable参数生成对应的统计结果
        2. 将所有df_tmp合并成新的DataFrame返回
        3. 只计算stat_lable中指定的统计指标，提高计算效率

        示例:
        # 只计算基础统计指标
        df_basic = data_agg(df, stat_lable=['count','sum','mean','std'])

        # 计算完整的波动性指标
        df_full = data_agg(df, stat_lable=['count','sum','mean','std','q25','q75','skew','kurtosis','cv','iqr'])
        """
        import pandas as pd
        import numpy as np

        all_results = []

        # 对identifys中的每个分组键进行处理
        # for i, group_cols in enumerate(identifys):
        #     # print(f"处理分组键 {i+1}/{len(identifys)}: {group_cols}")

        #     # 构建临时df_tmp的列：num_type + classify_type + group_cols
        #     tmp_cols = []
        #     tmp_cols.extend(group_cols)  # 添加分组键列

        #     # 检查并添加数值类型列
        #     available_num_cols = [col for col in num_type if col in df.columns]
        #     tmp_cols.extend(available_num_cols)

        #     # 检查并添加分类类型列
        #     available_cat_cols = [col for col in classify_type if col in df.columns]
        #     tmp_cols.extend(available_cat_cols)

        #     # 创建临时DataFrame
        #     df_tmp = df[tmp_cols].copy()
        #     # print(f"临时DataFrame列: {df_tmp.columns.tolist()}")
        #     # print(f"临时DataFrame形状: {df_tmp.shape}")

        #     # 按当前分组键进行聚合
        #     grouped = df_tmp.groupby(group_cols)

        #     # 为当前分组创建统计结果
        #     group_results = []

            # print(f"开始数据聚合，统计指标: {stat_lable}")
        # print(f"分组标识: {identifys}, 数值列: {num_type}, 分类列: {classify_type}")

        # 对identifys中的每个分组键进行处理
        for i, group_cols in enumerate(identifys):
            # print(f"处理分组键 {i+1}/{len(identifys)}: {group_cols}")

            # 构建临时df_tmp的列：num_type + classify_type + group_cols
            tmp_cols = []
            tmp_cols.extend(group_cols)  # 添加分组键列

            # 检查并添加数值类型列
            available_num_cols = [col for col in num_type if col in df.columns]
            tmp_cols.extend(available_num_cols)

            # 检查并添加分类类型列
            available_cat_cols = [col for col in classify_type if col in df.columns]
            tmp_cols.extend(available_cat_cols)

            # 创建临时DataFrame
            df_tmp = df[tmp_cols].copy()
            # print(f"临时DataFrame列: {df_tmp.columns.tolist()}")
            # print(f"临时DataFrame形状: {df_tmp.shape}")

            # 按当前分组键进行聚合
            grouped = df_tmp.groupby(group_cols)

            # 为当前分组创建统计结果
            group_results = []

            # 1. 对数值列进行统计
            for num_col in available_num_cols:
                # print(f"  对数值列 {num_col} 进行统计...")

                # 根据stat_lable参数动态生成统计列名
                stat_columns = []
                for stat in stat_lable:
                    stat_columns.append(f'{num_col}_{stat}')

                # print(f"  将计算统计列: {stat_columns}")

                # 获取所有唯一的分组组合
                all_groups = df_tmp[group_cols].drop_duplicates()
                # print(f"  发现 {len(all_groups)} 个唯一分组")

                # 创建结果DataFrame，包含所有分组和统计列
                num_result = all_groups.copy()
                for col in stat_columns:
                    num_result[col] = 0.0  # 初始化所有统计列为0

                # 创建字典来快速查找分组对应的行索引
                group_to_index = {}
                for idx, row in all_groups.iterrows():
                    key = tuple(row[group_cols])
                    group_to_index[key] = idx

                # 计算每个分组的统计指标
                for group_key, group_data in grouped:
                    # print(f"    处理分组: {group_key}, 数据量: {len(group_data)}")

                    try:
                        values = group_data[num_col].dropna()  # 移除NaN值

                        if len(values) == 0:
                            # print(f"      警告: 分组 {group_key} 没有有效数据")
                            continue

                        # 基础统计
                        count = len(values)
                        sum_val = values.sum()
                        mean_val = values.mean()
                        std_val = values.std(ddof=0) if count > 1 else 0.0
                        min_val = values.min()
                        max_val = values.max()
                        median_val = values.median()

                        # 分位数
                        q25_val = values.quantile(0.25)
                        q75_val = values.quantile(0.75)

                        # 衍生统计
                        skew_val = values.skew() if count > 2 else 0.0
                        kurt_val = values.kurtosis() if count > 3 else 0.0
                        cv_val = std_val / mean_val if mean_val != 0 else 0.0
                        iqr_val = q75_val - q25_val
                        range_val = max_val - min_val
                        se_val = std_val / np.sqrt(count) if count > 0 else 0.0

                        # 获取该分组在结果DataFrame中的行索引
                        if group_key in group_to_index:
                            row_idx = group_to_index[group_key]

                            # 更新统计值
                            num_result.at[row_idx, f'{num_col}_count'] = count
                            num_result.at[row_idx, f'{num_col}_sum'] = sum_val
                            num_result.at[row_idx, f'{num_col}_mean'] = mean_val
                            num_result.at[row_idx, f'{num_col}_std'] = std_val
                            num_result.at[row_idx, f'{num_col}_min'] = min_val
                            num_result.at[row_idx, f'{num_col}_max'] = max_val
                            num_result.at[row_idx, f'{num_col}_median'] = median_val
                            num_result.at[row_idx, f'{num_col}_q25'] = q25_val
                            num_result.at[row_idx, f'{num_col}_q75'] = q75_val
                            num_result.at[row_idx, f'{num_col}_skew'] = skew_val
                            num_result.at[row_idx, f'{num_col}_kurtosis'] = kurt_val
                            num_result.at[row_idx, f'{num_col}_cv'] = cv_val
                            num_result.at[row_idx, f'{num_col}_iqr'] = iqr_val
                            num_result.at[row_idx, f'{num_col}_range'] = range_val
                            num_result.at[row_idx, f'{num_col}_se'] = se_val

                        # print(f"      完成 {count} 个数据点的统计")

                    except Exception as e:
                        print(f"      计算分组 {group_key} 的统计时出错: {e}")
                        continue

                # 确保所有统计列都存在且为数值类型
                for col in stat_columns:
                    if col not in num_result.columns:
                        num_result[col] = 0.0
                    else:
                        num_result[col] = pd.to_numeric(num_result[col], errors='coerce').fillna(0.0)

                # print(f"  数值列 {num_col} 统计完成，结果形状: {num_result.shape}")
                group_results.append(num_result)

            # 2. 对分类列进行交叉统计
            for cat_col in available_cat_cols:
                # print(f"  对分类列 {cat_col} 进行交叉统计...")

                # 获取唯一值（过滤掉NaN）
                unique_values = df_tmp[cat_col].dropna().unique()

                for num_col in available_num_cols:
                    # print(f"    处理分类列 {cat_col} 与数值列 {num_col} 的交叉统计")

                    # 预定义所有分类统计列
                    cat_stat_columns = []
                    for cat_value in unique_values:
                        cat_stat_columns.extend([
                            f'{cat_col}_{cat_value}_{num_col}_count',
                            f'{cat_col}_{cat_value}_{num_col}_sum',
                            f'{cat_col}_{cat_value}_{num_col}_mean',
                            f'{cat_col}_{cat_value}_{num_col}_std'
                        ])

                    # 获取所有唯一的分组组合
                    all_groups = df_tmp[group_cols].drop_duplicates()

                    # 创建分类统计结果DataFrame
                    cat_result = all_groups.copy()
                    for col in cat_stat_columns:
                        cat_result[col] = 0.0  # 初始化所有分类统计列为0

                    # 创建字典来快速查找分组对应的行索引
                    group_to_index = {}
                    for idx, row in all_groups.iterrows():
                        key = tuple(row[group_cols])
                        group_to_index[key] = idx

                    # 计算每个分类值的统计
                    for cat_value in unique_values:
                        filtered_data = df_tmp[df_tmp[cat_col] == cat_value]
                        if len(filtered_data) == 0:
                            continue

                        # print(f"      处理分类值 {cat_value}, 数据量: {len(filtered_data)}")

                        # 按分组键和分类值进行分组
                        cat_grouped = filtered_data.groupby(group_cols)

                        for group_key, group_data in cat_grouped:
                            try:
                                values = group_data[num_col].dropna()
                                if len(values) == 0:
                                    continue

                                count = len(values)
                                sum_val = values.sum()
                                mean_val = values.mean()
                                std_val = values.std(ddof=0) if count > 1 else 0.0

                                # 更新对应的统计值
                                if group_key in group_to_index:
                                    row_idx = group_to_index[group_key]
                                    cat_result.at[row_idx, f'{cat_col}_{cat_value}_{num_col}_count'] = count
                                    cat_result.at[row_idx, f'{cat_col}_{cat_value}_{num_col}_sum'] = sum_val
                                    cat_result.at[row_idx, f'{cat_col}_{cat_value}_{num_col}_mean'] = mean_val
                                    cat_result.at[row_idx, f'{cat_col}_{cat_value}_{num_col}_std'] = std_val

                            except Exception as e:
                                print(f"        计算分组 {group_key} 分类统计时出错: {e}")
                                continue

                    # 确保所有分类统计列都存在且为数值类型
                    for col in cat_stat_columns:
                        if col not in cat_result.columns:
                            cat_result[col] = 0.0
                        else:
                            cat_result[col] = pd.to_numeric(cat_result[col], errors='coerce').fillna(0.0)

                    # print(f"      分类列 {cat_col} 与数值列 {num_col} 交叉统计完成，结果形状: {cat_result.shape}")
                    group_results.append(cat_result)

            # 3. 合并当前分组的所有统计结果
            if group_results:
                # print(f"  合并 {len(group_results)} 个统计结果...")

                # 获取所有唯一的分组组合（确保包含所有可能的分组）
                all_groups = df_tmp[group_cols].drop_duplicates()

                # 创建包含所有分组的基准DataFrame
                group_final = all_groups.copy()

                # 合并所有统计结果到基准DataFrame
                for i, result_df in enumerate(group_results):
                    # print(f"    合并第 {i+1} 个结果，形状: {result_df.shape}")

                    # 使用外连接确保所有分组都被保留
                    group_final = group_final.merge(
                        result_df,
                        on=group_cols,
                        how='outer'
                    )

                # 添加分组标识
                group_final['group_key'] = '_'.join(group_cols)

                # 最终处理所有NaN值：将统计列的NaN转换为0
                for col in group_final.columns:
                    if col not in group_cols + ['group_key']:
                        group_final[col] = pd.to_numeric(group_final[col], errors='coerce').fillna(0.0)

                # print(f"  分组 {group_cols} 合并完成，最终形状: {group_final.shape}")
                # print(f"  NaN值数量: {group_final.isnull().sum().sum()}")
                all_results.append(group_final)
        

        # 4. 合并所有分组的最终结果
        if all_results:
            final_result = pd.concat(all_results, ignore_index=True)

            # 最终NaN值处理：确保所有统计列都没有NaN
            stat_cols = [col for col in final_result.columns if col != 'group_key']
            for col in stat_cols:
                if final_result[col].dtype in ['float64', 'int64']:
                    final_result[col] = final_result[col].fillna(0)

            # 将group_key列移动到第一列位置
            if 'group_key' in final_result.columns:
                cols = ['group_key'] + [col for col in final_result.columns if col != 'group_key']
                final_result = final_result[cols]

            return final_result
        else:
            return pd.DataFrame()


    @classmethod
    def cols_more2one(cls, df, cols=['From','To'], new_col_name='key'):
        """多列互斥合并为一列
        cols中的列是互斥的，同一行只能有一个列有值，其余列为NaN,现在将这些列合并为一个列,新列名为new_col_name
        """

        # 验证输入列是否存在
        missing_cols = [col for col in cols if col not in df.columns]
        if missing_cols:
            raise ValueError(f"以下列在DataFrame中不存在: {missing_cols}")

        # 创建新列，使用bfill或ffill来填充非NaN值
        # 方法1: 使用combine_first方法
        result_df = df.copy()

        # 初始化新列为NaN
        result_df[new_col_name] = np.nan

        # 按顺序合并列，后面的列会填充前面列的NaN位置
        # 使用更简单的方法避免StringDtype问题
        for col in cols:
            # 找出新列中为NaN但在当前列中不为NaN的位置
            mask = result_df[new_col_name].isna() & result_df[col].notna()
            # 在这些位置上用当前列的值填充
            result_df.loc[mask, new_col_name] = result_df.loc[mask, col]

        # 验证合并结果：检查是否存在冲突（即原数据中同一行有多个非NaN值）
        # 计算每行非NaN值的数量
        non_nan_count = df[cols].notna().sum(axis=1)
        conflicts = non_nan_count > 1

        if conflicts.any():
            print(f"警告: 发现 {conflicts.sum()} 行数据存在冲突（多列同时有值）")
            print("冲突行示例:")
            print(df[conflicts][cols].head())

            # 对于冲突行，优先使用第一个非NaN值
            for idx in df[conflicts].index:
                for col in cols:
                    if pd.notna(df.loc[idx, col]):
                        result_df.loc[idx, new_col_name] = df.loc[idx, col]
                        break

        # 删除原始列
        result_df = result_df.drop(columns=cols)

        # 将新列移动到第一列位置
        cols = [new_col_name] + [col for col in result_df.columns if col != new_col_name]
        result_df = result_df[cols]

        # print(f"成功将 {len(cols)-1} 列合并为 '{new_col_name}' 列")
        # print(f"合并后的非NaN值数量: {result_df[new_col_name].notna().sum()}")

        return result_df 

    @classmethod
    def data_agg_byday(cls, df,
                col_time='time8',
                interval=1,
                win_len=1,
                identifys=[['From','time8'],['To','time8']],
                num_type =['Amount'],
                classify_type=['Payment Format', 'Currency'],
                merge_del_cols=['From','To'],
                new_col_name='key',
                stat_lable=['count','sum','mean','std','min','max','median','q25','q75','skew','kurtosis','cv','iqr','range','se']):
        """
        按天滚动窗口聚合交易数据

        参数:
        df: 输入的交易数据DataFrame
        col_time: 时间列名，默认为'time8'
        interval: 滚动间隔，默认为1天
        win_len: 窗口长度，默认为1天
        identifys: 分组标识列列表，默认为[['From','time8'],['To','time8']]
        num_type: 数值类型列名列表，默认为['Amount']
        classify_type: 分类类型列名列表，默认为['Payment Format', 'Currency']
        merge_del_cols: 需要合并的列名列表，默认为['From','To']
        new_col_name: 合并后的新列名，默认为'key'

        返回:
        df_final: 合并所有窗口结果的DataFrame

        功能说明:
        1. 使用滚动窗口按天处理交易数据
        2. 对每个窗口的数据进行聚合统计（调用data_agg方法）
        3. 将多个标识列合并为一个统一的关键列（调用cols_more2one方法）
        4. 将所有窗口的结果合并为一个最终DataFrame返回
        """

        # 创建空的DataFrame用于存储所有窗口的结果
        df_final = pd.DataFrame()

        print(f"开始按天滚动窗口聚合，时间列: {col_time}, 间隔: {interval}, 窗口长度: {win_len}")
        # print(f"分组标识: {identifys}, 数值列: {num_type}, 分类列: {classify_type}")

        window_count = 0

        # 一次提取一天的数据，滚动窗口处理
        for s, e, df_sub in DataDeal.rolling_windows(
            df=df,
            col_time=col_time,
            interval=interval,
            win_len=win_len):

            window_count += 1
            print(f'\n处理第 {window_count} 个窗口: {s} ~ {e}，记录数 {len(df_sub)}')

            if len(df_sub) == 0:
                # print(f"  窗口 {s} ~ {e} 没有数据，跳过")
                continue

            # 1. 对当前窗口数据进行聚合统计
            # print(f"  开始聚合统计...")
            df_agg_by_day = cls.data_agg(df_sub,
                    identifys=identifys,
                    num_type=num_type,
                    classify_type=classify_type,
                    stat_lable=stat_lable)

            # print(f"  聚合完成，结果形状: {df_agg_by_day.shape}")

            # 2. 将多个标识列合并为一个关键列
            if merge_del_cols and all(col in df_agg_by_day.columns for col in merge_del_cols):
                # print(f"  合并列 {merge_del_cols} 为新列 '{new_col_name}'...")
                df_agg_by_day = cls.cols_more2one(df_agg_by_day,
                                        cols=merge_del_cols,
                                        new_col_name=new_col_name)
                # print(f"  列合并完成，结果形状: {df_agg_by_day.shape}")
            else:
                print(f"  跳过列合并，检查列是否存在: {merge_del_cols}")
                print(f"  DataFrame列: {df_agg_by_day.columns.tolist()}")

            # 3. 添加窗口时间信息
            df_agg_by_day['window_start'] = s
            df_agg_by_day['window_end'] = e
            df_agg_by_day['window_seq'] = window_count

            # 4. 将当前窗口结果合并到最终结果中
            if df_final.empty:
                df_final = df_agg_by_day.copy()
                # print(f"  初始化最终结果DataFrame，形状: {df_final.shape}")
            else:
                # 使用concat合并，保持列对齐
                df_final = pd.concat([df_final, df_agg_by_day], ignore_index=True)
                # print(f"  合并当前窗口结果，最终形状: {df_final.shape}")

            # 可选：记录详细信息（如果需要调试）
            # pc.lg(f"窗口 {s} ~ {e} 聚合完成，结果形状: {df_agg_by_day.shape}")
            # pc.lg(f"窗口 {s} ~ {e} 聚合结果示例:\n{df_agg_by_day[:3]}")

        print(f"\n所有窗口处理完成，共处理 {window_count} 个窗口")
        print(f"最终结果形状: {df_final.shape}")

        if not df_final.empty:
            print(f"最终结果列: {df_final.columns.tolist()}")
            print(f"窗口序列范围: {df_final['window_seq'].min()} ~ {df_final['window_seq'].max()}")

            # 将窗口信息列移到最后
            info_cols = ['window_start', 'window_end', 'window_seq']
            other_cols = [col for col in df_final.columns if col not in info_cols]
            df_final = df_final[other_cols]

            # 将df_final中的NaN值替换为0
            print(f"开始处理df_final中的NaN值...")
            nan_before = df_final.isnull().sum().sum()
            print(f"处理前NaN值总数: {nan_before}")

            if nan_before > 0:
                # 显示每列的NaN值数量
                nan_by_col = df_final.isnull().sum()
                cols_with_nan = nan_by_col[nan_by_col > 0]
                if len(cols_with_nan) > 0:
                    # print("各列NaN值数量:")
                    for col, count in cols_with_nan.items():
                        print(f"  {col}: {count}")

                # 替换NaN值为0
                df_final = df_final.fillna(0)

                nan_after = df_final.isnull().sum().sum()
                print(f"处理后NaN值总数: {nan_after}")
                print("✓ 所有NaN值已替换为0")
            else:
                print("✓ df_final中没有NaN值")

        return df_final



        
        
        @classmethod
        def data_type_change(cls,df,num_type=None,classify_type=None,date_type=None):
            """
            转换DataFrame中指定列的数据类型；通常是指定num_type、date_type,将剩下的列转换成classify_type

            该方法用于将DataFrame中的列转换为指定的数据类型，支持数值型、分类型和日期型列的转换。
            主要用于数据预处理阶段，确保数据具有正确的类型以便后续分析。

            Args:
                df (pd.DataFrame): 输入的数据表
                num_type (list): 需要转换为数值型的列名列表，默认为None（不转换）
                classify_type (list): 需要转换为分类型的列名列表，默认为None（不转换）
                date_type (list): 需要转换为日期型的列名列表，默认为None（不转换）

            Returns:
                pd.DataFrame: 数据类型转换后的数据表

            使用示例：
                # 转换指定列的数据类型
                df_converted = Data2Feature.data_type_change(
                    df,
                    num_type=['age', 'salary'],      # 转换为数值型
                    classify_type=['gender', 'city'], # 转换为分类型
                    date_type=['create_time', 'update_time']  # 转换为日期型
                )

            注意事项：
            - 转换失败的列会保持原有数据类型
            - 日期转换支持常见的日期格式
            - 数值转换会将无法解析的值设为NaN
            """
            df = DataDeal.data_type_change(df,num_type=num_type,classify_type=classify_type,date_type=date_type)
            return df
            
        @classmethod
        def data_filter(cls, df, data_dict={}, type='remove'):
            """
            根据指定条件过滤DataFrame数据

            参数:
            df (pd.DataFrame): 要过滤的DataFrame
            data_dict (dict): 过滤条件字典，key为列名，value为列的值列表(list类型)
            type (str): 过滤类型，可选值为'remove'或'in'
                    - remove: 删除列中值为value的行
                    - in: 保留列中值存在于value列表中的行

            返回:
            pd.DataFrame: 过滤后的DataFrame

            示例:
            # 删除color列中值为'red'或'blue'的行
            df_filtered = Data2Feature.data_filter(df, {'color': ['red', 'blue']}, 'remove')

            # 只保留name列中值为'Alice'或'Bob'的行
            df_filtered = Data2Feature.data_filter(df, {'name': ['Alice', 'Bob']}, 'in')
            """
            import pandas as pd

            # 参数验证
            if df is None or df.empty:
                cls.pc.lg("警告: 输入DataFrame为空")
                return df.copy()

            if not data_dict:
                cls.pc.lg("警告: data_dict为空，返回原始DataFrame")
                return df.copy()

            if type not in ['remove', 'in']:
                raise ValueError("type参数必须是'remove'或'in'")

            # 创建结果DataFrame的副本
            result_df = df.copy()
            original_count = len(result_df)

            cls.pc.lg(f"开始数据过滤，原始行数: {original_count}")
            cls.pc.lg(f"过滤类型: {type}")
            cls.pc.lg(f"过滤条件: {data_dict}")

            # 对每个列应用过滤条件
            for column, values in data_dict.items():
                # 检查列是否存在
                if column not in result_df.columns:
                    cls.pc.lg(f"警告: 列 '{column}' 不存在于DataFrame中，跳过此条件")
                    continue

                # 检查values是否为列表
                if not isinstance(values, (list, tuple, set)):
                    cls.pc.lg(f"警告: 列 '{column}' 的值不是列表类型，转换为列表")
                    values = [values]

                # 记录过滤前的行数
                before_count = len(result_df)

                # 根据过滤类型应用条件
                if type == 'remove':
                    # 删除列中值在values列表中的行
                    mask = ~result_df[column].isin(values)
                    result_df = result_df[mask]
                    removed_count = before_count - len(result_df)
                    cls.pc.lg(f"列 '{column}': 删除了 {removed_count} 行 (值在 {values} 中)")

                elif type == 'in':
                    # 只保留列中值在values列表中的行
                    mask = result_df[column].isin(values)
                    result_df = result_df[mask]
                    kept_count = len(result_df)
                    removed_count = before_count - kept_count
                    cls.pc.lg(f"列 '{column}': 保留了 {kept_count} 行 (值在 {values} 中)，删除了 {removed_count} 行")

            # 统计最终结果
            final_count = len(result_df)
            total_removed = original_count - final_count

            cls.pc.lg(f"过滤完成:")
            cls.pc.lg(f"  原始行数: {original_count}")
            cls.pc.lg(f"  最终行数: {final_count}")
            cls.pc.lg(f"  总计删除: {total_removed} 行")
            cls.pc.lg(f"  删除比例: {total_removed/original_count*100:.2f}%" if original_count > 0 else "  删除比例: 0%")

            return result_df 
            
        @classmethod
        def data_make(cls,
                    data_type={'numf':'float32','num':'int32', "date":"yyyy-mm-dd",'classify':'string'},
                    num_rows=100):
            """
            根据data_type随机生成数据

            参数:
            data_type (dict): 数据类型配置字典
                - numf: 浮点数类型，默认'float32'
                - num: 整数类型，默认'int32'
                - date: 日期类型，默认'yyyy-mm-dd'
                - classify: 分类类型，默认'string'
            num_rows (int): 生成的行数，默认100行

            返回:
            pd.DataFrame: 生成的随机数据DataFrame

            示例:
            # 生成默认配置的测试数据
            df = Data2Feature.data_make()

            # 生成指定行数的数据
            df = Data2Feature.data_make(num_rows=1000)

            # 自定义数据类型配置
            df = Data2Feature.data_make({
                'numf': 'float64',
                'num': 'int16',
                'date': 'dd/mm/yyyy',
                'classify': 'category'
            }, num_rows=500)
            """
            import pandas as pd
            import numpy as np
            import random
            from datetime import datetime, timedelta
            import string

            cls.pc.lg(f"开始生成随机数据，行数: {num_rows}")
            cls.pc.lg(f"数据类型配置: {data_type}")

            # 生成数据
            data = {}

            # 生成浮点数列
            if 'numf' in data_type:
                float_col = np.random.normal(0, 1, num_rows).astype(data_type['numf'])
                data['float_col'] = float_col
                cls.pc.lg(f"生成浮点数列 'float_col'，类型: {data_type['numf']}")

            # 生成整数列
            if 'num' in data_type:
                int_col = np.random.randint(0, 1000, num_rows).astype(data_type['num'])
                data['int_col'] = int_col
                cls.pc.lg(f"生成整数列 'int_col'，类型: {data_type['num']}")

            # 生成日期列
            if 'date' in data_type:
                date_format = data_type['date']
                start_date = datetime(2020, 1, 1)
                end_date = datetime(2024, 12, 31)

                if date_format == 'yyyy-mm-dd':
                    date_col = [start_date + timedelta(days=random.randint(0, (end_date - start_date).days))
                            for _ in range(num_rows)]
                    date_col = [date.strftime('%Y-%m-%d') for date in date_col]
                elif date_format == 'dd/mm/yyyy':
                    date_col = [start_date + timedelta(days=random.randint(0, (end_date - start_date).days))
                            for _ in range(num_rows)]
                    date_col = [date.strftime('%d/%m/%Y') for date in date_col]
                elif date_format == 'mm-dd-yyyy':
                    date_col = [start_date + timedelta(days=random.randint(0, (end_date - start_date).days))
                            for _ in range(num_rows)]
                    date_col = [date.strftime('%m-%d-%Y') for date in date_col]
                else:
                    # 默认格式
                    date_col = [start_date + timedelta(days=random.randint(0, (end_date - start_date).days))
                            for _ in range(num_rows)]
                    date_col = [date.strftime('%Y-%m-%d') for date in date_col]

                data['date_col'] = date_col
                cls.pc.lg(f"生成日期列 'date_col'，格式: {date_format}")

            # 生成分类列
            if 'classify' in data_type:
                classify_type = data_type['classify']

                # 生成一些随机的分类值
                categories = [
                    ['Category_A', 'Category_B', 'Category_C', 'Category_D', 'Category_E'],
                    ['Red', 'Green', 'Blue', 'Yellow', 'Black'],
                    ['Active', 'Inactive', 'Pending', 'Completed'],
                    ['Type_1', 'Type_2', 'Type_3']
                ]

                for i, category_list in enumerate(categories):
                    if i >= 2:  # 最多生成4个分类列
                        break

                    col_name = f'category_col_{i+1}'
                    classify_data = [random.choice(category_list) for _ in range(num_rows)]

                    if classify_type == 'category':
                        # 转换为pandas category类型
                        data[col_name] = pd.Categorical(classify_data)
                    else:
                        # 保持为字符串类型
                        data[col_name] = classify_data

                    cls.pc.lg(f"生成分类列 '{col_name}'，类型: {classify_type}")

            # 生成额外的混合数据列
            # ID列
            data['id'] = range(1, num_rows + 1)
            cls.pc.lg("生成ID列 'id'")

            # 随机文本列
            text_data = []
            for _ in range(num_rows):
                word_length = random.randint(3, 10)
                word = ''.join(random.choices(string.ascii_lowercase, k=word_length))
                text_data.append(word)
            data['text_col'] = text_data
            cls.pc.lg("生成文本列 'text_col'")

            # 布尔列
            bool_data = [random.choice([True, False]) for _ in range(num_rows)]
            data['bool_col'] = bool_data
            cls.pc.lg("生成布尔列 'bool_col'")

            # 创建DataFrame
            df = pd.DataFrame(data)

            cls.pc.lg(f"数据生成完成，DataFrame形状: {df.shape}")
            cls.pc.lg(f"生成的列: {list(df.columns)}")

            # 显示数据类型信息
            cls.pc.lg("数据类型:")
            for col, dtype in df.dtypes.items():
                cls.pc.lg(f"  {col}: {dtype}")

            # 显示前几行样本
            cls.pc.lg("数据样本 (前3行):")
            cls.pc.lg(df.head(3).to_string())

            return df 
            
        @classmethod
        def data_sample_cat(cls, df, y=None, n=10, indetify=[], cat_cols=[], time_col='time8'):
            """
            连续时间采样，按类别采样

            参数:
            df (pd.DataFrame): 输入的DataFrame
            y: 目标变量（暂未使用，保留参数）
            n (int): 每个类别采样的数据行数，默认为10
            indetify (list): 标识列列表，用于去重
            cat_cols (list): 类别列列表，需要按这些列的类别进行采样
            time_col (str): 时间列名，默认为'time8'

            返回:
            pd.DataFrame: 采样后的数据

            主要逻辑:
            1. 循环cat_cols类别列，每个类别列进行采样：
            1.1 获取该类别列的所有数据不重复的类别
            1.2 循环一个列中所有不重复的类别，针对每个不重复的类别：
                1.2.1 取该类别所有数据，按时间降序排序，取前n行数据
            2. 合并循环的数据，然后按indetify+time_col作为主键进行去重，返回合并后的数据

            示例:
            # 按Payment Format列进行类别采样，每个类别取最新的10条记录
            df_sampled = Data2Feature.data_sample_cat(
                df=df,
                y=None,
                n=10,
                indetify=['From'],
                cat_cols=['Payment Format'],
                time_col='time8'
            )
            """
            import pandas as pd

            # 参数验证
            if df is None or df.empty:
                cls.pc.lg("警告: 输入DataFrame为空")
                return pd.DataFrame()

            if not cat_cols:
                cls.pc.lg("警告: cat_cols为空，返回空DataFrame")
                return pd.DataFrame()

            if time_col not in df.columns:
                cls.pc.lg(f"警告: 时间列 '{time_col}' 不存在，返回空DataFrame")
                return pd.DataFrame()

            cls.pc.lg(f"开始按类别采样数据")
            cls.pc.lg(f"原始数据形状: {df.shape}")
            cls.pc.lg(f"采样数量: {n} 行/类别")
            cls.pc.lg(f"类别列: {cat_cols}")
            cls.pc.lg(f"标识列: {indetify}")
            cls.pc.lg(f"时间列: {time_col}")

            # 确保时间列是datetime类型以便排序
            df_sample = df.copy()
            if not pd.api.types.is_datetime64_any_dtype(df_sample[time_col]):
                try:
                    df_sample[time_col] = pd.to_datetime(df_sample[time_col])
                    cls.pc.lg(f"将时间列 '{time_col}' 转换为datetime类型")
                except Exception as e:
                    cls.pc.lg(f"警告: 无法转换时间列 '{time_col}' 为datetime类型: {e}")
                    cls.pc.lg("尝试使用字符串排序")

            # 存储所有采样结果
            all_samples = []

            # 1. 循环cat_cols类别列，每个类别列进行采样
            for cat_col in cat_cols:
                if cat_col not in df_sample.columns:
                    cls.pc.lg(f"警告: 类别列 '{cat_col}' 不存在，跳过")
                    continue

                cls.pc.lg(f"\n处理类别列: {cat_col}")

                # 1.1 获取该类别列的所有数据不重复的类别
                unique_categories = df_sample[cat_col].dropna().unique()
                cls.pc.lg(f"发现 {len(unique_categories)} 个不重复类别: {unique_categories}")

                # 1.2 循环一个列中所有不重复的类别，针对每个不重复的类别进行采样
                for category in unique_categories:
                    cls.pc.lg(f"  处理类别 '{category}':")

                    # 筛选该类别的所有数据
                    category_data = df_sample[df_sample[cat_col] == category].copy()
                    cls.pc.lg(f"    类别 '{category}' 共有 {len(category_data)} 条记录")

                    if len(category_data) == 0:
                        cls.pc.lg(f"    跳过空类别")
                        continue

                    # 1.2.1 取该类别所有数据，按时间降序排序，取前n行数据
                    try:
                        # 按时间降序排序
                        category_sorted = category_data.sort_values(by=time_col, ascending=False)

                        # 取前n行
                        sample_data = category_sorted.head(n)
                        cls.pc.lg(f"    采样了 {len(sample_data)} 条记录")

                        # 添加采样信息
                        sample_data = sample_data.copy()
                        sample_data['_sample_cat_col'] = cat_col
                        sample_data['_sample_category'] = category
                        sample_data['_sample_count'] = len(sample_data)

                        all_samples.append(sample_data)

                    except Exception as e:
                        cls.pc.lg(f"    错误: 处理类别 '{category}' 时出错: {e}")
                        continue

            # 2. 合并循环的数据
            if not all_samples:
                cls.pc.lg("警告: 没有采样到任何数据")
                return pd.DataFrame()

            cls.pc.lg(f"\n合并 {len(all_samples)} 个采样结果")
            merged_data = pd.concat(all_samples, ignore_index=True)
            cls.pc.lg(f"合并后数据形状: {merged_data.shape}")

            # 按indetify+time_col作为主键进行去重
            if indetify:
                dedup_cols = indetify + [time_col]
                # 检查去重列是否存在
                missing_cols = [col for col in dedup_cols if col not in merged_data.columns]
                if missing_cols:
                    cls.pc.lg(f"警告: 去重列中缺少以下列: {missing_cols}")
                    cls.pc.lg("跳过去重步骤")
                else:
                    # 去重前记录数量
                    before_dedup = len(merged_data)

                    # 按指定列去重，保留第一次出现的记录（即最新的记录）
                    dedup_data = merged_data.drop_duplicates(subset=dedup_cols, keep='first')

                    # 去重后记录数量
                    after_dedup = len(dedup_data)
                    dedup_count = before_dedup - after_dedup

                    cls.pc.lg(f"按列 {dedup_cols} 去重:")
                    cls.pc.lg(f"  去重前: {before_dedup} 条记录")
                    cls.pc.lg(f"  去重后: {after_dedup} 条记录")
                    cls.pc.lg(f"  删除重复: {dedup_count} 条记录")

                    merged_data = dedup_data
            else:
                cls.pc.lg("未指定标识列，跳过去重步骤")

            # 移除临时添加的采样信息列
            temp_cols = ['_sample_cat_col', '_sample_category', '_sample_count']
            existing_temp_cols = [col for col in temp_cols if col in merged_data.columns]
            if existing_temp_cols:
                merged_data = merged_data.drop(columns=existing_temp_cols)
                cls.pc.lg(f"移除临时列: {existing_temp_cols}")

            # 最终统计
            cls.pc.lg(f"\n采样完成:")
            cls.pc.lg(f"  最终数据形状: {merged_data.shape}")
            cls.pc.lg(f"  处理的类别列: {[col for col in cat_cols if col in df.columns]}")

            # 显示每个原始类别列的采样统计
            for cat_col in cat_cols:
                if cat_col in merged_data.columns:
                    unique_cats = merged_data[cat_col].nunique()
                    cls.pc.lg(f"  {cat_col}: {unique_cats} 个类别")

            return merged_data
            
        @classmethod
        def show_col_type(cls, df, numeric_only=False, non_numeric_only=False):
            """
            显示DataFrame列的数据类型

            Args:
                df (pd.DataFrame): 输入的数据表
                numeric_only (bool): 是否只显示数值列，默认为False
                non_numeric_only (bool): 是否只显示非数值列，默认为False

            Note:
                如果numeric_only和non_numeric_only都为False，显示所有列类型
                如果numeric_only为True，只显示数值列类型
                如果non_numeric_only为True，只显示非数值列类型
            """
            if numeric_only and non_numeric_only:
                print("警告：numeric_only和non_numeric_only不能同时为True，将显示所有列类型")
                print(df.dtypes)
            elif numeric_only:
                numeric_cols = df.select_dtypes(include=['number']).columns
                if len(numeric_cols) > 0:
                    print("数值列类型：")
                    print(df[numeric_cols].dtypes)
                else:
                    print("没有数值列")
            elif non_numeric_only:
                non_numeric_cols = df.select_dtypes(exclude=['number']).columns
                if len(non_numeric_cols) > 0:
                    print("非数值列类型：")
                    print(df[non_numeric_cols].dtypes)
                else:
                    print("没有非数值列")
            else:
                print(df.dtypes)
            
        @classmethod
        def show_null_count(cls,df):
            print(df.isnull().sum())
            
        @classmethod
        def show_one_row(cls, df=None, row_idx=0, n=10, show_all=False):
            """
            显示DataFrame中指定行的前n个字段

            参数:
            df: DataFrame对象，如果为None则使用全局的df_final_result
            row_idx: 行索引，默认为0（第一行）
            n: 显示的字段数量，默认为10个
            show_all: 是否显示所有字段，如果为True则忽略n参数

            功能:
            1. 显示指定行的前n个字段的键值对
            2. 支持显示DataFrame的基本信息
            3. 提供字段计数和总览信息
            4. 支持显示所有字段或限制显示数量
            """
            import pandas as pd

            # 检查DataFrame是否为空
            if df is None or df.empty:
                cls.pc.lg("DataFrame为空，没有数据可显示")
                return

            # 检查行索引是否有效
            if row_idx < 0 or row_idx >= len(df):
                cls.pc.lg(f"错误: 行索引 {row_idx} 超出范围 [0, {len(df)-1}]")
                return

            # 显示DataFrame基本信息
            cls.pc.lg(f"DataFrame形状: {df.shape}")
            cls.pc.lg(f"显示第 {row_idx} 行（索引: {df.index[row_idx]}）")
            cls.pc.lg(f"总字段数: {len(df.columns)}")

            if show_all:
                cls.pc.lg(f"显示所有字段:")
                display_count = len(df.columns)
            else:
                cls.pc.lg(f"显示前 {n} 个字段:")
                display_count = min(n, len(df.columns))

            cls.pc.lg("-" * 60)

            # 显示指定行的字段
            count = 0
            for k, v in df.iloc[row_idx].items():
                # 格式化显示
                if pd.isna(v):
                    value_str = "NaN"
                elif isinstance(v, float):
                    if abs(v) < 0.001:
                        value_str = f"{v:.6f}"
                    else:
                        value_str = f"{v:.3f}"
                elif isinstance(v, (int, np.integer)):
                    value_str = str(v)
                else:
                    value_str = str(v)
                    # 限制字符串长度
                    if len(value_str) > 50:
                        value_str = value_str[:47] + "..."

                cls.pc.lg(f"{k:30}: {value_str}")
                count += 1

                # 如果不显示全部且达到指定数量，则停止
                if not show_all and count >= display_count:
                    break

            cls.pc.lg("-" * 60)

            # 如果还有未显示的字段，提示用户
            if not show_all and len(df.columns) > n:
                remaining = len(df.columns) - n
                cls.pc.lg(f"还有 {remaining} 个字段未显示，使用 show_all=True 可显示全部")

                
        @classmethod
        def show_unique_count(cls,df):
            print(df.nunique())
            

        @classmethod
        def show_describe(cls,df,cols=[],show_category=False):
            """
            显示数据的描述统计信息

            Args:
                df (pd.DataFrame): 输入的数据表
                cols (list): 指定要显示的列，如果为空或None则显示所有列
                show_category (bool): 显示类别类型的信息还是数字类型的信息，默认为False(显示数字类型)
            """
            # 如果cols不为空或None，则只显示指定列
            if cols and len(cols) > 0:
                df_display = df[cols]
            else:
                df_display = df

            if show_category:
                # 显示类别列的描述统计
                print("=== 类别列描述统计 ===")
                try:
                    # 使用_categorical_function_not_num_date方法识别类别列
                    categorical_cols = cls._categorical_not_num_date(df_display)

                    if len(categorical_cols) > 0:
                        # 对每个类别列显示统计信息
                        for col in categorical_cols:
                            if col in df_display.columns:
                                print(f"\n列 '{col}' 的统计信息:")
                                print(f"  唯一值数量: {df_display[col].nunique()}")
                                print(f"  缺失值数量: {df_display[col].isnull().sum()}")
                                print(f"  前10个最频繁的值:")
                                print(df_display[col].value_counts().head(10))
                    else:
                        print("没有类别列")
                except Exception as e:
                    print(f"显示类别列统计时出错: {e}")
            else:
                # 显示数值列的描述统计
                print("=== 数值列描述统计 ===")
                try:
                    # 显示数值列的统计信息
                    numeric_cols = df_display.select_dtypes(include=['number']).columns
                    if len(numeric_cols) > 0:
                        print(df_display[numeric_cols].describe())
                    else:
                        print("没有数值列")
                except Exception as e:
                    print(f"显示数值列统计时出错: {e}")

            # 显示数据基本信息
            print(f"\n=== 数据基本信息 ===")
            print(f"总行数: {len(df_display)}")
            print(f"总列数: {len(df_display.columns)}")
            print(f"缺失值总数: {df_display.isnull().sum().sum()}")
            print(f"内存使用: {df_display.memory_usage(deep=True).sum() / 1024 / 1024:.2f} MB") 
            
        @classmethod
        def tonum_col2index(cls,df, identity=[], classify_type=[], classify_type2=[],
                    dict_file="dict_file.dict", is_pre=False,
                    word2id=None, start_index=1):
            """
            将分类列转换为数值索引，支持训练和预测模式

            该方法将DataFrame中的分类特征列转换为数值索引，便于机器学习模型处理。
            支持单列分类和多列组合分类的转换，并能保存和加载编码字典。

            Args:
                df (pd.DataFrame): 输入的数据表
                identity (list): 标识列列表，不参与编码，默认为空
                classify_type (list): 需要编码的单列分类列名列表，默认为空
                classify_type2 (list): 需要编码的多列组合分类列列表，每个元素为列名列表，默认为空
                dict_file (str): 编码字典保存路径，默认为"dict_file.dict"
                is_pre (bool): 是否为预测模式，默认为False（训练模式）
                word2id (dict): 预定义的词汇到ID映射字典，默认为None
                start_index (int): 索引起始值，默认为1

            Returns:
                pd.DataFrame: 编码后的数据表，分类列已转换为数值索引

            Raises:
                ValueError: 当classify_type2中的元素不是列表类型时抛出

            处理逻辑：
            1. 参数验证：检查classify_type2参数格式，确保每个元素都是列表
            2. 调用底层DataDeal.col2index方法进行实际的编码转换
            3. 支持训练模式和预测模式的不同处理逻辑

            参数说明：
            - classify_type: 单列分类，如["性别", "学历"]
            - classify_type2: 多列组合分类，如 [["省份", "城市"], ["部门", "职位"]]
            - is_pre=True时为预测模式，会加载已有的编码字典
            - is_pre=False时为训练模式，会创建新的编码字典并保存
            """
            # 检验classify_type2参数，如果不为空或None，则其元素必须为列表
            if classify_type2 is not None and classify_type2:
                for i, item in enumerate(classify_type2):
                    if not isinstance(item, list):
                        raise ValueError(f"classify_type2的第{i+1}个元素必须是列表，但得到了{type(item)}: {item}")

            # 确保classify_type2为列表类型（避免None值传递给底层方法）
            classify_type2 = classify_type2 or []

            df = DataDeal.col2index(df,
                    identity=identity, classify_type=classify_type, classify_type2=classify_type2,
                    dict_file=dict_file, is_pre=is_pre,
                    word2id=word2id, start_index=start_index)
            return df  
        
        @classmethod
        def tonum_label_encoding(cls, df, identity=[], classify_type=[], file_path=None,
                                is_pre=False, force_rewrite=False):
            """
            对分类列进行LabelEncoder编码，支持训练和预测模式

            Args:
                df (pd.DataFrame): 输入的数据表
                identity (list): 标识列列表，不参与编码，默认为空
                classify_type (list): 需要编码的分类列名列表，如果为空或None则自动推断
                file_path (str): 编码字典保存路径，如果为None则不保存/加载字典
                is_pre (bool): 是否为预测模式，默认为False（训练模式）
                force_rewrite (bool): 是否强制重新训练编码器，默认为False

            Returns:
                pd.DataFrame: 编码后的数据表

            处理逻辑：
            1. 训练模式(is_pre=False)：
            - 如果编码字典文件存在且force_rewrite=False，加载字典并应用
            - 否则重新训练编码器，保存字典并应用

            2. 预测模式(is_pre=True)：
            - 如果force_rewrite=True，则重新训练编码器（忽略is_pre）
            - 否则只加载并应用现有编码器，不重新训练

            3. 如果file_path为None，始终进行训练但不保存字典

            4. 如果classify_type为空或None，自动推断类别列：
            - 选择df中所有非数字列作为类别列
            - 排除identity中指定的标识列
            """
            # 自动推断类别列（如果classify_type为空）
            if not classify_type:
                # 获取所有非数字列
                non_numeric_cols = df.select_dtypes(exclude=['number']).columns.tolist()

                # 排除identity中的列
                identity_set = set(identity) if identity else set()
                classify_type = [col for col in non_numeric_cols if col not in identity_set]

                if classify_type:
                    print(f"自动推断类别列：{classify_type}")
                else:
                    print("没有找到合适的类别列进行编码")
                    return df

            # 检查分类列是否存在于DataFrame中
            valid_cols = [col for col in classify_type if col in df.columns]
            if len(valid_cols) != len(classify_type):
                missing_cols = set(classify_type) - set(valid_cols)
                print(f"警告：以下列不存在于DataFrame中：{missing_cols}")
                classify_type = valid_cols
                if not classify_type:
                    return df

            # 根据模式决定处理逻辑
            should_load = (file_path and os.path.exists(file_path) and
                        not force_rewrite and is_pre)

            if should_load:
                # 预测模式：加载现有编码字典
                try:
                    label_encoding_dict = pkl_load(file_path)
                    cls._apply_existing_encoders(df, classify_type, label_encoding_dict)
                    print("预测模式：已加载现有编码字典")
                except Exception as e:
                    print(f"加载编码字典失败，重新训练编码器：{e}")
                    force_rewrite = True  # 设置为重新训练

            if force_rewrite or not should_load:
                # 训练模式或强制重写：训练新的编码器
                mode = "强制重写" if force_rewrite else ("预测模式（重训练）" if is_pre else "训练模式")
                print(f"{mode}：训练新的编码器")

                label_encoding_dict = cls._train_new_encoders(df, classify_type)

                # 保存编码字典（如果指定了文件路径）
                if file_path:
                    try:
                        pkl_save(label_encoding_dict, file_path=file_path)
                        print(f"编码字典已保存至：{file_path}")
                    except Exception as e:
                        print(f"保存编码字典失败：{e}")

            return df



    
    
        @classmethod
        def norm_min_max_scaler(cls, X, num_type=[], 
                                model_path=f"min_max_scaler.pkl", 
                                is_train=True):
            if is_train:
                df = DataDeal.min_max_scaler(X, 
                                num_type=num_type, 
                                model_path=model_path, 
                                reuse=True, 
                                col_sort=True, 
                                force_rewrite=True)
            else:
                df = DataDeal.min_max_scaler(X, 
                                num_type=num_type, 
                                model_path=model_path, 
                                reuse=True, 
                                col_sort=True)
            return df  

        @classmethod
        def getXy(cls,
                data_path, heads, str_identity,
                alg_type, model_ai_dir, model_num, file_num,
                is_train, label_name, pc:ParamConfig, drop_columns,
                is_categorical_func_type=None, date_type=None, 
                sep='~',classify_type2 = [[]],bool_type = []):
            df = cls.read_csv(data_path, sep=sep, heads=heads)
            
            pass 
        
        @classmethod
        def processing(cls, 
                    df, str_identity,
                    alg_type, model_ai_dir, model_num, file_num,
                    is_train, label_name, pc:ParamConfig, drop_columns,
                    date_type, col_types):
            """
            通用数据处理管道

            Args:
                data_path (str): 数据文件路径
                model_title (str): 模型标题
                str_identity (str): 标识列
                alg_type (str): 算法类型
                model_ai_dir (str): 模型保存目录
                model_num (int): 模型编号
                file_num (int): 文件编号
                is_train (bool): 是否为训练
                label_name (str): 标签列名
                pc (ParamConfig): 参数配置对象
                drop_columns (list): 要删除的列
                is_categorical_func_type (str): 分类列判断函数类型，'general'或'tra'
                date_type (list, optional): 日期类型列列表
                sep (str): 分隔符，默认为'~'

            Returns:
                tuple: (处理后的DataFrame, 标签列, 参数配置对象)
            """
    
            # 4. 分析数值列
            num_small = cls._analyze_numeric_columns(df, pc)

            # 5. 设置参数配置
            cls._setup_param_config(pc, str_identity, col_types, num_small, alg_type,
                                model_ai_dir, model_num, file_num, is_train,
                                label_name, drop_columns, date_type)

            # 6. 记录数据信息
            cls._log_data_info(pc, num_small)

            # 7. 处理数据
            df_processed = cls._process_data_with_deal_dl(df, pc)

            return df_processed, pc
        
        @classmethod
        def deal(cls, 
                    data_path, model_title, str_identity,
                    alg_type, model_ai_dir, model_num, file_num,
                    is_train, label_name, pc:ParamConfig, drop_columns,
                    is_categorical_func_type=None, date_type=None, 
                    sep='~',classify_type2 = [[]],bool_type = []):
            pass 
            
    
class DataToFeature:
    """
    数据处理类 - 封装数据训练和交易处理的相关方法

    提供统一的数据处理接口，支持通用数据处理和交易特定数据处理
    """

    def __init__(self,df = None,y=None,col_types=None):
        """初始化数据处理类"""
        self.df = df 
        self.y = y
        self.col_types = col_types
        self.cat_func = None 

    def _get_usecols(self, model_title=None, sep='~'):
        """
        根据模型标题获取要使用的列

        Args:
            model_title (str): 模型标题，'all'表示使用所有列，否则按'~'分割

        Returns:
            list or None: 要使用的列列表，None表示使用所有列
        """
        if model_title == 'all':
            return None
        else:
            return model_title.split(sep)

    def _categorical_function_reg(self):
        """
        创建通用的分类列判断函数,通过正则匹配

        Returns:
            function: 分类列判断函数
        """
        def is_categorical(col: str) -> bool:
            return col.lower().startswith(('is_', 'has_', 'with_'))
        return is_categorical
    
    def set_categorical_function(self,cat_func):
        """
        创建通用的分类列判断函数,通过正则匹配

        Returns:
            function: 分类列判断函数
        """
        self.cat_func = cat_func
 

    def _categorical_function_in(self,cls_cols=[]):
        """
        指定列创建分类列判断函数,不分区大小写

        Returns:
            function: 分类列判断函数
        """
        def is_categorical(col: str) -> bool:
            cls_cols2 = [col.lower() for col in cls_cols]
            return col.lower() in cls_cols2
        return is_categorical
    
    def _categorical_function_not_num_date(self,df,num_type=[],date_type=[]):
        """
        创建分类列判断函数，判断逻辑为排除数值列和日期列

        如果num_type为空，则选择pandas数表df中类型为number的列，
        如果date_type为空或None，则自动推断df中日期类型的列作为日期列，
        同时排除类型为日期的列以及date_type中指定的列

        Args:
            df (pd.DataFrame): 输入的数据表
            num_type (list): 指定的数值列列表，如果为空则自动推断
            date_type (list): 指定的日期列列表，如果为空则自动推断

        Returns:
            function: 分类列判断函数
        """
        # 如果num_type为空，自动推断数值列
        if num_type is None or len(num_type) == 0:
            num_type = df.select_dtypes('number').columns.tolist()

        # 如果date_type为空或None，自动推断日期列
        if date_type is None or len(date_type) == 0:
            # 使用pd.api.types.is_datetime64_any_dtype自动推断日期列
            date_type = [col for col in df.columns
                        if pd.api.types.is_datetime64_any_dtype(df[col])]

        # 获取所有列名
        col_all = df.columns.tolist()

        # 排除数值列和指定的日期列
        exclude_cols = set(num_type) | set(date_type)
        categorical_cols = list(set(col_all) - exclude_cols)

        # 创建分类列判断函数
        def is_categorical(col: str) -> bool:
            return col in categorical_cols

        return is_categorical
    

    def _load_and_classify_data(self, 
                data_path, label_name, str_identity, is_train, 
                usecols, drop_columns, 
                is_categorical_func, sep='~',date_type=[],bool_type = []):
        """
        加载数据并进行分类的通用方法

        Args:
            data_path (str): 数据文件路径
            label_name (str): 标签列名
            str_identity (str): 标识列
            is_train (bool): 是否为训练数据
            usecols (list): 要使用的列
            drop_columns (list): 要删除的列
            is_categorical_func (function): 分类列判断函数
            sep (str): 分隔符，默认为'~'

        Returns:
            tuple: (DataFrame, label列, 列类型字典)
        """
        df, y, col_types = DataDeal.getXy(data_path, label_name,
                                    identity_cols=str_identity, sep=sep,
                                    is_train=is_train, usecols=usecols,
                                    drop_columns=drop_columns,
                                    dtype_mapping=None,
                                    is_categorical_func=is_categorical_func,
                                    date_type=date_type,
                                    bool_type=bool_type)
        return df, y, col_types

    def _analyze_numeric_columns(self, df, pc, threshold=100):
        """
        分析数值列，找出最大值小于阈值的列

        Args:
            df (DataFrame): 数据框
            pc (ParamConfig): 参数配置对象
            threshold (int): 阈值，默认为100

        Returns:
            list: 小于阈值的列名列表
        """
        num_small = DataDeal.columns_by_max_value(df, condition='less', threshold=threshold)
        pc.lg(f"num_small num:{len(num_small)}")
        if len(num_small) > 0:
            DataDeal.num_describe(df[num_small], pc)
            return num_small
        else:
            return []

    def _setup_param_config(self, pc:ParamConfig, str_identity, col_types, num_small, alg_type,
                           model_ai_dir, model_num, file_num, is_train,
                           label_name, drop_columns, date_type=None,classify_type2 = [[]],bool_type = [] ):
        """
        设置参数配置对象的通用方法

        Args:
            pc (ParamConfig): 参数配置对象
            str_identity (str): 标识列
            col_types (dict): 列类型字典
            num_small (list): 小数值列列表
            alg_type (str): 算法类型
            model_ai_dir (str): 模型保存目录
            model_num (int): 模型编号
            file_num (int): 文件编号
            is_train (bool): 是否为训练
            label_name (str): 标签列名
            drop_columns (list): 要删除的列
            date_type (list, optional): 日期类型列列表
        """
        # DataDealDL.data_deal需要的12个参数
        pc.col_type.identity       = str_identity
        pc.col_type.num_type       = col_types["num_type"]
        pc.col_type.num_small      = num_small
        pc.col_type.classify_type  = col_types["classify_type"]
        pc.col_type.classify_type2 = classify_type2  #一组类别使用同一个字典
        pc.col_type.date_type      = date_type if date_type is not None else []
        pc.col_type.bool_type      = bool_type
        pc.alg_type                = alg_type
        pc.model_save_dir          = model_ai_dir
        pc.model_num               = model_num
        pc.file_num                = file_num   #第几个文件,默认1
        pc.is_train                = is_train

        #其他参数
        pc.label_name              = label_name
        pc.drop_cols               = drop_columns

    def _log_data_info(self, pc:ParamConfig, num_small):
        """
        记录数据信息的通用方法

        Args:
            pc (ParamConfig): 参数配置对象
            num_small (list): 小数值列列表
        """
        pc.lg(pc.col_type.num_type[:3])
        pc.lg(f"num_small num:{len(num_small)},num type num:{len(pc.col_type.num_type)}")
        pc.lg(pc.col_type.classify_type[:3])
        pc.lg(f"is_merge_identity:{pc.is_merge_identity}")

    def _process_data_with_deal_dl(self, df, pc:ParamConfig):
        """
        使用DataDealDL处理数据的通用方法

        Args:
            df (DataFrame): 数据框
            pc (ParamConfig): 参数配置对象

        Returns:
            DataFrame: 处理后的数据框
        """
        df_processed = DataDealDL.data_deal(df, pc)
        return df_processed
    
    

    def _processing_pipeline(self, 
                data_path, model_title, str_identity,
                alg_type, model_ai_dir, model_num, file_num,
                is_train, label_name, pc:ParamConfig, drop_columns,
                is_categorical_func_type=None, date_type=None, 
                sep='~',classify_type2 = [[]],bool_type = []):
        """
        通用数据处理管道

        Args:
            data_path (str): 数据文件路径
            model_title (str): 模型标题
            str_identity (str): 标识列
            alg_type (str): 算法类型
            model_ai_dir (str): 模型保存目录
            model_num (int): 模型编号
            file_num (int): 文件编号
            is_train (bool): 是否为训练
            label_name (str): 标签列名
            pc (ParamConfig): 参数配置对象
            drop_columns (list): 要删除的列
            is_categorical_func_type (str): 分类列判断函数类型，'general'或'tra'
            date_type (list, optional): 日期类型列列表
            sep (str): 分隔符，默认为'~'

        Returns:
            tuple: (处理后的DataFrame, 标签列, 参数配置对象)
        """
        if self.df is None:
            # 1. 获取要使用的列
            usecols = self._get_usecols(model_title)

            # 2. 创建分类列判断函数
            if is_categorical_func_type is None:
                is_categorical_func = self.cat_func
            elif is_categorical_func_type == 'general':
                is_categorical_func = self._categorical_function_reg()
            elif is_categorical_func_type == 'tra':
                is_categorical_func = self._categorical_function_in()
            else:
                raise ValueError(f"未知的is_categorical_func_type: {is_categorical_func_type}")

            # 3. 加载数据并分类
            # print("data_path:",data_path)
            df, y, col_types = self._load_and_classify_data(
                data_path, label_name, str_identity, is_train,
                usecols, drop_columns, is_categorical_func, sep, date_type, bool_type
            )
            self.df = df 
            self.y  = y 
            self.col_types = col_types
            
            self.lg(f"classify_data----------------------")
            self.lg(f"col_types['date_type'] len = {len(col_types['date_type'])}")
            self.lg(f"col_types['num_type'] len = {len(col_types['num_type'])}")
            self.lg(f"col_types['classify_type'] len = {len(col_types['classify_type'])}")
            self.lg(f"df[:3]:\n{df[:3]}")

        # 4. 分析数值列
        num_small = self._analyze_numeric_columns(self.df, pc)

        # 5. 设置参数配置
        self._setup_param_config(pc, str_identity, col_types, num_small, alg_type,
                               model_ai_dir, model_num, file_num, is_train,
                               label_name, drop_columns, date_type)

        # 6. 记录数据信息
        self._log_data_info(pc, num_small)

        # 7. 处理数据
        df_processed = self._process_data_with_deal_dl(df, pc)

        return df_processed, y, pc

    def deal(self, data_path, model_title, str_identity,
                       alg_type, model_ai_dir, model_num, file_num=1,
                       is_train=True, label_name=None, pc:ParamConfig=None,
                       drop_columns=None, date_type=[], sep='~',
                       classify_type2 = [[]],bool_type = [], is_categorical_func_type=None):
        """
        通用数据训练处理方法 - 重构版本

        使用通用数据处理管道来处理训练数据，简化代码并提高可维护性

        Args:
            data_path (str): 数据文件路径
            model_title (str): 模型标题
            str_identity (str): 标识列
            alg_type (str): 算法类型
            model_ai_dir (str): 模型保存目录
            model_num (int): 模型编号
            file_num (int): 文件编号，默认为1
            is_train (bool): 是否为训练，默认为True
            label_name (str): 标签列名
            pc (ParamConfig): 参数配置对象
            drop_columns (list): 要删除的列
            date_type (list, optional): 日期类型列列表
            sep (str): 分隔符，默认为'~'

        Returns:
            tuple: (处理后的DataFrame, 标签列, 参数配置对象)
        """
        self.lg = pc.lg
        return self._processing_pipeline(
            data_path=data_path,
            model_title=model_title,
            str_identity=str_identity,
            alg_type=alg_type,
            model_ai_dir=model_ai_dir,
            model_num=model_num,
            file_num=file_num,
            is_train=is_train,
            label_name=label_name,
            pc=pc,
            drop_columns=drop_columns,
            is_categorical_func_type=is_categorical_func_type,
            date_type=date_type,
            sep=sep
        )

    
#------------------------------------------------------------------
# 文本处理
#------------------------------------------------------------------
import numpy as np 
import pandas as pd 
from tpf import read,write
# from tpf.data.deal import DataDeal as dtl

class TextDeal:
    
    def __init__(self, data) -> None:
        """文本处理方法集 
        - data: pandas数表 
        """
        self.data = data 
        
    def log(self,msg, print_level=1):
        if self.print_level >= print_level:
            print(msg)
        
        
    def get_data(self):
        return self.data 
    
    def update_data(self,data):
        self.data = data 
        
    def head(self,num):
        return self.data.head(num)
        

    def word2id(self, c_names, word2id=None, start_index=1):
        """文本转换成索引
        - c_names:列名
        - word2id:编码字典，key为关键字，value为连续的整数索引；若非None，则在该字典基本上添加新的key与index
        - start_index:开始索引编码，默认为1，因为0给了未知类别'<UNK>'

        return
        -----------------------------
        每个列的编码字典,'<UNK>':0，即每一列的索引0代表未记录的词

        """
    
        cls_dict = {'<UNK>': 0}
        global_word2id = {'<UNK>': 0} if word2id is None or len(word2id)==0 else word2id.copy()
        next_index = start_index if len(global_word2id) == 1 else max(global_word2id.values()) + 1
        
        # 首先收集所有列的所有唯一词汇
        all_words = set()
        for cname in c_names:
            all_words.update(set(self.data[cname]))
        
        # 为所有词汇创建全局映射
        for word in all_words:
            if word not in global_word2id:
                global_word2id[word] = next_index
                next_index += 1
        
        # 为每列创建单独的映射字典（基于全局映射）
        for cname in c_names:
            cls_dict[cname] = global_word2id
        
        # 应用映射到每列
        for col in c_names:
            self.data[col] = (
                self.data[col]
                    .map(cls_dict[col])          # 已知类别 → 索引，未知 → NaN
                    .fillna(0)                   # NaN → 0
                    .astype(np.int64)            # 转换为整数
            )
            
        return self.data, cls_dict

    
    
    def word2id_pre(self, c_names, word2id=None):
        """
        预测时将指定列中的类别转成索引。
        未知类别统一映射为 0。
        
        Parameters
        ----------
        c_names : list[str]
            需要转换的列名列表。
        word2id : dict, optional
            类别到索引的映射字典。若未提供，则所有值视为未知，全部填 0。
        """
        if word2id is None:
            word2id = {}

        # 用 0 作为默认值，一次性完成映射
        for col in c_names:
            self.data[col] = (
                self.data[col]
                    .map(word2id[col])          # 已知类别 → 索引，未知 → NaN
                    .fillna(0)             # NaN → 0
                    .astype("int32")       # 或 Int64 以保留缺失，但这里统一用 0
            )
            
    
    def col_filter(self,regex):
        """
        选择指定的列,不同的列以|分隔,"name|age",
        "一元.*" 匹配 "一元一次","一元二次"等所有以"一元"开头的字符串 
        """
        self.data = self.data.filter(regex=regex)
        self.log("数据过滤之后的列-------------------------:",2)
        self.log(self.data.info(),2)

    def empty_num(self,col_name):
        self.data.loc[(self.data[col_name].isnull()), col_name] = np.mean(self.data[col_name])

    def empty_str(self,col_name,char_null="N"):
        self.data.loc[(self.data[col_name].isnull()), col_name] = char_null

    def error_max_7mean(self,col_name):
        """
        超过均值7倍的数据转为均值7倍
        """
        col_mean = np.mean(self.data[col_name])
        self.data[col_name][self.data[col_name]>7*col_mean] = 7*col_mean
    
    
    def onehot_encoding(self,c_names):
        """pandas onehot编码，每个类别一个新列
        """
        for cname in c_names:
            c_new_1 = pd.get_dummies(self.data[cname], prefix=cname)
            self.data = pd.concat([self.data,c_new_1],axis=1)
            self.data.drop([cname], axis=1, inplace=True)

    def col_drop(self,c_names):
        self.data.drop(c_names,axis=1,inplace=True)

    def replace_blank(self,to_float=True):
        """
        去除空格，并将NIL置0
        """
        for col in self.columns():
            index = 0
            for val in self.data[col]:
                # print("data type :",type(val))
                if isinstance(val,str):
                    matchObj = re.search( r'\s+', val)

                    if to_float:
                        # print("---col:{},val--{}==".format(col,val))
                        if val == "NIL":
                            val = "0"
                        if matchObj:
                            self.data[col].iloc[index] = float(val.replace('\s+','',regex=True,inplace=True))
                        else:
                            self.data[col].iloc[index] = float(val)
                    else:
                        if matchObj:
                            self.data[col].iloc[index] = val.replace('\s+','',regex=True,inplace=True)
                else:
                    continue
                index +=1



    def min_max_scaler(self,feature_range=(0, 1)):
        """
        return
        ---------------------
        <class 'numpy.ndarray'>,MinMaxScaler自动将pandas.core.frame.DataFrame转为了numpy.ndarray
        
        """
        self.scaler = MinMaxScaler(feature_range=feature_range)
        self.replace_blank()
        data = self.scaler.fit_transform(self.data)
        return data 

    def min_max_scaler_inverse(self, data):
        data = self.scaler.inverse_transform(data)
        return data 


class TextEmbedding:
    cls_dict = {}
    def __init__(self):
        pass
    
    @classmethod
    def cls2index(cls,df, classify_type=[],word2id=None,start_index=1):
        """类别转索引"""
        DataDeal.str_pd(df,classify_type)
        tt = TextDeal(data=df)
        for cc in classify_type:
            df,cls_dict = tt.word2id([cc],word2id=word2id,start_index=start_index)
            cls.cls_dict.update(cls_dict)
        return  df 
    
    @classmethod
    def cls2index2(cls,df, classify_type=[],word2id=None,start_index=1):
        """类别转索引"""
        DataDeal.str_pd(df,classify_type)
        tt = TextDeal(data=df)

        df,cls_dict = tt.word2id(classify_type,word2id=word2id,start_index=start_index)
        cls.cls_dict.update(cls_dict)
        return  df 
    
    @classmethod
    def cls2index_pre(cls,df, classify_type, word2id):
        """类别转索引预测"""
        DataDeal.str_pd(df,classify_type)
        tt = TextDeal(data=df)
        tt.word2id_pre(classify_type,word2id=word2id)


    @classmethod
    def col2index(cls,df,classify_type,classify_type2=[],
                  dict_file="dict_file.dict",
                  is_pre=False,word2id=None,start_index=1):
        """
        类别列索引编码：将文本类别转换为数值索引，支持独立编码和共享编码

        主要计算逻辑：
        1. 训练/推理模式分支
           - 训练模式 (is_pre=False)：创建新的编码字典并保存
           - 推理模式 (is_pre=True)：加载已有编码字典进行转换

        2. 推理模式处理逻辑
           - 加载编码字典：从dict_file文件中读取已保存的word2id映射
           - 合并编码列：将classify_type2中的列合并到classify_type中统一处理
           - 应用已有编码：使用cls.cls2index_pre方法，基于现有字典进行转换
           - 未知类别处理：未在字典中的类别统一映射为0（'<UNK>'标记）

        3. 训练模式处理逻辑
           - 共享编码组处理：
             * 遍历classify_type2中的每个共享组（如[['From', 'To']]）
             * 调用cls.cls2index2为每个共享组创建统一的编码空间
             * 多列共享同一字典，确保相同的值在不同列中获得相同索引
             * 使用空字典{}初始化，创建新的编码映射

           - 独立编码处理：
             * 调用cls.cls2index为classify_type中的独立列创建编码
             * 每列独立的编码空间，不同列的相同值可能有不同索引
             * 自动处理'<UNK>'标记，索引为0

        4. 编码字典保存
           - 将生成的编码字典保存到dict_file文件
           - 字典格式：{列名: {类别值: 索引}} 或 {共享组名: {类别值: 索引}}
           - 支持增量更新：新数据会被添加到现有字典中

        5. 内存管理
           - 使用TextDeal类进行实际的编码转换
           - 自动处理字符串类型转换
           - 支持大量类别的内存高效处理

        Args:
            df: 输入的pandas DataFrame
            classify_type: 独立编码的类别列列表
            classify_type2: 共享编码组列表，每个元素是一个列列表
            dict_file: 编码字典文件路径
            is_pre: 是否为预处理模式（True=推理，False=训练）
            word2id: 预加载的编码字典，推理模式使用
            start_index: 开始索引编码，默认为1，因为0给了未知类别'<UNK>'

        Returns:
            DataFrame: 类别列被替换为数值索引后的数据表

        Algorithm:
            训练模式:
                1. for each shared_group in classify_type2:
                   df = cls2index2(df, shared_group, word2id={})
                2. df = cls2index(df, classify_type)
                3. save encoding dictionary to file

            推理模式:
                1. load encoding dictionary from file
                2. merge classify_type2 into classify_type
                3. df = cls2index_pre(df, classify_type, word2id)

        Example:
            # 独立编码
            df_encoded = TextEmbedding.col2index(
                df,
                classify_type=['currency', 'payment_type'],
                dict_file='encoding.dict',
                is_pre=False
            )

            # 共享编码（From和To列使用同一编码空间）
            df_encoded = TextEmbedding.col2index(
                df,
                classify_type=['transaction_type'],
                classify_type2=[['From', 'To']],
                dict_file='shared_encoding.dict',
                is_pre=False
            )
        """
        if is_pre:
            if word2id is None:
                word2id = read(dict_file)
            for cc in classify_type2:
                classify_type.extend(cc)
            cls.cls2index_pre(df, classify_type=classify_type, word2id=word2id) 
        else: #重新编码
            for c in classify_type2:
            ## 类别编码扩充,机构作为账户特征,pc.col_type.classify_type不能再包含bank了，否则会重复编码
                df = cls.cls2index2(df, classify_type=c,word2id={},start_index=start_index)

            ## 类别索引编码
            df = cls.cls2index(df, classify_type=classify_type,start_index=start_index)
            write(cls.cls_dict,dict_file)

# ================== 测试函数 ==================

def test_get_col_names_optimization():
    """
    测试优化后的get_col_names方法
    """
    import pandas as pd
    import numpy as np
    from datetime import datetime

    print("测试优化后的get_col_names方法")
    print("=" * 50)

    # 创建测试DataFrame
    test_data = {
        'id': [1, 2, 3, 4, 5],
        'name': ['Alice', 'Bob', 'Charlie', 'David', 'Eve'],
        'age': [25, 30, 35, 40, 45],
        'salary': [50000.5, 60000.0, 70000.5, 80000.0, 90000.5],
        'is_active': [True, False, True, True, False],
        'category': pd.Categorical(['A', 'B', 'A', 'C', 'B']),
        'join_date': pd.to_datetime(['2020-01-01', '2019-05-15', '2021-03-10', '2018-11-20', '2022-07-05']),
        'score': np.array([85.5, 92.0, 78.5, 88.0, 95.5], dtype=np.float32)
    }

    df = pd.DataFrame(test_data)

    print("测试DataFrame信息:")
    print(f"形状: {df.shape}")
    print(f"列名: {list(df.columns)}")
    print(f"数据类型:\n{df.dtypes}")
    print()

    # 测试各种col_type参数
    test_cases = [
        ('all', '所有列'),
        ('num', '数值类型列'),
        ('int', '整数类型列'),
        ('float', '浮点数类型列'),
        ('cat', '分类类型列'),
        ('str', '字符串类型列'),
        ('bool', '布尔类型列'),
        ('date', '日期类型列'),
        ('datetime64[ns]', 'datetime64[ns]类型列'),
        ('object', 'object类型列'),
    ]

    for col_type, description in test_cases:
        try:
            result = DataDeal.get_col_names(df, col_type)
            print(f"{description} ({col_type}): {result}")
        except Exception as e:
            print(f"{description} ({col_type}): 错误 - {e}")

    print()

    # 测试新增的辅助方法
    print("测试新增的辅助方法:")
    print("-" * 30)

    # 测试按模式获取列名
    pattern_result = DataDeal.get_col_names_by_pattern(df, r'.*date.*')
    print(f"包含'date'的列: {pattern_result}")

    # 测试类型汇总
    type_summary = DataDeal.get_col_types_summary(df)
    print("数据类型汇总:")
    for dtype, cols in type_summary.items():
        print(f"  {dtype}: {cols}")

    print("\n测试完成!")

if __name__ == "__main__":
    # 运行测试
    test_get_col_names_optimization()
             
