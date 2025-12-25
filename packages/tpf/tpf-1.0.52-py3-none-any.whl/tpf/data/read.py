
from typing import List, Dict, Optional, Callable, Tuple, Any 
import pandas as pd
import numpy as np


def get_features(
    data_path: str,
    label_name: str,
    identity_cols: List[str],
    sep: str = '~',
    is_categorical_func: Callable[[str], bool] = None,
    date_type=[],
    bool_type = [],
    usecols: List[str] = None,
    drop_columns: List[str] = None,
    dtype_mapping: Dict[str, Any] = None,
    is_train: bool = True,
    
) -> Tuple[pd.DataFrame, Optional[pd.Series], Dict[str, List[str]]]:
    """
    通用特征提取函数：从原始数据中提取 X, y 和字段分类信息

    :param data_path: 数据路径
    :param label_name: 标签列名
    :param identity_cols: 身份标识列（不参与建模，但需保留）
    :param sep: 分隔符，默认 '~'
    :param is_categorical_func: 判断列是否为类别的函数，输入列名，返回 bool
    :param usecols: 指定读取的列（可选）
    :param drop_columns: 明确要丢弃的列（如临时字段）
    :param dtype_mapping: 强制指定某些列的 dtype
    :param is_train: 是否为训练模式（决定是否提取 y）

    :return: (X, y, column_types)
        - X: 特征 DataFrame（含 identity cols）
        - y: 标签 Series（仅训练时返回，否则为 None）
        - column_types: 字典，包含 num_type, classify_type 等分类
        
    :examples
    ---------------------------------------------
    
    #1. 使用默认规则（is_ 开头为类别）
    X, y, col_types = get_features(
        data_path="data.csv",
        label_name="Is Laundering",
        identity_cols=["Account"],
        sep='~',
        is_train=True
    )

    print("Numeric:", col_types['num_type'][:3], "...")
    print("Categorical:", col_types['classify_type'][:3], "...")


    #2. 自定义类别判断逻辑（如包含 _flag 或在某个白名单中）
    # 方法1：lambda
    is_cat = lambda col: col.lower().startswith("is_") or "_flag" in col.lower()

    # 方法2：函数
    def is_categorical(col: str) -> bool:
        return col in ['Payment Format', 'Bank'] or col.lower().startswith(('is_', 'has_', 'with_'))

    X, y, col_types = get_features(
        data_path="data.csv",
        label_name="Is Laundering",
        identity_cols=["Account", "Bank"],
        sep='~',
        is_categorical_func=is_cat,
        is_train=True
    )
    
    
    #3. 指定读取列 + 类型映射
    X, y, col_types = get_features(
        data_path="data.csv",
        label_name="Is Laundering",
        identity_cols=["Account"],
        usecols=["Account", "Amount", "is_suspicious", "risk_score", "Is Laundering"],
        dtype_mapping={"Amount": "float32", "risk_score": "float32"},
        is_categorical_func=lambda c: c.startswith("is_"),
        is_train=True
    )


    #4. 预测时使用（无需 y）
    X_pred, y_pred, col_types = get_features(
        data_path="new_data.csv",
        label_name="Is Laundering",  # 仍传入，但 is_train=False 时不提取
        identity_cols=["Account"],
        is_train=False
    )
    # y_pred is None


        
        
    """
    # 默认类别判断函数：以 'is_' 开头
    if is_categorical_func is None:
        is_categorical_func = lambda col: col.lower().startswith("is_")

    # 1. 读取数据
    try:
        df = pd.read_csv(data_path, sep=sep, usecols=usecols, dtype=dtype_mapping)
    except FileNotFoundError:
        raise FileNotFoundError(f"Data file not found: {data_path}")
    except Exception as e:
        raise RuntimeError(f"Error reading CSV: {e}")

    if df.empty:
        raise ValueError("No data available in the file.")

    # 2. 删除指定列
    if drop_columns:
        df = df.drop(columns=[col for col in drop_columns if col in df.columns])

    # 3. 分离特征列
    feature_cols = [col for col in df.columns if col not in identity_cols]
    if is_train and label_name in feature_cols:
        feature_cols.remove(label_name)

    # 4. 自动分类列类型
    column_types = {
        'num_type': [],
        'classify_type': [],
        'bool_type': [],
        'date_type': []
    }

    for col in feature_cols:
        if col == label_name:
            continue
        if col in date_type:
            column_types['date_type'].append(col)
        elif col in bool_type:
            column_types['bool_type'].append(col)
            column_types['num_type'].append(col)  # bool类型也归为数字类型处理
        elif is_categorical_func(col):
            column_types['classify_type'].append(col)
        else:
            column_types['num_type'].append(col)

    # 5. 类型转换
    # date_type保持原类型不做处理
    # bool类型归为数字类型处理
    # 数值列转 float（包含bool类型列）
    num_cols = [col for col in column_types['num_type'] if col in df.columns]
    df[num_cols] = df[num_cols].apply(pd.to_numeric, errors='coerce').fillna(0).astype(np.float64)

    # 类别列转 str + category
    cat_cols = [col for col in column_types['classify_type'] if col in df.columns]
    df[cat_cols] = df[cat_cols].astype(str).astype("category")

    # 6. 构造 X（保留 identity 列）
    X_cols = identity_cols + num_cols + cat_cols + date_type
    # print("X_cols:", X_cols[:5])
    X = df[X_cols].copy()

    # 排序列名（保证顺序一致）
    identity_set = set(identity_cols)
    sorted_features = sorted([c for c in X_cols if c not in identity_set])
    X = X[identity_cols + sorted_features]

    # 7. 提取 y（仅训练）
    y = None
    if is_train:
        if label_name is not None:
            y = df[label_name].astype(np.int64)

    return X, y, column_types
