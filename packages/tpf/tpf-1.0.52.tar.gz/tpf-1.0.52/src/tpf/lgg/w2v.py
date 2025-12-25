
"""
词转向量：word2vec

输入：单词列表
输入：不重复的单词列表，与其对应的词向量
"""

import collections
import random 
import numpy as np 


class WordBatch():
    """
    调用该方法时，内存崩溃，而原代码则没有这个问题，后续可能用rust封装一下，看看内存的使用情况 ,
    后来添加  del words 之后，内存就够用了
    """
    def __init__(self,words=[],is_pre=False) -> None:
        self.vocabulary_size = len(set(words))
        self.is_pre = is_pre
        self.data = list()
        self.data_index = 0
        self.count = list()
        self.dictionary = dict()
        self.reverse_dictionary = dict()
        self.build_dataset(words=words)
        self.vocabulary_size = len(set(words))
        del words
        # print('uniuqe words:', self.vocabulary_size)  # uniuqe words: 199247

    def build_dataset(self, words):
        """
        词频越大，词的类别编号越小

        words:文本所有的词，未去重 


        return
        -----------------------------------
        data:  单词列表所对应的编号ID列表,


        count：不重复的词按词频从高到低排序，类似[('的', 13), ('数学', 8), ('数学家', 3)]
        但不同的是，count去掉了最后一个，也就是最不重要的那个单词，
        同时为count列表添加一个元素，放在索引为0的位置，
        它就是['UNK', -1],用于表示未知的／无法识别的单词
        count列表去掉一个添加一个，
        所以count列表的长度依然是词汇表不重复单词的个数，
        简称为词汇表长度self.vocabulary_size


        dictionary: 单词到ID的字典,


        reverse_dictionary: ID到单词的字典


        注意：
        未知单词unk_count会统计个数，但这部分代码被注释掉了，
        为什么？
        因为按代码的逻辑，先从所有单词统计不重复的单词，编号，反转，
        怎么会出现未编号的单词，不可能的，
        写上这段代码除了增加计算量外没别的用处，
        所以这段代码被注释了

        那为什么要写上？
        这是因为word2vec最先出现在训练阶段，
        通过词向量计算出参数权重，得到模型，
        之后该预测了，这才训练的意义所在，
        而预测的数据是未知的，可能不在原来训练样本中，
        在预测时加上这段代码，
        可以了解一下预测中出现了多少未知的单词


        后来，我在word2vec的基础上加上了is_pre这个参数，用于控制这段逻辑，
        因为预测的时候，不能再修改模型，也不能动原来的字典了，
        
        为什么预测的时候不能学习？要是发现预测不对就再学习才更智能！
        因为预测之所以叫预测，是因为结果尚未出现，而学习建立在结果已经出现的前提上


        其实，这里的真正问题是，一改全改的问题
        输入的字典数，数据shape,
        模型学习后，将之做为数据，参数计算的维度，这些维度贯穿整个模型，
        后续发现新词，加入字典，这就从根源上改变了数据的shape,
        跟原来的在旧shape上进行学习的模型 匹配不上，
        所以模型不认这个新shape，
        这是原因，也是现状

        可...
        可...
        可我不甘心啊，这样实在太麻烦...
        现实中的智慧生命的本能就是一边认识新东西，一边更新自己的知识...
        为什么这个叫人工智能的程序不能自动实现这个...


        这个...
        这个...
        这个...
        这个就交给看到这段话的你们了，
        你们将去开启新一代的人工智能！！！


        """
        
        count = [['UNK', -1]] # UNK就是不知道，不知道的词赋值为 -1 
        # count = [{'UNK': -1}]
        #collections.Counter(words).most_common
        count.extend(collections.Counter(words).most_common(self.vocabulary_size - 1))
        self.count = count 

        dictionary = self.dictionary
        for word, _ in count:
            dictionary[word] = len(dictionary)

        
        unk_count = 0
        self.data=[dictionary[word]  if  word in dictionary else 0 for word in words]
        # for word in words:
        #     if word in dictionary:
        #         index = dictionary[word]
        #     else:
        #         index = 0  # dictionary['UNK']
        #         unk_count += 1
        #     data.append(index)
        if self.is_pre:
            for word in words:
                if word in dictionary:
                    index = dictionary[word]
                else:
                    index = 0  # dictionary['UNK']
                    unk_count += 1
                self.data.append(index)
            
        count[0][1] = unk_count
        self.reverse_dictionary = dict(zip(dictionary.values(), dictionary.keys()))
        return self.data, count, dictionary, self.reverse_dictionary


    def generate_batch(self, batch_size, skip_window=2):
        """
        # Step 3: Function to generate a training batch for the skip-gram model.
        
        原理:滑动取词
        ----------------------------
        span = 2 * skip_window + 1 
        滑动窗口的尺度，包含相关单词的长度，
        1表示中间的中心单词， skip_window表示离中心词的距离，相邻为1，隔一个为2
        乘以2表示，前面一个，后面一个



        得到下面这样的输出：
        单词->前一个单词
        单词->后一个单词

        """
        num_skips=2*skip_window
        assert batch_size % num_skips == 0

        # skip_window是前后的单词数，
        # num_skips是取多少个(中心单词，前/后单词)组
        # 所以num_skips不可能超过skip_window的两倍
        assert num_skips <= 2 * skip_window


        batch = np.ndarray(shape=(batch_size), dtype=np.int32)    # 1维数组，相当于列表
        labels = np.ndarray(shape=(batch_size, 1), dtype=np.int32)# [n,1]，相当于列向量

        # 取一个窗口长度的单词，＋1加的是中心单词
        span = 2 * skip_window + 1  # [ 划动窗口的尺度，包含相关单词的长度，1表示中间的中心记事， skip_window表示离中心词的]
        buffer = collections.deque(maxlen=span)   # 队列，其长度为窗口长度
        for _ in range(span):
            buffer.append(self.data[self.data_index])
            self.data_index = (self.data_index + 1) % len(self.data)

        # 输出多少个中心单词相关组合，
        # 一个中心单词相关组合(中心单词，前/后单词)对应 num_skips=2*skip_window 个组合
        for i in range(batch_size // num_skips):#i取值0,1,2,3, 两个斜杠表示整除
            target = skip_window  # target label at the center of the buffer
            targets_to_avoid = [skip_window]
            for j in range(num_skips):
                # 取[0,span-1]范围的num_skips个整数，每次取一个,然后放入targets_to_avoid数组
                # span - 1 ＝ 2 * skip_window >＝ num_skips
                # 最多在最后一次for循环中取出最后一个不同的整数，所以不会出现死循环 
                # 巧妙的地方在于，新取到的值与列表中已有的值都不同
                # 这样就做到了，用过的单词(放入列表)，不会再用到
                # 第一步就是将中心单词放入列表中，因为我们要取中心单词前/后span尺度中的单词
                while target in targets_to_avoid:
                    target = random.randint(0, span - 1)

                targets_to_avoid.append(target)
                # 因为队列的长度就是窗口的长度，因此buffer[skip_window]永远都是中心单词
                batch[i * num_skips + j] = buffer[skip_window]
                labels[i * num_skips + j, 0] = buffer[target]  #窗口长度内，除中心单词外的所有其他单词

            # 加入一个新单词，自动去掉一个旧单词，相当于中心单词位置＋1
            # 即向前走了一步
            buffer.append(self.data[self.data_index])
            self.data_index = (self.data_index + 1) % len(self.data)
        return batch, labels









