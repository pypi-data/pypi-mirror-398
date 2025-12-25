
from tpf.mlib.tree.lightgbm import lgbm_baseline
from tpf.mlib.tree.lgbmclassifier import lgbmc_02

# 导入可选依赖包，如果未安装则设置为None
try:
    # 检查catboost是否安装
    import catboost
    from tpf.mlib.tree.catboost import catboostc_03
except ImportError:
    catboostc_03 = None

try:
    # 检查xgboost是否安装
    import xgboost
    from tpf.mlib.tree.xgbc import xgbc_01
except ImportError:
    xgbc_01 = None

try:
    # 检查scikit-learn是否安装 (svm依赖)
    import sklearn
    from tpf.mlib.tree.svm import svc_01
except ImportError:
    svc_01 = None

# 导入日志记录器用于输出提示信息
try:
    import logging
    logger = logging.getLogger(__name__)

    # 记录未安装的包信息
    if catboostc_03 is None:
        # logger.warning("catboost未安装，catboostc_03功能将不可用")
        pass 
    if xgbc_01 is None:
        # logger.warning("xgboost未安装，xgbc_01功能将不可用")
        pass
    if svc_01 is None:
        # logger.warning("scikit-learn未安装，svc_01功能将不可用")
        pass 
except ImportError:
    # 如果连logging都没有，则静默处理
    pass

# 提供便捷的检查函数
def get_available_models():
    """
    获取当前可用的模型列表

    Returns:
        dict: 包含可用模型信息的字典
    """
    available_models = {
        'lightgbm': {
            'lgbm_baseline': lgbm_baseline,
            'lgbmc_02': lgbmc_02
        },
        'catboost': catboostc_03,
        'xgboost': xgbc_01,
        'svm': svc_01
    }

    # 过滤掉None值
    available = {k: v for k, v in available_models.items() if v is not None}

    return available

def is_model_available(model_name):
    """
    检查特定模型是否可用

    Args:
        model_name (str): 模型名称 ('catboost', 'xgboost', 'svm')

    Returns:
        bool: 如果模型可用返回True，否则返回False
    """
    model_map = {
        'catboost': catboostc_03,
        'xgboost': xgbc_01,
        'svm': svc_01
    }

    return model_map.get(model_name) is not None

# 导出的公共接口
__all__ = [
    'lgbm_baseline',
    'lgbmc_02',
    'catboostc_03',
    'xgbc_01',
    'svc_01',
    'get_available_models',
    'is_model_available'
]