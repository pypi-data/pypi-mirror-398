
import numpy as np 
import random
import pandas as pd 
import string

from tpf.box.fil import parentdir
from tpf.box.fil import iswin

from datetime import datetime, timedelta
import random
import logging


# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


import random
import string

def random_str(n):
    """随机字符(仅数字与字母)
    - n:表示字符串长度为n
    """
    # 定义可能的字符集：数字 + 小写字母 + 大写字母
    characters = string.ascii_letters + string.digits
    # 使用列表推导式和 random.choice 从字符集中随机选择字符
    random_characters = [random.choice(characters) for _ in range(n)]
    # 将列表转换为字符串（如果需要）
    random_string = ''.join(random_characters)
    return random_string

def random_str_numpy(n):
    """随机字符(仅数字与字母),numpy生成
    - n:表示字符串长度为n
    """
    characters = string.ascii_letters + string.digits
    indices = np.random.choice(len(characters), n, replace=True)
    random_characters = [characters[i] for i in indices]
    random_string = ''.join(random_characters)
    return random_string


# 定义生成随机字符串的函数
def random_str_lower(length=3):
    """定义生成随机字符串的函数
    """
    # 生成一个由小写字母和数字组成的随机字符串
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))
    
def random_str_p(seq_len=(1,3)):
    """随机生成seq_len[0]到 seq_len[1]长度的字符串
    - 字符串由字母与数字组成

    """
    # 单词集合，对应键盘上的字母
    words = [
        '0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 
        'q', 'w', 'e', 'r',  't', 'y',  'u', 'i', 'o', 'p', 
        'a', 's', 'd', 'f',  'g', 'h',  'j', 'k', 'l', 
        'z', 'x', 'c', 'v',  'b', 'n',  'm'
    ]
        
    # 每个词被选中的概率，随机初始化的概率
    # p = np.array([
    #     1, 2, 3, 4, 5, 6, 7, 8, 9, 10,
    #     1,   2,  3,  4,  5,  6,  7,  8,  9, 10,
    #     11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26
    # ])
    p = np.random.randint(low=1, high=100, size=len(words), dtype=int)
    
    # 转概率，所有单词的概率之和为1
    _p = p / p.sum()
    
    # 随机选n个词
    # Return random integer in range [a, b], including both end points.
    _n = random.randint(seq_len[0], seq_len[1])

    _x = np.random.choice(words, size=_n, replace=True, p=_p)

    return "".join(_x)

def random_str_list(n=5,seq_len=(1,3)):
    """生成字符串列表
    """
    tmp = []
    for i in range(n):
        tmp.append(random_str_p(seq_len))
    return tmp 


def random_yyyymmdd():
    """随机生成日期,从2000年起
    - 格式：yyyy-mm-dd
    """
    from datetime import datetime, timedelta
    # 定义日期的起始和结束年份（如果需要）
    start_year = 2000
    end_year = datetime.now().year
    
    # 生成随机的年份
    year = random.randint(start_year, end_year)
    
    # 生成随机的月份
    month = random.randint(1, 12)
    
    # 生成随机的天数（注意每个月的天数不同）
    # 使用calendar模块可以帮助我们确定每个月的天数，但这里为了简单起见，我们使用datetime的date方法结合try-except来处理非法日期
    day = random.randint(1, 28)  # 先假设一个月最多28天
    
    while True:
        try:
            # 尝试创建日期对象
            random_date = datetime(year, month, day)
            # 如果成功，则跳出循环
            break
        except ValueError:
            # 如果日期非法（比如2月30日），则增加天数并重试
            day += 1
            if day > 28:  # 如果超过28天还未成功，则重置为1并从新月的天数开始检查（这里可以更加优化，比如根据月份确定最大天数）
                day = 1
                # 注意：这个简单的重置逻辑在跨月时可能不正确，因为它没有考虑到不同月份的天数差异。
                # 一个更准确的做法是使用calendar模块来确定每个月的最大天数。
                # 但为了简洁起见，这里我们假设用户不会频繁生成跨月的随机日期，或者接受偶尔的非法日期重试。
                # 在实际应用中，应该使用更精确的逻辑来确定每个月的最大天数。
                # 然而，为了这个示例的完整性，我们在这里保留这个简单的重置逻辑，并指出其潜在的不足。
    
    # 实际上，上面的while循环和重置逻辑是不完美的。下面是一个更准确的做法：
    from calendar import monthrange
    
    # 生成随机的天数（使用monthrange来确定每个月的最大天数）
    day = random.randint(1, monthrange(year, month)[1])
    random_date = datetime(year, month, day)
    
    # 格式化日期为"YYYY-MM-DD"
    formatted_date = random_date.strftime("%Y-%m-%d")
    return formatted_date


def data_sample_small(x, y, batch_size=1):
    '''下采样
    从原样本中随机取出部分数据

    batch_size为取出的行数
    0表示全部数据


    from data_sample import data_sample_small

    X_train = [[1,2],[1,2],[1,2]]

    y_train = [1,2,3]

    X_train = np.array(aa)

    y_train = np.array(b)


    X_train, y_train = data_sample_small(X_train, y_train, batch_size=16)

    print(X_train)
    
    print(y_train)
    '''
    
    x_row_count = len(x)
    if batch_size > x_row_count or batch_size == 0:
        return x, y

    #  随机取batch_size个不重复索引下标
    index_list =  random.sample(range(x_row_count), batch_size) 
    x_samll = [0 for x in range(len(index_list))]
    y_samll = [0 for x in range(len(index_list))]
    
    for i,elem in enumerate(index_list):
        x_samll[i] = x[elem]
        y_samll[i] = y[elem]
        
    return np.array(x_samll), np.array(y_samll)


def pd1(row_num):
    x = np.random.normal(0,1,[row_num,1])
    y = 0.3*x + 0.7

    x1 = pd.DataFrame(x,columns=list("A"))
    y1 = pd.DataFrame(y,columns=list("B"))

    data1 = pd.concat([x1,y1],axis=1)
    return data1

def pd2(row_num):
    x = np.random.normal(0,1,[row_num,1])
    y1 = 0.3*x + 0.7
    y2 = 1.2 * x**2 - 0.3*x + 0.7

    x1 = pd.DataFrame(x,columns=list("A"))
    y1 = pd.DataFrame(y1,columns=list("B"))
    y2 = pd.DataFrame(y2,columns=list("C"))

    data1 = pd.concat([x1,y1,y2],axis=1)
    return data1



def data_numpy2(row_num):
    """
    返回指定行数的两组数据
    y = x**2 + 2x + 1 , 多特征时sum求和
    x 为两列, 表示数据，符合标准正态分布 
    y 为一行，表示标签
    """
    np.random.seed(111)
    x = np.random.randn(row_num, 2)
    # print(len(x))
    # print(x[:1])  # [[-1.13383833  0.38431919]]
    y = []
    for i in range(len(x)):
        d = x[i]**2 + 2*x[i] + 1
        y.append(np.sum(d))
    # print(y[:3])  # [1.9342523289452673, 6.648312741121465, 0.3373482907093769]
    return x, y


# 梯度下降多项式模型数据生成
def sgd111(row_num=1000000, col_num=3):
    """梯度下降多项式模型数据生成
    随机系数与随机样本相乘再求和，得到一批训练集与测试集
    生成几行几列的训练集测试集数据
    默认100万行数据，每行3个特征
    """
    np.random.seed(111)

    X_train = np.random.normal(0, 1, [row_num, col_num])

    theta0 = 0.01
    theta = np.random.rand(col_num)
    # theta_real.append(theta0)
    # for i in range(col_num):
    #     theta_real.append(theta[i])
    # print("theta:", theta0, theta)
    y_train = theta * X_train + theta0 + np.random.normal(0, 0.1, [row_num, col_num])

    X_test = np.random.normal(1, 1, [row_num, col_num])
    y_test = theta * X_test + theta0

    ll = len(X_train)
    y_train_new = []
    y_test_new = []

    # y定为sum的一半，也可以定为别的
    for i in range(ll):
        y_train_new.append(np.sum(y_train[i]))
        y_test_new.append(np.sum(y_test[i]))

    y_train_new = np.array(y_train_new)
    y_test_new = np.array(y_test_new)

    return X_train, X_test, y_train_new, y_test_new




def random_yyyymmdd(dt_format="%Y-%m-%d"):
    """随机日期，从2000年以来的日期
    - 格式：yyyy-mm-dd 
    """
    from datetime import datetime, timedelta
    # 定义日期的起始和结束年份（如果需要）
    start_year = 2000
    end_year = datetime.now().year
    
    # 生成随机的年份
    year = random.randint(start_year, end_year)
    
    # 生成随机的月份
    month = random.randint(1, 12)
    
    # 生成随机的天数（注意每个月的天数不同）
    # 使用calendar模块可以帮助我们确定每个月的天数，但这里为了简单起见，我们使用datetime的date方法结合try-except来处理非法日期
    day = random.randint(1, 28)  # 先假设一个月最多28天
    
    while True:
        try:
            # 尝试创建日期对象
            random_date = datetime(year, month, day)
            # 如果成功，则跳出循环
            break
        except ValueError:
            # 如果日期非法（比如2月30日），则增加天数并重试
            day += 1
            if day > 28:  # 如果超过28天还未成功，则重置为1并从新月的天数开始检查（这里可以更加优化，比如根据月份确定最大天数）
                day = 1
                # 注意：这个简单的重置逻辑在跨月时可能不正确，因为它没有考虑到不同月份的天数差异。
                # 一个更准确的做法是使用calendar模块来确定每个月的最大天数。
                # 但为了简洁起见，这里我们假设用户不会频繁生成跨月的随机日期，或者接受偶尔的非法日期重试。
                # 在实际应用中，应该使用更精确的逻辑来确定每个月的最大天数。
                # 然而，为了这个示例的完整性，我们在这里保留这个简单的重置逻辑，并指出其潜在的不足。
    
    # 实际上，上面的while循环和重置逻辑是不完美的。下面是一个更准确的做法：
    from calendar import monthrange
    
    # 生成随机的天数（使用monthrange来确定每个月的最大天数）
    day = random.randint(1, monthrange(year, month)[1])
    random_date = datetime(year, month, day)
    
    # 格式化日期为"YYYY-MM-DD"
    formatted_date = random_date.strftime(dt_format)
    return formatted_date



import datetime
import numpy as np

class TimeGen():
    def __init__(self):
        """
        examples
        -----------------------------------------------
        from tpf.data.make import TimeGen
        tg = TimeGen()
        ts = tg.year1_ymh(count=30000)
        ts[:3],len(ts)
        
        (['2025-06-21 18:31:58', '2025-06-21 18:28:00', '2025-06-21 18:28:00'], 30000)
        
        """
        pass

    def _minute_one_year(self, minute_min=10, minute_max=24*60*30, count=None):
        """年交易时间数据：分钟列表，
        - 依据该分钟列表，按时间相减，可得出一系列日期
        - minute_month:最小单位为分钟,minute_bymonth为一个月的分钟数
        - count_month:一个月的交易笔数
        - 伪算法
            - 以1年的总分钟数为最大尺度，10分钟为最小尺度,取一定数量的随机数
            - 每月随机发生count_month笔交易
        """
        minute_month = 24*60*30
        if count is None:
            count_month = np.random.randint(low=0,high=100)
            count_year = count_month*12
            count = count_year
        a=np.random.randint(low=minute_min, high=minute_month, size=count)
        a.sort()
        return a.tolist()
    
    def _ymdhms_time(self, minute_list, max_count=10, dt_format='%Y-%m-%d %H:%M:%S'):
        """根据分钟列表，从当前日期开始生成一系列日期
        - 返回 
            - %Y-%m-%d %H:%M:%S格式 日期字符串 列表
        """
        t1 = []
        count = 0
        for m in minute_list:
            if count >= max_count:
                break 

            day1 = datetime.datetime.now() - datetime.timedelta(minutes=m*0.99)
            ss = day1.strftime(dt_format)
            t1.append(ss)
            count = count+1 
        return t1

    def year1_ymh(self, count=3, dt_format='%Y-%m-%d %H:%M:%S', 
                  minute_min=10, minute_max=24*60*30):
        """生成count个，一年内的 随机日期字符串
        - count:随机字符串的个数


        说明
        --------------------------
        - 日期可精准的分钟级别，最小分钟间隔为10分钟，最大跨越1年
        
        
        examples
        ----------------------------
        year1_ymh(count=3, dt_format='%Y-%m-%d')
        
        """
        m_time = self._minute_one_year(minute_min=minute_min, minute_max=minute_max, count=count)
        
        res = self._ymdhms_time(minute_list=m_time, max_count=count, dt_format=dt_format)
        return res 

import pandas as pd
import numpy as np


class JiaoYiBase:
    """
    交易和账户数据生成器

    优化说明：
    1. make_acc11方法生成的账户会存储在实例中
    2. make_trans11方法生成的交易流水只能使用已存储的账户池中的账户
    3. 账户池中的账户可以不在交易中出现，但交易中的账户必须来自账户池
    """

    def __init__(self):
        """初始化JiaoYi实例，用于管理账户池"""
        self._accounts_df = None
        self._accounts_generated = False

    def _make_acc11_instance(self, n_accounts=100):
        """生成账户数据并存储在实例中（实例方法）
        - n_accounts: 要生成的账户数量，默认100个
        - 返回生成的账户DataFrame
        """
        np.random.seed(42)

        # 银行列表
        banks = ['BOC', 'ABC', 'ICBC', 'CMB', 'CCB', 'BOCOM', 'PAB', 'CMBC', 'CEB', 'HXB']

        # 账户状态列表
        account_statuses = ['Active', 'Inactive', 'Frozen', 'Closed', 'Pending']

        # 账户类型列表
        account_types = ['Savings', 'Checking', 'Business', 'Investment', 'Credit']

        # 生成开户时间
        tg = TimeGen()
        opening_times = tg.year1_ymh(count=n_accounts, dt_format='%Y-%m-%d %H:%M:%S')

        # 生成账户
        accounts = []
        for i in range(n_accounts):
            bank = np.random.choice(banks)
            acc_id = f"{bank}_{np.random.randint(1000, 9999)}"

            avg_paid = int(np.random.normal(6000, 3000))
            avg_paid = max(avg_paid, 100)  # 最低100

            avg_recv_usd = int(np.random.normal(500, 200))
            avg_recv_usd = max(avg_recv_usd, 50)

            risk = round(np.random.uniform(0, 1), 1)

            is_laundering = 1 if risk >= 0.7 else 0
            if np.random.rand() < 0.1:  # 加入10%噪声
                is_laundering = 1 - is_laundering

            # 账户状态
            status = np.random.choice(account_statuses)

            # 账户类型
            acc_type = np.random.choice(account_types)

            # 账户余额 (正态分布，平均50000，标准差20000，最低1000)
            balance = int(np.random.normal(50000, 20000))
            balance = max(balance, 1000)

            accounts.append({
                'Account': acc_id,
                'Bank': bank,
                'avg_paid_CNY': avg_paid,
                'avg_received_USD': avg_recv_usd,
                'risk_score': risk,
                'Is_Laundering': is_laundering,
                'Opening_Time': opening_times[i],
                'Status': status,
                'Account_Type': acc_type,
                'Balance': balance
            })

        self._accounts_df = pd.DataFrame(accounts)
        self._accounts_generated = True
        return self._accounts_df

    def _make_trans11_instance(self, n_transactions=1000):
        """生成交易流水数据，使用已生成的账户池（实例方法）
        - n_transactions: 要生成的交易数量，默认1000笔
        - 返回生成的交易流水DataFrame
        - 注意：必须先调用_make_acc11_instance方法生成账户池
        """
        if not self._accounts_generated or self._accounts_df is None:
            raise ValueError("必须先调用make_acc11方法生成账户池才能生成交易流水")

        if len(self._accounts_df) < 2:
            raise ValueError("账户池中至少需要2个账户才能生成交易流水")

        payment_formats = ['Transfer', 'Wire', 'ACH', 'SWIFT']
        start_date = pd.Timestamp('2023-01-01')
        end_date = pd.Timestamp('2024-12-31')

        transactions = []

        for _ in range(n_transactions):
            from_acc = self._accounts_df.sample(1).iloc[0]
            to_acc = self._accounts_df[self._accounts_df['Account'] != from_acc['Account']].sample(1).iloc[0]

            # Amount based on sender's avg_paid_CNY with variation
            base_amount = from_acc['avg_paid_CNY']
            amount = int(base_amount * np.random.uniform(0.7, 1.3))  # ±30%

            currency = 'USD' if np.random.rand() < 0.1 else 'CNY'

            payment_format = np.random.choice(payment_formats)

            # 生成随机日期时间
            timestamp = start_date + (end_date - start_date) * np.random.rand()

            # time8: 8位日期格式 2023-07-09
            time8 = timestamp.strftime('%Y-%m-%d')

            # time14: 14位日期时间格式 2025-10-12 15:43:45
            time14 = timestamp.strftime('%Y-%m-%d %H:%M:%S')

            transactions.append({
                'From': from_acc['Account'],
                'To': to_acc['Account'],
                'Amount': amount,
                'Currency': currency,
                'Payment Format': payment_format,
                'time8': time8,
                'time14': time14
            })

        df_transactions = pd.DataFrame(transactions)
        return df_transactions

    def get_accounts(self):
        """获取当前账户池
        - 返回存储的账户DataFrame，如果没有则返回None
        """
        return self._accounts_df

    def is_accounts_generated(self):
        """检查是否已生成账户池
        - 返回布尔值
        """
        return self._accounts_generated

    def reset_accounts(self):
        """重置账户池
        - 清空已生成的账户数据
        """
        self._accounts_df = None
        self._accounts_generated = False

    # 公共实例方法，供用户使用
    def make_acc11_public(self, n_accounts=100):
        """公共的生成账户方法（实例方法）
        - n_accounts: 要生成的账户数量，默认100个
        """
        return self._make_acc11_instance(n_accounts)

    def make_trans11_public(self, n_transactions=1000):
        """公共的生成交易方法（实例方法）
        - n_transactions: 要生成的交易数量，默认1000笔
        """
        return self._make_trans11_instance(n_transactions)

    @classmethod
    def make_acc11(cls):
        """保留原有的类方法，用于向后兼容"""
        instance = cls()
        return instance._make_acc11_instance()

    @classmethod
    def make_trans11(cls):
        """保留原有的类方法，用于向后兼容"""
        instance = cls()
        # 先生成账户
        instance._make_acc11_instance()
        # 然后生成交易
        return instance._make_trans11_instance()



class JiaoYi(JiaoYiBase):
    """
    交易和账户数据生成器

    优化说明：
    1. make_acc11方法生成的账户会存储在实例中
    2. make_trans11方法生成的交易流水只能使用已存储的账户池中的账户
    3. 账户池中的账户可以不在交易中出现，但交易中的账户必须来自账户池
    """

    def __init__(self):
        """初始化JiaoYi实例，用于管理账户池"""
        super().__init__()
    

    @classmethod
    def make_acc11(cls):
        """保留原有的类方法，用于向后兼容"""
        instance = cls()
        return instance._make_acc11_instance()

    @classmethod
    def make_trans11(cls):
        """保留原有的类方法，用于向后兼容"""
        instance = cls()
        # 先生成账户
        instance._make_acc11_instance()
        # 然后生成交易
        return instance._make_trans11_instance()


    @classmethod
    def make_trans12(cls, num_accounts: int = 50000,
                      transactions_per_account: int = 50,
                      start_date: str = '2024-01-01',
                      end_date: str = '2024-02-01',
                      acc1='acc1',acc2='acc2',time_col='time14',amt_col='amt') -> pd.DataFrame:
        """按账户生成流水，每个账户生成固定条数的交易

        参数:
        num_accounts: 账户数量
        transactions_per_account: 每账户平均交易数
        start_date: 开始日期
        end_date: 结束日期

        返回:
        示例交易数据DataFrame
        """
        logger.info(f"创建示例数据: {num_accounts} 账户, 每账户约 {transactions_per_account} 条交易")

        # 生成账户
        accounts = [f'acc_{i:06d}' for i in range(1, num_accounts + 1)]

        # 添加一些特殊账户用于测试排除功能
        accounts.extend(['acc1', 'acc2', 'special_account_1', 'special_account_2'])

        data = []
        start_dt = pd.to_datetime(start_date)
        end_dt = pd.to_datetime(end_date)
        days_diff = (end_dt - start_dt).days

        for account in accounts:
            # 为每个账户生成随机数量的交易
            num_transactions = max(1, int(np.random.normal(transactions_per_account, 15)))

            for _ in range(num_transactions):
                # 随机生成交易时间
                random_days = np.random.randint(0, days_diff)
                random_hours = np.random.randint(0, 24)
                random_minutes = np.random.randint(0, 60)
                transaction_time = start_dt + timedelta(
                    days=random_days, hours=random_hours, minutes=random_minutes
                )

                # 随机生成交易金额
                amount = round(np.random.exponential(1000), 2)

                # 随机选择交易对手
                counterpart = random.choice(accounts)

                data.append({
                    acc1: account,
                    acc2: counterpart,
                    time_col: transaction_time,
                    amt_col: amount
                })

        df = pd.DataFrame(data)
        logger.info(f"示例数据创建完成: {len(df)} 条交易记录")

        return df


    @classmethod
    def make_trans13(cls, num_accounts: int = 50000,
                transactions_per_account: int = 50,
                start_date: str = '2024-01-01',
                end_date: str = '2024-02-01',
                acc1='acc1',acc2='acc2',time_col='time14',
                num_cols=['amt','balance'], cat_cols=['currency','payment_format']) -> pd.DataFrame:
        """
        1. 将JiaoYi.make_trans11方法生成数据的方法融入JiaoYi.make_trans12，形成本方法的逻辑
        2. 添加risk列，范围[0,1]
        3. 添加label列，risk>0.5为1，否则为0
        4. 支持多个数值列，通过num_cols参数配置
        5. 支持多个类别列，通过cat_cols参数配置
        """
        logger.info(f"创建示例数据: {num_accounts} 账户, 每账户约 {transactions_per_account} 条交易")

        # 银行列表 (来自make_trans11)
        banks = ['BOC', 'ABC', 'ICBC', 'CMB', 'CCB', 'BOCOM', 'PAB', 'CMBC', 'CEB', 'HXB']

        # 支付格式 (来自make_trans11)
        payment_formats = ['Transfer', 'Wire', 'ACH', 'SWIFT']

        # 生成账户 (结合make_trans11的银行账户格式和make_trans12的生成逻辑)
        accounts = []
        for i in range(num_accounts):
            bank = np.random.choice(banks)
            acc_id = f"{bank}_{np.random.randint(1000, 9999)}"
            accounts.append(acc_id)

        # 添加一些特殊账户用于测试排除功能
        accounts.extend(['acc1', 'acc2', 'special_account_1', 'special_account_2'])

        data = []
        start_dt = pd.to_datetime(start_date)
        end_dt = pd.to_datetime(end_date)
        days_diff = (end_dt - start_dt).days

        for account in accounts:
            # 为每个账户生成随机数量的交易
            num_transactions = max(1, int(np.random.normal(transactions_per_account, 15)))

            for _ in range(num_transactions):
                # 随机生成交易时间
                random_days = np.random.randint(0, days_diff)
                random_hours = np.random.randint(0, 24)
                random_minutes = np.random.randint(0, 60)
                transaction_time = start_dt + timedelta(
                    days=random_days, hours=random_hours, minutes=random_minutes
                )

                # 随机选择交易对手
                counterpart = random.choice(accounts)
                while counterpart == account:  # 确保不是自己转给自己
                    counterpart = random.choice(accounts)

                # 生成多个数值列的数据
                numeric_data = {}
                for col in num_cols:
                    if col == 'amt':
                        # 交易金额 (结合make_trans11的金额生成逻辑)
                        base_amount = np.random.normal(6000, 3000)  # 来自make_trans11的avg_paid_CNY逻辑
                        base_amount = max(base_amount, 100)  # 最低100
                        amount = round(base_amount * np.random.uniform(0.7, 1.3), 2)  # ±30%变化
                        numeric_data[col] = amount
                    elif col == 'balance':
                        # 账户余额 (基于账户类型的正态分布)
                        if 'Savings' in account or 'Checking' in account:
                            base_balance = np.random.normal(50000, 20000)
                        else:
                            base_balance = np.random.normal(100000, 50000)
                        balance = max(int(base_balance), 1000)
                        numeric_data[col] = balance
                    else:
                        # 其他数值列，默认生成逻辑
                        base_value = np.random.normal(1000, 500)
                        base_value = max(base_value, 10)
                        numeric_data[col] = round(base_value * np.random.uniform(0.8, 1.2), 2)

                # 生成多个类别列的数据
                categorical_data = {}
                for col in cat_cols:
                    if col == 'currency':
                        # 货币列 (来自make_trans11)
                        categorical_data[col] = 'USD' if np.random.rand() < 0.1 else 'CNY'
                    elif col == 'payment_format':
                        # 支付格式 (来自make_trans11)
                        categorical_data[col] = np.random.choice(payment_formats)
                    elif col == 'transaction_type':
                        # 交易类型
                        categorical_data[col] = np.random.choice(['Deposit', 'Withdrawal', 'Transfer', 'Payment'])
                    elif col == 'status':
                        # 交易状态
                        categorical_data[col] = np.random.choice(['Completed', 'Pending', 'Failed', 'Cancelled'])
                    else:
                        # 其他类别列，默认生成逻辑
                        categorical_data[col] = f"type_{np.random.randint(1, 10)}"

                # 生成risk值，范围[0,1]
                risk = round(np.random.uniform(0, 1), 3)

                # 根据risk生成label：risk>0.5为1，否则为0
                label = 1 if risk > 0.5 else 0

                # 构建数据记录
                record = {
                    acc1: account,
                    acc2: counterpart,
                    time_col: transaction_time,
                    'risk': risk,
                    'label': label
                }

                # 添加数值列
                record.update(numeric_data)

                # 添加类别列
                record.update(categorical_data)

                data.append(record)

        df = pd.DataFrame(data)

        # 添加time8列：time_col列的yyyy-mm-dd部分，字符串类型
        if time_col in df.columns:
            df['time8'] = df[time_col].dt.strftime('%Y-%m-%d')
            logger.info(f"已添加time8列: {time_col} -> time8 (yyyy-mm-dd格式)")

            # 调整列顺序：将time8列放在time_col列前面
            columns = list(df.columns)
            if time_col in columns and 'time8' in columns:
                # 找到time_col和time8的位置
                time_col_index = columns.index(time_col)
                time8_index = columns.index('time8')

                # 如果time8在time_col后面，则交换位置
                if time8_index > time_col_index:
                    # 移除time8列
                    columns.pop(time8_index)
                    # 在time_col位置之前插入time8
                    columns.insert(time_col_index, 'time8')

                    # 重新排列DataFrame列
                    df = df[columns]

                    logger.info(f"已调整列顺序: time8列已移至{time_col}列前面")

        logger.info(f"示例数据创建完成: {len(df)} 条交易记录")

        return df
    
    


if __name__ == '__main__':
    aa = [[1,2],[1,2],[1,2]]
    b = [1,2,3]
    aa = np.array(aa)
    b = np.array(b)

    x,y = data_sample_small(aa, b)
    print(x)
    print(y)

