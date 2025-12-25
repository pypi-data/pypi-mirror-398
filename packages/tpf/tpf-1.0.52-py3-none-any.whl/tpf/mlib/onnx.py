import numpy as np
import onnx
import onnxruntime as ort
from skl2onnx import convert_sklearn
from skl2onnx.common.data_types import FloatTensorType


def save_onnx_ml(model,in_features,file_path=None):
    """机器学习模型转onnx
    """
    #当输入数据维度可变时，需特别声明输入数据的维度：
    initial_types = [('input', FloatTensorType([None, in_features]))]  
    # 将模型转换为ONNX格式
    onnx_model = convert_sklearn(model, initial_types=initial_types)
    # 保存ONNX模型
    onnx.save_model(onnx_model, file_path)


def run_onnx_ml(file_path,X,proba=True,providers=["CPUExecutionProvider"]):
    """onnxruntime运行机器学习Onnx
    """
    # 加载ONNX模型
    ort_session = ort.InferenceSession(file_path, providers=providers)
    
    # 获取输入和输出的名称
    input_name = ort_session.get_inputs()[0].name
    output_name = ort_session.get_outputs()[0].name
    X_test_onnx = X.astype(np.float32)  # ONNX Runtime期望输入为float32类型的列表
    #第1个参数为None才会输出概率
    result = ort_session.run(None, {input_name: X_test_onnx})
    if proba:
        return result[1]
    else:
        return result[0]
