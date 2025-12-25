
import re,os,json 
import jieba.posseg as pseg
from collections import Counter
from typing import List, Dict, Tuple, Optional, Set

import jieba     
import pandas as pd 
import numpy as np
from tpf.conf import pc  
pc.set_log_path("/tmp/tousu.log")

class Word:
    def __init__(self) -> None:
        self.jieba = jieba 
        

    @staticmethod
    def add_jieba_dict(data=None, cols=[], save_path=None):
        """追加列的不重复值到jieba字典
        """
        # 将labels写入save_path文件，一行一个label，后续作为jieba自定义单词字典使用
        if cols and len(cols)>0:
            labels = []
            for lb in cols:
                ll = data[lb].unique().tolist()
                labels.extend(ll)

            # 写入labels到文件，一行一个label
            if save_path:
                # 读取现有文件内容
                existing_labels = set()
                try:
                    with open(save_path, 'r', encoding='utf-8') as f:
                        for line in f:
                            line = line.strip()
                            if line:
                                existing_labels.add(line)
                    print(f"从{save_path}读取了{len(existing_labels)}个现有labels")
                except FileNotFoundError:
                    print(f"{save_path}不存在，将创建新文件")

                # 合并并去重
                all_labels = set(labels) | existing_labels

                # 覆盖式写入文件
                with open(save_path, 'w', encoding='utf-8') as f:
                    for label in sorted(all_labels):
                        f.write(str(label) + '\n')
                print(f"已将{len(all_labels)}个去重后的labels写入{save_path}（新增{len(set(labels) - existing_labels)}个）")
                jieba.load_userdict(save_path)
        elif save_path:   
            jieba.load_userdict(save_path)
        




class TextPreDeal:
    """
    投诉文本预处理类
    提供6级标签投诉文本分类项目的完整文本预处理功能
    """

    def __init__(self,
                 custom_stopwords: List[str] = None,
                 allowed_pos: Set[str] = None,
                 use_custom_dict: bool = True,
                 min_word_length: int = 1):
        """
        初始化文本预处理器

        Args:
            custom_stopwords: 自定义停用词列表
            allowed_pos: 允许的词性集合
            use_custom_dict: 是否使用自定义词典
            min_word_length: 最小词长度
        """
        # 初始化停用词表 - 移除重要的否定词和语气词
        self.base_stopwords = [
            "的", "了", "在", "是", "我", "有", "和", "就", "人", "都", "一", "一个", "上", "也", "到", "说", "要", "去", "你", "会", "着", "看", "自己", "这", "那", "她", "他", "它", "们", "嗯嗯"
        ]

        # 重要保留词：否定词、语气词、程度副词（从停用词中移除）
        self.important_words = {
            "不", "没有", "无", "未", "别", "勿", "莫", "毫", "绝非", "并非", "决不",
            "很", "非常", "太", "极", "超", "特别", "格外", "尤其", "十分", "相当",
            "吗", "呢", "啊", "吧", "哦", "嗯", "哈", "呵", "唉", "嗨", "哎",
            "还", "还是", "又", "再", "也", "都", "只", "就", "才", "却"
        }

        # 投诉领域专用停用词 - 移除可能包含重要语义的词
        self.complaint_stopwords = [
            "公司", "用户", "投诉", "反馈", "请问", "你好", "谢谢", "客服", "坐席", "工号",
            "解释", "建议", "回复", "情况", "记录", "信息", "内容", "相关", "以下", "上述", "所说", "所述"
        ]

        # 个人信息相关停用词
        self.personal_info_stopwords = [
            "[姓名]", "[手机号]", "[日期]", "[时间]", "[地点]", "[金额]", "客户姓名", "被投诉", "投诉当的", "大概时间", "来电号码", "手机号码", "电话号码"
        ]

        self.custom_stopwords = custom_stopwords or []
        self.stopwords = set(self.base_stopwords + self.complaint_stopwords +
                            self.personal_info_stopwords + self.custom_stopwords)

        # 默认允许的词性：名词、动词、形容词、副词
        self.allowed_pos = allowed_pos or {'n', 'v', 'a', 'd', 'vn', 'an', 'vd'}

        self.min_word_length = min_word_length
        self.use_custom_dict = use_custom_dict

        # 加载自定义词典（如果需要）
        if self.use_custom_dict:
            self._load_custom_dict()

    def _load_custom_dict(self):
        """加载投诉领域自定义词典"""
        complaint_keywords = [
            "逾期", "征信", "贷款", "还款", "催收", "利息", "费用", "罚款",
            "消除", "撤销", "取消", "调取", "录音", "核实", "处理", "解决",
            "不满", "投诉", "举报", "申诉", "投诉", "反馈", "建议", "意见",
            "服务", "态度", "质量", "效率", "专业", "及时", "响应", "解答",
            "银行卡", "信用卡", "借记卡", "网银", "手机银行", "ATM", "柜台",
            "账户", "余额", "流水", "交易", "转账", "汇款", "支付", "收款",
            "理财", "基金", "保险", "股票", "债券", "投资", "收益", "风险",
            "个人贷款", "房屋贷款", "汽车贷款", "消费贷款", "经营贷款", "信用贷款",
            "催收", "催款", "催账", "讨债", "追债", "清收", "核销", "坏账",
            "利率", "利息", "罚息", "复利", "年化", "月供", "分期", "期供",
            "逾期", "违约", "失信", "黑名单", "征信报告", "信用记录", "不良记录",
            "银行", "金融机构", "客服中心", "营业网点", "分支机构", "总行"
        ]

        for word in complaint_keywords:
            jieba.add_word(word)

    def clean_text(self, text: str) -> str:
        """
        文本清洗

        Args:
            text: 原始文本

        Returns:
            清洗后的文本
        """
        if not isinstance(text, str):
            return ""

        # 移除HTML标签
        text = re.sub(r'<[^>]+>', '', text)

        # 移除URL
        text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)

        # 移除邮箱
        text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '', text)

        # 移除电话号码（保留投诉中的[手机号]占位符）
        text = re.sub(r'(?<!\[)[1][3-9]\d{9}(?!\])', '', text)

        # 移除身份证号
        text = re.sub(r'\b\d{17}[\dXx]\b', '', text)

        # 移除银行卡号
        text = re.sub(r'\b\d{16,19}\b', '', text)

        # 保留中文、英文、数字和基本标点
        text = re.sub(r'[^\u4e00-\u9fff\w\s，。！？；：""''（）【】《》、]', '', text)

        # 移除多余空格和换行
        text = re.sub(r'\s+', ' ', text).strip()

        return text

    def normalize_text(self, text: str) -> str:
        """
        文本标准化

        Args:
            text: 输入文本

        Returns:
            标准化后的文本
        """
        if not isinstance(text, str):
            return ""

        # 全角转半角
        text = text.replace('（', '(').replace('）', ')')
        text = text.replace('，', ',').replace('。', '.')
        text = text.replace('！', '!').replace('？', '?')
        text = text.replace('；', ';').replace('：', ':')

        # 英文大小写统一（小写）
        text = text.lower()

        # 移除重复字符（如：非常好 -> 很好）
        text = re.sub(r'(.)\1{2,}', r'\1\1', text)

        return text

    def segment_text(self, text: str, use_pos_filter: bool = True) -> List[str]:
        """
        文本分词

        Args:
            text: 输入文本
            use_pos_filter: 是否使用词性过滤

        Returns:
            分词结果列表
        """
        if not isinstance(text, str) or not text.strip():
            return []

        # 分词及词性标注
        words_with_pos = pseg.lcut(text)

        # 过滤处理
        filtered_words = []
        for word, pos in words_with_pos:
            # 优先保留重要词汇（否定词、语气词、程度副词）
            if word in self.important_words:
                filtered_words.append(word)
                continue

            # 跳过停用词
            if word in self.stopwords:
                continue

            # 跳过过短词汇
            if len(word) < self.min_word_length:
                continue

            # 跳过纯数字和纯符号
            if word.isdigit() or not re.search(r'[\u4e00-\u9fff]', word) and len(word) == 1:
                continue

            # 词性过滤
            if use_pos_filter:
                pos_first = pos[0].lower()
                if pos_first not in {p[0] for p in self.allowed_pos}:
                    continue

            filtered_words.append(word)

        return filtered_words

    def extract_ngrams(self, words: List[str], n: int = 2) -> List[str]:
        """
        提取N-gram特征

        Args:
            words: 词语列表
            n: n-gram的n值

        Returns:
            n-gram列表
        """
        if len(words) < n:
            return []

        ngrams = []
        for i in range(len(words) - n + 1):
            ngram = ''.join(words[i:i+n])
            ngrams.append(ngram)

        return ngrams

    def preprocess_text(self, text: str,
                       use_ngram: bool = False,
                       ngram_range: Tuple[int, int] = (2, 3)) -> List[str]:
        """
        完整文本预处理流程

        Args:
            text: 原始文本
            use_ngram: 是否使用n-gram
            ngram_range: n-gram范围

        Returns:
            处理后的词语列表
        """
        # 1. 文本清洗
        cleaned_text = self.clean_text(text)

        # 2. 文本标准化
        normalized_text = self.normalize_text(cleaned_text)

        # 3. 分词
        words = self.segment_text(normalized_text)

        # 4. N-gram处理
        if use_ngram and len(words) >= 2:
            ngrams = []
            for n in range(ngram_range[0], ngram_range[1] + 1):
                ngrams.extend(self.extract_ngrams(words, n))
            words.extend(ngrams)

        return words

    def analyze_label_keywords(self,
                             df: pd.DataFrame,
                             text_column: str,
                             label_column: str,
                             top_k: int = 20) -> Dict:
        """
        分析各标签下的高频词

        Args:
            df: 数据框
            text_column: 文本列名
            label_column: 标签列名
            top_k: 返回前k个高频词

        Returns:
            标签关键词字典
        """
        label_keywords = {}

        for label in df[label_column].unique():
            # 获取该标签下所有文本
            mask = df[label_column] == label
            texts = df.loc[mask, text_column]

            all_words = []
            for text in texts:
                words = self.preprocess_text(text)
                all_words.extend(words)

            # 统计词频
            word_freq = Counter(all_words).most_common(top_k)
            label_keywords[str(label)] = word_freq

            # print(f"标签 {label} 的高频词：")
            # for word, freq in word_freq:
            #     print(f"  {word}: {freq}")
            # print("-" * 50)

        return label_keywords

    def process_dataset(self,
                       df: pd.DataFrame,
                       text_column: str,
                       output_path: str = None,
                       use_ngram: bool = False) -> pd.DataFrame:
        """
        处理整个数据集

        Args:
            df: 输入数据框
            text_column: 文本列名
            output_path: 输出文件路径
            use_ngram: 是否使用n-gram

        Returns:
            处理后的数据框
        """
        print(f"开始处理数据集，共 {len(df)} 条记录...")

        # 创建处理后的文本列
        df['processed_text'] = df[text_column].apply(
            lambda x: ''.join(self.preprocess_text(x, use_ngram=use_ngram))
        )

        # 添加文本长度信息
        df['original_length'] = df[text_column].astype(str).apply(len)
        df['processed_length'] = df['processed_text'].astype(str).apply(len)
        df['word_count'] = df['processed_text'].astype(str).apply(lambda x: len(x.split()))

        # 保存结果
        if output_path:
            df.to_csv(output_path, index=False, encoding='utf-8')
            print(f"处理结果已保存到：{output_path}")

        # 打印统计信息
        print(f"\n预处理统计信息：")
        print(f"平均原始文本长度：{df['original_length'].mean():.2f}")
        print(f"平均处理后文本长度：{df['processed_length'].mean():.2f}")
        print(f"平均词汇数量：{df['word_count'].mean():.2f}")
        print(f"词汇数量为0的记录数：{(df['word_count'] == 0).sum()}")

        return df

    def save_stopwords(self, filepath: str):
        """保存停用词表到文件"""
        with open(filepath, 'w', encoding='utf-8') as f:
            for word in sorted(self.stopwords):
                f.write(word + '\n')
        print(f"停用词表已保存到：{filepath}")

    def load_stopwords(self, filepath: str):
        """从文件加载停用词表"""
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                new_stopwords = {line.strip() for line in f if line.strip()}
                self.stopwords.update(new_stopwords)
            print(f"已从 {filepath} 加载 {len(new_stopwords)} 个停用词")

    def get_text_stats(self, text: str) -> Dict:
        """
        获取文本统计信息

        Args:
            text: 输入文本

        Returns:
            文本统计字典
        """
        processed_words = self.preprocess_text(text)

        stats = {
            'original_length': len(text),
            'cleaned_length': len(self.clean_text(text)),
            'word_count': len(processed_words),
            'unique_word_count': len(set(processed_words)),
            'avg_word_length': np.mean([len(word) for word in processed_words]) if processed_words else 0
        }

        return stats


def test_optimization():
    """测试优化后的预处理效果"""
    print("=== 测试优化后的文本预处理效果 ===\n")

    # 初始化预处理器
    preprocessor = TextPreDeal(
        use_custom_dict=True,
        min_word_length=2
    )

    # 测试用例
    test_cases = [
        "[姓名]客户来电咨询之前的贷款具体下放时间，之前支行有工作人员联系，客户表示不认可，要求提供具体贷款时间，并且表示没有合理回复，客户表示要投诉协助处",
        "客户对服务态度非常不满意，要求立即处理",
        "银行系统异常，导致无法正常转账，客户很生气",
        "虽然客服解释了，但客户还是不理解，认为银行做法错误",
        "客户要求取消逾期记录，但银行表示不符合规定"
    ]

    for i, text in enumerate(test_cases, 1):
        print(f"测试用例 {i}:")
        print(f"原文: {text}")
        processed_words = preprocessor.preprocess_text(text)
        print(f"处理后: {''.join(processed_words)}")
        print("-" * 80)

def text_pre_deal(df=None, input_file = None, output_dir = "/tmp/",
                  use_ngram=False, show_demo=False,use_cols=['processed_text', 'label']):
    """文本预处理流程"""
    # 先测试优化效果
    # test_optimization()

    print("\n" + "="*80 + "\n")

    # 初始化预处理器
    preprocessor = TextPreDeal(
        use_custom_dict=True,
        min_word_length=2
    )

    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)

    # 读取数据
    print(f"读取数据文件：{input_file}")
    try:
        if df is None:
            df = pd.read_csv(input_file)
            print(f"数据读取成功，共 {len(df)} 条记录")
            print(f"列名：{df.columns.tolist()}")

            # 显示前几条数据
            print("\n原始数据示例：")
            print(df[['text']].head(3))

        # 分析各标签高频词
        if 'label' in df.columns:
            print("\n=== 分析各标签高频词 ===")
            label_keywords = preprocessor.analyze_label_keywords(
                df, text_column='text', label_column='label', top_k=15
            )

            # 保存标签关键词分析结果
            keywords_file = os.path.join(output_dir, 'label_keywords.json')
            with open(keywords_file, 'w', encoding='utf-8') as f:
                # 转换为可序列化的格式
                serializable_keywords = {
                    k: [{'word': w, 'freq': f} for w, f in v]
                    for k, v in label_keywords.items()
                }
                json.dump(serializable_keywords, f, ensure_ascii=False, indent=2)
            print(f"标签关键词分析结果已保存到：{keywords_file}")

        # 处理数据集
        print("\n=== 开始文本预处理 ===")

        # 输出文件路径
        output_file_basic = os.path.join(output_dir, 'processed_basic.csv')
        output_file_ngram = os.path.join(output_dir, 'processed_ngram.csv')

        if use_ngram:
            # 带N-gram的预处理
            processed_df_ngram = preprocessor.process_dataset(
                df.copy(),
                text_column='text',
                output_path=output_file_ngram,
                use_ngram=True
            )
            df = processed_df_ngram[use_cols]
        else:
            # 基础预处理
            processed_df_basic = preprocessor.process_dataset(
                df.copy(),
                text_column='text',
                output_path=output_file_basic,
                use_ngram=False
            )
            df = processed_df_basic[use_cols]
            
        # 保存停用词表
        stopwords_file = os.path.join(output_dir, 'stopwords.txt')
        preprocessor.save_stopwords(stopwords_file)

        if show_demo:
        # 文本统计示例
            print("\n=== 文本预处理效果示例 ===")
            sample_indices = [0, 1, 2] if len(df) >= 3 else range(len(df))

            for idx in sample_indices:
                original_text = df.iloc[idx]['text']
                processed_text = processed_df_basic.iloc[idx]['processed_text']
                stats = preprocessor.get_text_stats(original_text)

                print(f"\n样本 {idx + 1}:")
                print(f"原始文本：{original_text[:100]}...")
                print(f"处理后文本：{processed_text[:100]}...")
                print(f"统计信息：{stats}")

        print(f"\n=== 处理完成 ===")
        print(f"输出文件：")
        print(f"- 基础预处理：{output_file_basic}")
        print(f"- 带N-gram预处理：{output_file_ngram}")
        print(f"- 停用词表：{stopwords_file}")
        df.rename(columns={'processed_text': 'text'}, inplace=True)
        return df

    except Exception as e:
        print(f"处理过程中出现错误：{e}")
        import traceback
        traceback.print_exc()
    
    return None 



from rank_bm25 import BM25Okapi
import jieba

class BM25Reranker:
    def __init__(self, df=None, use_cols=['text','label'],texts=[],k1=1.8, b=0.75,score_name='score'):
        """初始化索引
        - 针对全体文本
        - use_cols:共有两个元素，第1个元素为文本列，第2个元素为标签列
        """
        if len(texts)==0:
            if df is None:
                raise Exception("texts为空时，请输入数据集df")
            self.text_name = use_cols[0]
            self.label_name = use_cols[1]
            self.score_name = score_name
            texts = df[use_cols[0]].tolist()
        self.df = df[use_cols]   
        # 对中文文档进行分词
        tokenized_texts = [jieba.lcut(text) for text in texts]
        self.tokenized_texts = tokenized_texts
        self.k1 = k1 
        self.b = b 
        self.bm25 = BM25Okapi(tokenized_texts, k1=k1, b=b)
        
    def epoch_cross_scores(self, sim_top_k=5, label_top_k=3, p_num=50,save_path=None):
        """计算BM25分数，按轮次
        - 每个轮次取第i行数据，对剩下的n-1行数据，计算BM25分数
        - 对于每个轮次来说，最终结果只有sim_top_k*label_top_k行数据
        """
        data = self.df.copy()
        data_len = len(self.tokenized_texts)
        pc.lg(f"data.columns: {data.columns.tolist()}")
        
        # 全局数据框列表，用于收集所有批处理结果
        df_results = []
        for i in range(data_len):
            new_query = data.iloc[i][self.text_name]
            label     = data.iloc[i][self.label_name]
            others    = data.drop(data.index[i])
            tokenized_query = self.tokenized_texts[i]
            tokenized_texts = [doc for j, doc in enumerate(self.tokenized_texts) if j != i]
            bm25 = BM25Okapi(tokenized_texts, k1=self.k1, b=self.b)
            # 第i行相对剩下n-1行的文本计算BM25分数
            others[self.score_name] = bm25.get_scores(tokenized_query)
            
            df3 = others.groupby('label').apply(
                lambda x: pd.Series({
                    self.text_name: x.nlargest(sim_top_k, self.score_name)[self.text_name].iloc[0],  # 取分数最高的第一个样本的text
                    self.label_name: x.name,
                    'mean_score': x.nlargest(sim_top_k, self.score_name)[self.score_name].mean()  # 计算前5个分数的均值
                }),
                include_groups=False
            ).reset_index(drop=True)

            # 按mean_score降序排列
            df3_sorted = df3.sort_values('mean_score', ascending=False)
            label_topk = df3_sorted[:label_top_k]
            label_topk = label_topk[[self.label_name, 'mean_score']]
            labels = label_topk[self.label_name].tolist()
            
            df_topk = others[others[self.label_name].isin(labels)]
            
            df_result_list = []
            for label in labels:
                # 筛选当前label的数据
                label_data = df_topk[df_topk[self.label_name] == label]
                # 按score降序排序并取前sim_top_k条
                top_similar = label_data.nlargest(sim_top_k, self.score_name)
                df_result_list.append(top_similar)

            # 合并所有结果
            if df_result_list:
                df_topk = pd.concat(df_result_list, axis=0, ignore_index=True)
            df_topk=df_topk.merge(label_topk, on=self.label_name,how='left')
            df_topk = df_topk.rename(columns={self.text_name: 'sim_text'})
            
             # 添加真实标签和重命名标签列
            df_topk['real_label'] = label
            df_topk['query_text'] = new_query
            df_topk = df_topk.rename(columns={self.label_name: 'sim_label','score':'sim_score'})
            # pc.lg(f"df_topk.columns: {df_topk.columns.tolist()}")
            # print(f"df_topk.columns: {df_topk.columns.tolist()}")
            # pc.lg(f"df_topk.shape: {df_topk.shape}")
            # 将当前结果添加到全局列表
            df_results.append(df_topk)
            if i%p_num == 0 or i==data_len-1:
                print(f"处理第{i+1}/{data_len}条数据，单条sim_label数量: {len(df_topk)}")

        # 按行拼接所有结果
        if df_results:
            df_final = pd.concat(df_results, axis=0, ignore_index=True)
            print(f"批量处理完成，总计处理{data_len}条查询，返回{len(df_final)}条结果")
            if save_path is not None:
                df_final.to_csv(save_path, index=False, encoding='utf-8-sig')
                print(f"保存CSV文件到: {save_path}")
                print(f"记录数: {len(df_final)}")
                print(f"字段数: {len(df_final.columns.tolist())}")
            return df_final
        else:
            print("未处理任何数据，返回空数据框")
            return pd.DataFrame() 
        
            
    def sim_scores(self, new_query):
        """计算相似度： 对于新的投诉文本，分词后使用 get_scores 方法即可得到它与已有文本的BM25相似度分数
        """
        tokenized_query = jieba.lcut(new_query)
        scores = self.bm25.get_scores(tokenized_query)
        return scores
    
    
    def label_topk(self, new_query, sim_top_k=5, label_top_k=3, outdir=""):
        """
        处理BM25分数，计算每个标签前sim_top_k个样本的均值分数

        Args:
            df: 原始数据框，包含text, label, label_text_count列
            sim_top_k: top k个相似分数
            label_top_k: top k个标签

        Returns:
            df3_sorted: 按mean_score降序排列的数据框
            
        Out Files:
            bm25_scores.csv: 原始分数
            bm25_scores_mean5.csv: 按mean_score降序排列的数据
        """
        
        # 添加分数列
        self.df[self.score_name] = self.sim_scores(new_query)

        # 保存原始分数
        bm25_path = os.path.join(outdir, "bm25_scores.csv")
        self.df.to_csv(bm25_path, index=False)

        df2 = self.df 

        # 按标签分组，取每个标签分数最高的前5个样本的均值
        df3 = df2.groupby('label').apply(
            lambda x: pd.Series({
                self.text_name: x.nlargest(sim_top_k, self.score_name)[self.text_name].iloc[0],  # 取分数最高的第一个样本的text
                self.label_name: x.name,
                'mean_score': x.nlargest(sim_top_k, self.score_name)[self.score_name].mean()  # 计算前5个分数的均值
            }),
            include_groups=False
        ).reset_index(drop=True)

        # 按mean_score降序排列
        df3_sorted = df3.sort_values('mean_score', ascending=False)

        # 保存结果
        df3_path = os.path.join(outdir, "bm25_scores_mean5.csv")
        df3_sorted.to_csv(df3_path, index=False)

        return df3_sorted[:label_top_k]

    
    def data_topk(self, new_query, sim_top_k=5, label_top_k=3,outdir=""):
        #与new_query相似的标签
        label_topk = self.label_topk(new_query, sim_top_k, label_top_k,outdir=outdir)
        label_topk = label_topk[[self.label_name, 'mean_score']]
        labels = label_topk[self.label_name].tolist()
        
        df = self.df.copy()
        # 添加分数列,df的text为相似的文本,而非新的文本new_query
        df[self.score_name] = self.sim_scores(new_query)
        df_topk = df[df[self.label_name].isin(labels)]

        # 对df_topk中每个label下按score降序排序，取前sim_top_k条数据
        df_result_list = []
        for label in labels:
            # 筛选当前label的数据
            label_data = df_topk[df_topk[self.label_name] == label]
            # 按score降序排序并取前sim_top_k条
            top_similar = label_data.nlargest(sim_top_k, self.score_name)
            df_result_list.append(top_similar)

        # 合并所有结果
        if df_result_list:
            df_topk = pd.concat(df_result_list, axis=0, ignore_index=True)
        df_topk=df_topk.merge(label_topk, on=self.label_name,how='left')
        df_topk = df_topk.rename(columns={self.text_name: 'sim_text'})
        return df_topk
         

    def data_topk_batch(self, df, sim_top_k=5, label_top_k=3,p_num=50,outdir=""):
        """
        批量处理数据，返回所有结果的拼接数据框

        Args:
            df: 输入数据框，第1列为text，第2列为label
            sim_top_k: 相似度top_k
            label_top_k: 标签top_k

        Returns:
            pd.DataFrame: 按行拼接所有df_tmp的结果
        """
        # 全局数据框列表，用于收集所有批处理结果
        df_results = []
        df_len = len(df)

        # 遍历输入数据的每一行
        for i, tup in enumerate(df.itertuples(index=False)):   # index=True 把索引也带出来
            new_query = tup[0]
            
            # 调用data_topk方法获取单个查询的结果
            df_tmp = self.data_topk(new_query, sim_top_k=sim_top_k, label_top_k=label_top_k,outdir=outdir)

            # 添加真实标签和重命名标签列
            if len(tup)>1:
                label = tup[1]
                df_tmp['real_label'] = label
            df_tmp['query_text'] = new_query
            df_tmp = df_tmp.rename(columns={self.label_name: 'sim_label','score':'sim_score'})

            # 添加批次信息，便于追踪
            df_tmp['batch_index'] = i

            # 将当前结果添加到全局列表
            df_results.append(df_tmp)
            if i%p_num == 0 or i==df_len-1:
                print(f"处理第{i+1}/{len(df)}条数据，单条sim_label数量: {len(df_tmp)}")

        # 按行拼接所有结果
        if df_results:
            df_final = pd.concat(df_results, axis=0, ignore_index=True)
            print(f"批量处理完成，总计处理{len(df)}条查询，返回{len(df_final)}条结果")
            return df_final
        else:
            print("未处理任何数据，返回空数据框")
            return pd.DataFrame() 

class NLP:
    def __init__(self):
        self.t5_model = None 
        self.t5_tokenizer = None 
        self.t5_device = 'cpu'
        self.nlp = None

    def init_t5(self, model_path='/wks/models/t5_summary_en_ru_zh_base_2048', device='cpu'):
        self.t5_device = device
        from modelscope import T5ForConditionalGeneration, T5Tokenizer
        model = T5ForConditionalGeneration.from_pretrained(model_path)
        model.eval()
        model.to(device)
        generation_config = model.generation_config
        # for quality generation
        generation_config.length_penalty = 0.6
        generation_config.no_repeat_ngram_size = 2
        generation_config.num_beams = 10
        
        tokenizer = T5Tokenizer.from_pretrained(model_path)
        self.t5_tokenizer = tokenizer 
        self.t5_model = model
        self.t5_generation_config = generation_config
        
    def summary_t5(self, text, limit_len=200):
        """
        使用T5模型生成文本摘要

        参数:
        text: 输入文本
        limit_len: 长度限制，如果文本长度超过此值则进行摘要生成，否则返回原文本

        返回:
        str: 摘要结果或原文本
        """
        # 检查文本长度，如果不超过限制则直接返回原文本
        if len(text) <= limit_len:
            return text

        if self.t5_model is None:
            self.init_t5()

        # text summary generate
        prefix = 'summary to zh: '
        src_text = prefix + text
        input_ids = self.t5_tokenizer(src_text, return_tensors="pt")

        generated_tokens = self.t5_model.generate(**input_ids.to(self.t5_device), generation_config=self.t5_generation_config)

        result = self.t5_tokenizer.batch_decode(generated_tokens, skip_special_tokens=True)

        # 返回第一个结果（通常只有一个摘要结果）
        return result[0] if result else text
    
    def summary_hanlp(self,text,top_n=8, limit_len=200):
        if self.nlp is None:
            self.nlp = TLP()
        # 检查文本长度，如果不超过限制则直接返回原文本
        if len(text) <= limit_len:
            return text
        ss = self.nlp.summary_str(text,top_n=top_n)
        return ss

nlp = NLP()
# 尝试导入pyhanlp，如果未安装则设为None
try:
    from pyhanlp import HanLP
    PYHANLP_AVAILABLE = True
except ImportError:
    HanLP = None
    PYHANLP_AVAILABLE = False


class TLP:
    def __init__(self) -> None:
        
        pass 
    
    @staticmethod
    def cut_words(text):
        """使用结巴分词对文本进行分词
        """
        words = jieba.cut(text, cut_all=False)
        return words 
    
    @staticmethod
    def summary_str(text,top_n=8):
        summary_sentences = HanLP.extractSummary(text,top_n)
        st =""
        for sentence in summary_sentences:
            st += sentence+","
        st = st.removesuffix(",")
        return st
    
    @staticmethod
    def summary(text, n=5):
        """使用HanLP进行文本摘要

        Args:
            text (str): 待摘要的文本
            n (int): 返回的摘要数量

        Returns:
            list: 摘要列表，如果pyhanlp未安装则返回空列表
        """
        if not PYHANLP_AVAILABLE:
            print("警告: pyhanlp未安装，无法使用HanLP进行文本摘要")
            return []

        try:
            # 使用HanLP进行摘要
            summary_result = HanLP.extractSummary(text, n)
            return [str(item) for item in summary_result]
        except Exception as e:
            print(f"HanLP摘要失败: {e}")
            return []

    @staticmethod
    def segment(text):
        """使用HanLP进行分词

        Args:
            text (str): 待分词的文本

        Returns:
            list: 分词结果，如果pyhanlp未安装则返回空列表
        """
        if not PYHANLP_AVAILABLE:
            print("警告: pyhanlp未安装，无法使用HanLP进行分词")
            return []

        try:
            # 使用HanLP进行分词
            segment_result = HanLP.segment(text)
            return [str(item) for item in segment_result]
        except Exception as e:
            print(f"HanLP分词失败: {e}")
            return [] 