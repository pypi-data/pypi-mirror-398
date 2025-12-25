import numpy as np
import random
import pandas as pd
import wave, os
import string

from tpf.box.fil import parentdir
from tpf.box.fil import iswin
from tpf.data.make import TimeGen

class JiaoYiFixed:

    def __init__(self):
        """初始化JiaoYi实例，用于管理账户池"""
        self._accounts_df = None
        self._accounts_generated = False

    def make_acc11(self, n_accounts=100):
        """生成账户数据并存储在实例中
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

    def make_trans11(self, n_transactions=1000):
        """生成交易流水数据，使用已生成的账户池
        - n_transactions: 要生成的交易数量，默认1000笔
        - 返回生成的交易流水DataFrame
        - 注意：必须先调用make_acc11方法生成账户池
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

            timestamp = start_date + (end_date - start_date) * np.random.rand()
            timestamp = timestamp.strftime('%Y-%m-%d')

            transactions.append({
                'From': from_acc['Account'],
                'To': to_acc['Account'],
                'Amount': amount,
                'Currency': currency,
                'Payment Format': payment_format,
                'Timestamp': timestamp
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

    @classmethod
    def make_acc11(cls):
        """保留原有的类方法，用于向后兼容"""
        instance = cls()
        return instance.make_acc11()

    @classmethod
    def make_trans11(cls):
        """保留原有的类方法，用于向后兼容"""
        instance = cls()
        return instance.make_trans11()