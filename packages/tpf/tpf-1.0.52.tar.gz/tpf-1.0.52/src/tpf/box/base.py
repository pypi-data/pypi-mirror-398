'''
Description: 基础功能
Author: 七三学徒
Date: 2022-01-25 15:30:42
'''
import numpy as np 
import os ,time 
import platform
import pandas as pd 

import json 
import numpy 

class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, numpy.int):
            return int(obj)
        elif isinstance(obj, numpy.float):
            return float(obj)
        elif isinstance(obj, numpy.ndarray):
            return obj.tolist()        
        return json.JSONEncoder.default(self, obj)


def has_key(dct,key):
    res = key in list(dct.keys())
    return res 

def stp(data, msg=None):
    """print shape type
    """
    ss = "shape:{}, type:{}".format(data.shape,type(data))
    if msg:
        ss = "{}, {}".format(ss,msg)

    print(ss)


def is_windows():
    system = platform.system()
    if system == "Windows":
        return True
    else:
        return False

# 判断对象是否为 DataFrame

def is_dataframe(obj):

    return isinstance(obj, pd.DataFrame)

def is_numpy_array(variable):

    return isinstance(variable, np.ndarray)



if __name__=="__main__":
    from tpf.vec3 import matrix_multiply

    a = np.arange(6).reshape(2,3)

    b = np.arange(6).reshape(3,2)

    c=matrix_multiply(a,b)
    
    print(c)


