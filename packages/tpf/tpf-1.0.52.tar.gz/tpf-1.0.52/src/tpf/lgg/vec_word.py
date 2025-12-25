
from os import sep
from pickle import NONE
from tpf.lgg.cut_word import TextClassifier
# from tpf.box.d1 import pkl_fil_dump
from tpf.d1 import pkl_save
from tpf.lgg.stop_words import get_stwd_1

from sklearn.feature_extraction.text import CountVectorizer ,TfidfTransformer,TfidfVectorizer


def vec_word_1(word_seg_path, save_vec_path,batch_size=500):
    
    news = TextClassifier()
    # 加载分词数据
    x,y = news.get_word_segment(word_seg_path)

    # 标签编码
    _, y = news.lable_encoding(y)
    
    x = news.text_vec_batch(x, batch_size=batch_size)
    # pkl_fil_dump([x,y], save_vec_path)
    pkl_save((x,y), save_vec_path)




class Word2Vec():

    # def __init__(self,word_list=None,log_level=2) -> None:
    #     self._word_list = word_list 
    #     self._word_vec = None
    #     self._x = None 
    #     self.log_level = log_level

    def __init__(self,log_level=2) -> None:
        self.log_level = log_level


    def text_CountVectorizer_1(self, train_data,ngram_range=(1, 3),max_df=0.80,max_features=None):
        """
        文本向量化


        return 
        -----------------------------------
        scipy.sparse.csr.csr_matrix
        """

        # if isinstance(train_data,list):
        #     train_data = np.array(train_data)

        stop_word_list = get_stwd_1()

        # 会对每一个样本进行向量化
        # 不是整个数据集所有的词合计到一起
        # 每个样本的词的个数与其他样本是不一样的
        # 所以，每行样本的向量长度也是不同的
        # vect_method = CountVectorizer(
        #                 stop_words={".","。"," ","(",")","[","]","{","}","（","）","！","?"},    #停用词
        #                 # stop_words=None,
        #                 token_pattern=r"(?u)\b\w+\b",
        #                 ngram_range=(2, 3),
        #                 max_df=0.95,                  #百分之百的词出现，无法根据此分类，可去掉； 1.0 ＝ 100％ 
        #                                             #min_df＝1只有一个文章出现
        #                 max_features= None            # 保存多少个重要特征
        #                 ) 
                
        vect_method = CountVectorizer(
                        stop_words=stop_word_list,    #停用词
                        # stop_words=None,
                        token_pattern=r"(?u)\b\w+\b",
                        ngram_range=ngram_range,
                        max_df=max_df,                  # 百分之百的词出现，无法根据此分类，可去掉； 1.0 ＝ 100％ 
                                                      # min_df＝1只有一个文章出现
                        max_features= max_features           # 保存多少个重要特征
                        ) 

        text_sparse_matrix = vect_method.fit_transform(train_data) # 向量化 

        if self.log_level == 3:
            # print(type(text_sparse_matrix[0]))  # <class 'scipy.sparse.csr.csr_matrix'>
            # print(text_sparse_matrix.shape)     # (22, 30959)
            row_count = text_sparse_matrix.shape[0]
            print("row count:",row_count,len(train_data))
            for i in range(row_count):
                print("count_nonzero, row {} :".format(i), text_sparse_matrix[i].count_nonzero())

        return text_sparse_matrix 

    def CountVectorizer_1(self, word_list):
        """
        CountVectorizer 示例 1

        return 
        --------------------------------
        ndarray 

        """
     
     
        # text_sparse_matrix = self.text_CountVectorizer_1(word_list)
        # word_vec = text_sparse_matrix.A 

        news = TextClassifier()
        x = news.text_CountVectorizer(word_list)
        word_vec = x.A

        return word_vec

    def lda_batch(self,x,n_components=128,batch_size=100,model_path=None):
        """
        lda 批次降维
        """
        from tpf.box.d2 import lda_batch 
        x = lda_batch(x,n_components=n_components,batch_size=batch_size,model_path=model_path)
        return x 

    def dimension_reduction(self):
        pass 

    def text2vec_1(self):
        pass 







