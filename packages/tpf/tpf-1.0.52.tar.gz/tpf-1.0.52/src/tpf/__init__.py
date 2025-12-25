"""
方法直接放tpf的__init__方法中
除以下两个
python基础方法，
data集获取方法 
"""


from tpf.box.base import stp 
from tpf.d1 import DataStat
# from tpf.d1 import DataDeal
from tpf.d1 import pkl_load,pkl_save
#from tpf.dl import T 
from tpf.d1 import read,write
from tpf.d1 import value_map 
from tpf.d2 import mean_by_count
from tpf.ml import MlTrain 
# from tpf.db import DbTools
# from tpf.db import OracleDb

from tpf.box.fil import log
from tpf.box.fil import filname_nosuffix
from tpf.metric import get_psi_bybins


# from tpf.data import toolml as tml
# from tpf.data.toolml import rules_clf2
# from tpf.datasets import load_boston

from tpf.data.make import random_str_list,random_str,random_str_lower
from tpf.data.make import random_yyyymmdd
from tpf.data.make import TimeGen
#-------------link---------------------

# from tpf.link import Corr
# from tpf.link.datadeal import DateDeal 
# from tpf.link import FeatureEval

# from tpf.link.toolml import null_deal_pandas,std7,min_max_scaler
# from tpf.link.toolml import str_pd,get_logical_types,ColumnType
# from tpf.link.toolml import data_classify_deal
# from tpf.link.toolml import pkl_save,pkl_load

