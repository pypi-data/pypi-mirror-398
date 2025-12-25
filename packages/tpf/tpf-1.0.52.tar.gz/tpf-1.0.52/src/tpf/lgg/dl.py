
import os,time
from pickle import NONE  
import torch 
import torch.nn as nn 
from tpf.py1.fil import mkdir 
from tpf.lgg.d1 import wordid_dict
from tpf.box.d1 import pkl_load,pkl_save ,write,read 
import torch.nn.functional as F 

import numpy as np 

class AudioModel1(nn.Module):
    def __init__(self, input_size=None, hidden_size=512, hidden_layers=2,out_channels=None) -> None:
        """
        语音模型1

        model = AudioModel1(input_size=_feature_count, word2id=word2id)

        model.train()

        model.eval()
        
        """
        super().__init__()

        # 多的1为nn.CTCLoss的空白字符的ID
        # 最后的维度
        self._out_channels_last = out_channels 

        # 构建多层循环神经网络 
        self._hidden_size = hidden_size
        self._hidden_layers = hidden_layers  

        # GRU相当于STFT 
        self._rnn = nn.GRU(input_size=input_size, hidden_size=self._hidden_size, num_layers=hidden_layers)

        # 卷积:将通道数变成词的个数 , 加1加的是空白字符的标签
        self._cnn = nn.Conv1d(in_channels=self._hidden_size, out_channels=self._out_channels_last, kernel_size=1, stride=1)


    def forward(self, x):
        """ 
        输入x:[T, B, C] 
        """ 
        T, B, C = x.shape 

        # 初始状态 
        # 2层,Batch,256个特征 
        h = torch.zeros([self._hidden_layers, B, self._hidden_size]) 
        y,h = self._rnn(x, h)      # y.shape:[T,B,C] 
        # F.batch_norm()
        y = F.relu(y)
        
        y = y.permute(1, 2, 0)     # [B,C,T]

        # 注意,卷积将特征映射到了词
        # 2884个词,后面会对这2884个词进行softmax,转为概率
        # 某个词的概率最大,那么就会选择这个最大概率的词作为该分支的最终结果 
        y = self._cnn(y)  # torch.Size([10, 2885, 200])

        # 卷积之后,维度还原为[T,B,C]
        y = y.permute([2,0,1])  # [B,C,T] -> [T,B,nword+1]
        # print(y.shape,h.shape)   
        return y 


class AudioModel():
    def __init__(self, model=None, tmp_dir=None,word2id=None,id2word=None,h0=None,init_h0=False) -> None:
        """
        语音模型1

        model = AudioModel1(input_size=_feature_count, word2id=word2id)

        model.train()

        model.eval()
        
        """
        super().__init__()
        self._h0=h0 
        self._init_h0 = init_h0

        # 将标签列转为概率 
        self.__logSoftmax = nn.LogSoftmax(dim=2)

        # 指定损失函数的空白字符为最后维度的最后一个编号
        # bland指定是的索引下标,
        # 所以原来的标签维度必须加1,不然就会索引溢出
        self._ctc_blank = 0
        self.__lossfn = nn.CTCLoss(blank=self._ctc_blank)

        # 不再关心特征具体是多少,有多少个标签就有多少个特征 
        # 为损失函数添加一个key,val 
        self._word2id, self._id2word = word2id,id2word 
        nword = len(self._word2id) 
        if tmp_dir:
            dict_fil = os.path.join(tmp_dir,"model_word2id.wid")
            write(self._word2id,dict_fil)

        # 多的1为nn.CTCLoss的空白字符的ID
        # 最后的维度
        self._out_channels_last = nword 

        self._model = model 
        self._model_path = ""
        self._minloss  = 1000000 
        self._currentloss = 0
        
    def parameters(self):
        return self._model.parameters()

    def train(self):
        self._model.train()

    def eval(self):
        self._model.eval()

    def forward(self, x):
        """ 
        输入x:[T, B, C] 
        """ 
        T, B, C = x.shape 
        if self._init_h0:
            y = self._model(x,self._h0)  
        else:
            y = self._model(x)  
        return y 

    def loss_step(self,x, d, nx, nd):
        """
        损失函数计算,最保留最小损失函数的值 
        """
        
        y = self.forward(x)
        logp = self.__logSoftmax(y)
        loss = self.__lossfn(logp, d, nx, nd)
        loss.backward()
        self._currentloss = loss 


        if torch.lt(loss, self._minloss):
            self._minloss = loss 
            # print("more small:",loss)
        return loss,y

    def save(self,model_name=None):
        """
        在执行文件同目录下创建module目录,模型保存于该目录,按小时保存
        """
        
        if not model_name:
            tim = time.strftime('%Y%m%d_%H',time.localtime(time.time()))
            model_name = "model_"+tim+".ml"
            

        pdir = os.path.dirname(os.path.abspath(__file__))
        module_dir = os.path.join(pdir,"module")
        mkdir(module_dir)
        module_file = os.path.join(module_dir,model_name)
        
        torch.save(self._model.state_dict(), module_file)
        self._model_path =  module_file

    def save_minloss(self, model_name=None,threshold_loss = 10):
        """
        如果损失函数变小一次才保存,也就是说损失函数变大时不保存；最后的保存结果是模型中损失函数最小的模型 
        """
        if torch.le(self._currentloss, self._minloss) and torch.lt(self._currentloss, threshold_loss):
            self.save(model_name)
            print("save model {} ,loss :{}".format(self._model_path,self._currentloss))



    def label_from_y(self,y,label=False):
        """"
        取第3维中最大数的索引下标,用于解码字符, 
        y的维度与标签维度一致,索引下标顺序与标签ID一致,
        故下面的处理相当于解码字符 ,
        """
        print("字库长度:",len(self._word2id))

        if not label:
            with torch.no_grad():
                # 取第3维中最大数的索引下标,用于解码字符 
                # y的维度与标签维度一致,索引下标顺序与标签ID一致
                # 故下面的处理相当于解码字符 
                y = torch.argmax(y, 2)
        y = y.detach().cpu().numpy() 
        y = np.reshape(y, [-1])

        blank = self._ctc_blank 
        # blank = len(self._word2id)
        if len(self._id2word) <1 :
            id2word = {}
            for key in self._word2id:
                id2word[self._word2id[key]] = key 
            
            id2word[blank] = "-"
            self._id2word = id2word 

        i_pre = blank 
        words = []
        for i in y:

            if label:
                words.append(self._id2word[i])
            else:
                # 去重,去掉重要的字 
                if i==i_pre:
                    # print("-")
                    continue 
                else:
                    if i!=blank:
                        words.append(self._id2word[i])
                    i_pre = i

        return words 




