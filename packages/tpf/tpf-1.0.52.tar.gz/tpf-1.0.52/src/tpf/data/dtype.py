'''
Description: 
Author: 七三学徒
Date: 2022-01-24 14:35:00
FilePath: /73_code/aisty/box/dtype.py
'''

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
