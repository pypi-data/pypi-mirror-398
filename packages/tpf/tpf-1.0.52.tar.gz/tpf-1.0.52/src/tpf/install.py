
ml = """
    pip install --upgrade pip -i https://pypi.tuna.tsinghua.edu.cn/simple  #pip要求系统具有SSL

    pip install jupyter jupyter_contrib_nbextensions -i https://pypi.tuna.tsinghua.edu.cn/simple

    pip install pandas sklearn-pandas scikit-learn hmmlearn  sklearn_crfsuite chinese_calendar matplotlib  pydotplus  openpyxl  pdfminer.six -i https://pypi.tuna.tsinghua.edu.cn/simple

    pip install lightgbm catboost xgboost statsmodels -i https://pypi.tuna.tsinghua.edu.cn/simple

    pip install featuretools feature-engine tsfresh mlxtend shap seaborn pyod copulas cx_Oracle pymysql==1.0.2 sqlalchemy -i https://pypi.tuna.tsinghua.edu.cn/simple

    """
    
dl = """
    pip install torch torchvision torchaudio onnx onnxruntime -i https://pypi.tuna.tsinghua.edu.cn/simple

    >>> import torch
    >>> torch.__version__
    '2.5.1+cu124'

    #https://pypi.org/project/torch-scatter/
    pip install torch-scatter -f https://data.pyg.org/whl/torch-2.5.1+cu124.html -i https://pypi.tuna.tsinghua.edu.cn/simple
    pip install torch-sparse -f https://data.pyg.org/whl/torch-2.5.1+cu124.html -i https://pypi.tuna.tsinghua.edu.cn/simple
    pip install torch-geometric -i https://pypi.tuna.tsinghua.edu.cn/simple
    pip install torch-cluster -f https://data.pyg.org/whl/torch-2.5.1+cu124.html -i https://pypi.tuna.tsinghua.edu.cn/simple
    pip install torch-spline-conv -f https://data.pyg.org/whl/torch-2.5.1+cu124.html -i https://pypi.tuna.tsinghua.edu.cn/simple

    pip install torch-scatter -f https://data.pyg.org/whl/torch-2.5.1+cpu.html -i https://pypi.tuna.tsinghua.edu.cn/simple
    pip install torch-sparse -f https://data.pyg.org/whl/torch-2.5.1+cpu.html -i https://pypi.tuna.tsinghua.edu.cn/simple
    pip install torch-geometric -i https://pypi.tuna.tsinghua.edu.cn/simple
    pip install torch-cluster -f https://data.pyg.org/whl/torch-2.5.1+cpu.html -i https://pypi.tuna.tsinghua.edu.cn/simple
    pip install torch-spline-conv -f https://data.pyg.org/whl/torch-2.5.1+cpu.html -i https://pypi.tuna.tsinghua.edu.cn/simple

    """
