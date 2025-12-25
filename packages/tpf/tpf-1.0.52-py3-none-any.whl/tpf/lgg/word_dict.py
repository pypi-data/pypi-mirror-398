
import os,csv 
import jieba 

ai_words_path = "/source/aisty/73_code/aisty/case/AI知识库/data/word-dict.csv"
film_words_path = "/source/aisty/73_code/aisty/dataset/word_dict/film.csv"
common_words_path = "/source/aisty/73_code/aisty/dataset/word_dict/common.csv"
person = "/source/aisty/73_code/aisty/dataset/word_dict/person.csv"

def get_words(word_dict_path):
    word_pos = {}
    aipos = []   # 自定义AI词性列表

    # 读取常用词典，并将之补充到jieba
    rows=csv.reader(open(word_dict_path,'r',encoding='utf8'))
    for row in rows:
        if len(row)==2:
            word = row[0].strip().replace(" ","")
            pos = row[1].strip()
            aipos.append(pos)
            word_pos[word] = pos
    
    return word_pos

def ai_words():
    ai_dict = get_words(word_dict_path=ai_words_path)

    answer_path = "/source/aisty/73_code/aisty/case/AI知识库/data/answer"
    word_pos = {}
    aipos = []   # 自定义AI词性列表

    # 读取原始文件单词与词性
    for fil in os.listdir(answer_path):
        if not "original.txt" in fil:
            with open(os.path.join(answer_path,fil),'r', encoding='utf8') as f:
                for line in f:
                    ll = line.split(sep=",")
                    if len(ll) == 2 :
                        word = ll[0].strip().replace(" ","")
                        pos = ll[1].strip()
                        aipos.append(pos)
                        word_pos[word] = pos 
            

    ai_dict.update(word_pos)

    return ai_dict

def film_word():
    return get_words(word_dict_path=film_words_path)

def common_word():
    return get_words(word_dict_path=common_words_path)

def all_word():
    d1 = ai_words()
    d2 = get_words(word_dict_path=film_words_path)
    d3 = get_words(word_dict_path=common_words_path)
    d4 = get_words(word_dict_path=person)
    d1.update(d2)
    d1.update(d3)
    d1.update(d4)
    return d1 

def add_words(word_pos):
    # 将读取到的单词与词性补充到jieba
    for word,pos in word_pos.items():
        # 要保证word中没有空格，否则jieba会优先按空格拆分单词
        # 即使suggest_freq也没有用
        jieba.add_word(word=word,tag=pos)
        jieba.suggest_freq(word)

