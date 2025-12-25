import numpy as np 
import random
import pandas as pd 
import wave, os

from tpf.box.fil import parentdir
from tpf.box.fil import iswin


"""

if iswin():
    img_path1 = "K:\\tpf\\aiwks\\datasets\\images\\001"
    csv_path1 = ""
else:
    img_path1 = "/opt/wks/aiwks/datasets/images/001"
    csv_path1 = "/opt/wks/aiwks/datasets/text/a.cvs"

class TestEnvPath(object):
    ABS_DIR = "K:\\tpf\\aiwks\\datasets\\images\\001"
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DATA_TMP = os.path.join(os.path.dirname(os.path.abspath(__file__)),"data_tmp")

    DATA_PATH = os.path.join(ABS_DIR,"dataset")
    DATA_BREAST_CANCER_PATH = os.path.join(DATA_PATH,"breast_cancer\\data")


"""



if iswin():
    
    pan_flag = "E"
    ABS_DIR=pan_flag+":\\tpf\\aiwks"
    IMG_MNIST = pan_flag+":\\tpf\\aiwks\\datasets\\MNIST_reader"
    IMG_CIFAR  = pan_flag+":\\tpf\\aiwks\\datasets\\images"
    img_path1 = pan_flag+":\\tpf\\aiwks\\datasets\\images\\001"
    csv_path1 = ""
    dataset_path1 = pan_flag+":\\tpf\\aiwks\\datasets"
    DATA_ROOT= "C:\\datai"

    img_base_path = pan_flag+":\\shu\\img"

    TPF_BASEDIR=pan_flag+":\\tpf\\aitpf\\source"
    TPF_DATADIR=pan_flag+":\\tpf\\aitpf\\source\\dataset"
    TPF_MODELDIR=pan_flag+os.path.join(TPF_BASEDIR,"models")

else:
    ABS_DIR="/opt/wks/aiwks/"

    img_base_path = "/opt/shu/img"
    run_path = "/opt/shu/run"

    IMG_MNIST = "/wks/datasets/MNIST_reader"
    IMG_CIFAR = "/wks/datasets/images"
    img_path1 = "/wks/datasets/images/001"
    csv_path1 = "/wks/datasets/text/a.cvs"
    dataset_path1 = "/wks/datasets"
    DATA_ROOT="/wks/datasets"

    TPF_BASEDIR="/opt/wks/aitpf/source/"
    TPF_DATADIR="/opt/wks/aitpf/source/dataset"
    TPF_MODELDIR=os.path.join(TPF_BASEDIR,"models")



class ImgPath():
    mnist_data_test=os.path.join(IMG_MNIST,"img0-9_test.pkl")
    mnist_data_train=os.path.join(IMG_MNIST,"img0-9_train.pkl")
    mnist_run = os.path.join(IMG_MNIST,"model")
    mnist_tmp = os.path.join(IMG_MNIST,"tmp")



class TestEnvPath():
    
    BASE_DIR=os.path.dirname(os.path.abspath(__file__))
    DATA_TMP = os.path.join(os.path.dirname(os.path.abspath(__file__)),"data_tmp")

    DATA_PATH = os.path.join(ABS_DIR,"datasets")
    DATA_BREAST_CANCER_PATH = os.path.join(os.path.join(DATA_PATH,"breast_cancer"),"data")


class ImgEnvPath():
    TuGou1= os.path.join(ABS_DIR,"datasets/test_image/tugou/tugou16.jpg")



def get_data_path(fil):
    data_dir = "/data"
    fil_path = os.path.join(data_dir,fil)
    return  fil_path
    

class data_file_path:
    pd2 = get_data_path("pd2.csv")
    
    @staticmethod
    def mnist():
        """
        手写数字识别
        """
        return get_data_path("deep/mnist.npz")

    @staticmethod
    def taitan01():
        """
        泰坦原始数据
        """
        return "/opt/aidoc/data/taitan_train.csv"

    def taitan02():
        """
        泰坦独热编码后的数据
        """
        return "/opt/aidoc/data/taitan02.csv"

    def pd2():
        """
        pandas 测试数据存文件
        
        """
        return "/opt/aidoc/data/pd2.csv"
    
    def wordcount1():
        """
        word count 
        单词统计文本
        """
        return [
            "/data/1_PySpark/test-1.txt",
            "/data/1_PySpark/test-2.txt"]

    def ctr_train01():
        """
        点击率训练集01
        """ 
        return "/data/ctr/train_sample_ctr.csv"

    def ctr_test01():
        """
        点击率测试集01
        """ 
        return "/data/ctr/test_sample_ctr.csv"

    def text_news01_small():
        """
        长文本新闻数据，用于代码开发，22行
        tail -n 100 > cnews_row_2.train.txt
        """
        return "/opt/aisty/data/text_news/kaifa.txt"
        
    def text_news01_small2():
        """
        长文本新闻数据，用于代码开发，5718行
        tail -n 60000 cnews.train.txt|grep "体育" > cnews_row_6.train.txt
        """
        return "/opt/aisty/data/text_news/cnews_row_6.train.txt"

    def text_news01_small_save():
        """
        长文本新闻数据，用于代码开发
        """
        return "/opt/aisty/data/text_news/cnews_row_2.train2.pkl"

    def text_news01_small_save2():
        """
        长文本新闻数据，用于代码开发
        """
        return "/opt/aisty/data/text_news/cnews_row_2.train6.pkl"

    def text_news01_small_save2():
        """
        长文本新闻数据，用于代码开发
        """
        return "/opt/aisty/data/text_news/cnews_row_2.train6.pkl"

    def text_news01_train():
        """
        长文本新闻数据，训练集,125M
        """
        return "/opt/aisty/data/text_news/cnews.train.txt"

    def text_news01_train2():
        """
        长文本新闻数据，训练集,125M
        """
        return "/opt/aisty/data/text_news/cnews.train2.pkl"

    def text_news01_train3():
        """
        长文本新闻数据，训练集
        """
        return "/opt/aisty/data/text_news/cnews.train3.pkl"

    def text_news01_test():
        """
        长文本新闻数据，测试集，27M
        """
        return "/opt/aisty/data/text_news/cnews.test.txt"

    def text_news01_val():
        """
        长文本新闻数据，可用于超参调优，12M
        """
        return "//opt/aisty/data/text_news/cnews.val.txt"

    def text_news01_lda_small():
        """
        长文本新闻数据，用于代码开发,
        LDA降维后数据
        """
        return "/opt/aisty/data/text_news/text.npz"

    def text_news01_lda_small_pkl():
        """
        长文本新闻数据，用于代码开发,
        LDA降维后数据
        """
        return "/opt/aisty/data/text_news/cnews_lda_2.train2.pkl"

    def text_news01_lda_small_pkl2():
        """
        长文本新闻数据，用于代码开发,
        LDA降维后数据
        """
        return "/media/xt/source/data/text_news/cnews_lda_2.train6.pkl"

    def text_news01_lda_train():
        """
        长文本新闻数据，用于代码开发,
        LDA降维后数据
        """
        return "/opt/aisty/data/text_news/text_lda_train.pkl"



if __name__=="__main__":
    ep = TestEnvPath()
    # print(ep.DATA_TMP)
    # print(ep.DATA_BREAST_CANCER_PATH)
