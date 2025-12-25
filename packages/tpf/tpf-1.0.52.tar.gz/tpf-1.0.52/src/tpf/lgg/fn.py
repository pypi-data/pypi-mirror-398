from pickle import NONE
from tpf.lgg.cut_word import TextClassifier,CutWord
import jieba ,os ,pickle,re 

from tpf.box.fil import mkdir,parentdir,filname_nosuffix 
from tpf.d1 import np_load_x,np_save_x

from tpf.d1 import DataStat
from tpf.ml import model_load_joblib,model_save_joblib
from tpf.lgg.vec_word import Word2Vec

def delete_zh_flag(text):
    punctuation = '\s，？！（）!,;():?"\''
    text = re.sub(r'[{}]+'.format(punctuation),'',text)
    return text


def replace_c(text):
    """
    文本过滤
    """
    # 将中文的intab转化为英文的outtab 
    intab = ",?!()"
    outtab = "，？！（）"    

    # 删除一些html的元素 
    deltab = " \n)(<li>< li>+_-.><li \U0010fc01 _"
    trantab=text.maketrans(intab, outtab,deltab)
    return text.translate(trantab)

def replace_zh_flag(text):
    intab = ",?!"
    outtab = "，？！"    
    deltab = ")(+_-.>< "
    trantab=text.maketrans(intab, outtab,deltab)
    return text.translate(trantab)

class TextVec1():
    def __init__(self,text_file=None, tmp_file_save_dir=None, text_format="tab", use_jieba=False, use_hanlp=False,only_n=False) -> None:
        """
        文本转向量处理



        按指定格式初始化单词列表word_x,word_y


        tmp_file_save_dir:中间文件临时存储目录 
        """
        self.cw = CutWord()
        self.ds = DataStat()
        
    
        self.wv = Word2Vec()
        self.x = None
        self.y = None
        self.text_file = text_file
        self.pdir = pdir = parentdir(text_file)

        if tmp_file_save_dir:
            self.tmp_dir = os.path.join(tmp_file_save_dir, "data_tmp")
        else: # 如果不指定临时目录,则使用文件所在目录下的data_tmp目录 
            
            sf = os.path.join(pdir,"data_tmp")
            mkdir(sf)  # 目录不存在会创建,存在则跳过
            self.tmp_dir = sf 
        mkdir(self.tmp_dir)
        # 不带后缀的文件路径
        print(text_file,"text_file-------------------------")
        _fname = filname_nosuffix(file_name=text_file)
        self.filname = self.tmp_dir + os.sep + _fname
        
        self.word_file = ""
        # tab格式文本处理
        if self.text_file and text_format == "tab":
            if use_jieba:
                # 分词的临时存储文件
                self.word_file = sf = self.filname + ".jieba.word"
                if not os.path.exists(sf):  
                    self.cw.tab_xy_jieba(self.text_file, save_file=sf)
            if use_hanlp:
                # 分词的临时存储文件
                self.word_file = sf = self.filname + ".hanlp.word"
                if not os.path.exists(sf):  
                    self.cw.tab_xy_hanlp(self.text_file, save_file=sf,only_n=only_n)
        self._istrain = True 

        model_dir = os.path.join(self.pdir,"model")
        mkdir(model_dir)
        self._model_name_lda = model_dir+os.sep+"lda.ml"

    def istrain(self,train=True):
        self._istrain = train 



    def init_word_xy(self,word_x,word_y):
        self.word_x = word_x
        self.word_y = word_y 

    def get_word_xy(self):
        """
        按指定格式初始化单词列表word_x,word_y

        tmp_file_save_dir:中间文件临时存储目录 
        """
        if os.path.exists(self.word_file ):  # 如果文件存在,则直接加载 
            word_x,word_y = self.cw.get_xy_from_pkl(self.word_file )
            return word_x,word_y

    def value_counts(self,data):
        """
        统计不同类别标签的个数,查看样本均衡情况
        """
        count_dict = self.ds.value_counts(data)
        return count_dict

    def lable_encoding(self,word_y, one_hot=False, force=False):
        """
        标签编码,自动生成临时文件,如果文件已存在,则直接读取;


        设置force=True可再次进行编码 
        """
        if one_hot:
            pass 
        else:
            if force:
                self.y = self.ds.lable_encoding(word_y)
            else:
                if not (self.y and len(self.y)>0):
                    self.y = self.ds.lable_encoding(word_y)

        return self.y 

    def CountVectorizer_1(self, word_x,ngram_range=(1, 3),max_df=0.8,max_features=10000):
        """
        文件向量化,约1M用时1秒;向量化的数据量非常大,不保存,只保存降维后的向量 


        retrun 
        ----------------------------
        ndarray 
        """
        x = self.wv.text_CountVectorizer_1(word_x,max_df=max_df,max_features=max_features,ngram_range=ngram_range)
        return x.A 

    def np_save_vec(self,vec):
        """
        文本向量化的中间结果非常地大,建议直接进行降维,然后保存降维后的数据  
        """

        # 向量临时存储文件
        sf = self.filname + ".vec.tmp"  #文件大时,未写完异常中断,不会读这个文件
        dsf = self.filname + ".vec"
        np_save_x(vec,sf)
        os.rename(sf+".npz",dsf+".npz")  # 如果dsf文件已存在,则会先删除dsf文件

    def np_load_vec(self):
        dsf = self.filname + ".vec"
        x = np_load_x(dsf)
        return x 

    def lda_batch(self,x, n_components=128, batch_size=100, force=False):
        """
        LDA批次降维并保存降维后的结果,再次降维时,如果文件已存在则优先读取文件,除非指定force=True 
        """
        
        dsf = self.filname + ".vec.npz"
        model_path=self._model_name_lda

        if force and self._istrain: # 预测时,不重复生成模型,也就是说force无效 
            x = self.wv.lda_batch(x, n_components=n_components, batch_size=batch_size,model_path=model_path)
            self.np_save_vec(x)
            return x 

        # 不管是训练还是预测,相同文件的数据只要存在就可以直接加载
        # 前提,训练集与测试集不在同一文件中
        if os.path.exists(dsf):  
            x = self.np_load_vec()
        elif self._istrain:    
            x = self.wv.lda_batch(x, n_components=n_components, batch_size=batch_size,model_path=model_path)
            self.np_save_vec(x)
        else:   # 如果已经训练过了,直接加载模型,然后进行预测
            print("加载model,进行预测-------------------------------")
            model_lda = model_load_joblib(file_path=model_path)
            # x = model_lda.fit_transform(x) # 该方法会使预测时精度降低5个百分点
            x = model_lda.transform(x)
            model_save_joblib(model_lda, model_path)
            self.np_save_vec(x)
        return x 

        

    def CountVectorizer_save(self, word_x, force=False):
        """
        单词列表向量化 CountVectorizer 示例 1


        保存文件会耗费大量内存,原因未知
        """
        # 向量临时存储文件
        sf = self.filname + ".vec.tmp"  #文件大时,未写完异常中断,不会读这个文件
        dsf = self.filname + ".vec"
        if force :
            x = self.wv.CountVectorizer_1(word_x)
            with open(sf, "wb") as f:
                pickle.dump(x, f)
            os.rename(sf,dsf)  # 如果dsf文件已存在,则会先删除dsf文件
        elif os.path.exists(dsf) and os.path.getsize(dsf)>0:  # 如果文件存在,则直接加载
            with open(dsf, "rb") as f:
                x = pickle.load(f)
        else:
            x = self.wv.CountVectorizer_1(word_x)
            with open(sf, "wb") as f:
                pickle.dump(x, f)
            os.rename(sf,dsf)  # 如果dsf文件已存在,则会先删除dsf文件

        return x 






