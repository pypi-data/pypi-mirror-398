"""
交易数据采样脚本 - Python版本
基于高斯数据库SQL脚本的逻辑实现

功能：
1. 取一段时间的数据，提取其不重复账户
2. 从这些账户中去除排除账户后
3. 循环每个账户取其一个月的数据，降序排列，取最近的100条数据

作者：AI Assistant
日期：2024
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import logging
from typing import List, Dict, Optional, Tuple

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class TransactionSampler:
    """交易数据采样器"""

    def __init__(self,
                 start_date: str = '2024-01-01',
                 end_date: str = '2024-02-01',
                 excluded_accounts: List[str] = ['acc1', 'acc2'],
                 sample_size: int = 10000,
                 records_per_account: int = 100,
                 acc1: str = 'acctt',
                 acc2: str = 'acc2',
                 time_col: str = 'dt_time',
                 amt_col: str = 'amount'):
        """
        初始化交易数据采样器

        参数:
        start_date: 开始日期，格式 'YYYY-MM-DD'
        end_date: 结束日期，格式 'YYYY-MM-DD'
        excluded_accounts: 需要排除的账户列表
        sample_size: 采样账户数量
        records_per_account: 每个账户保留的交易记录数量
        acc1: 主账户列名
        acc2: 对手账户列名
        time_col: 时间列名
        amt_col: 金额列名
        """
        self.start_date = pd.to_datetime(start_date)
        self.end_date = pd.to_datetime(end_date)
        self.excluded_accounts = set(excluded_accounts)
        self.sample_size = sample_size
        self.records_per_account = records_per_account
        self.acc1 = acc1
        self.acc2 = acc2
        self.time_col = time_col
        self.amt_col = amt_col

        # 采样统计信息
        self.sampling_stats = {}

        logger.info(f"初始化交易采样器:")
        logger.info(f"  时间范围: {start_date} 到 {end_date}")
        logger.info(f"  排除账户: {excluded_accounts}")
        logger.info(f"  采样账户数: {sample_size}")
        logger.info(f"  每账户记录数: {records_per_account}")

    def load_data(self, df: pd.DataFrame) -> None:
        """
        加载交易数据

        参数:
        df: 交易数据DataFrame，应包含列: acctt, dt_time, acc2, amount 等
        """
        # 数据预处理
        self.raw_data = df.copy()

        # 转换时间列
        if self.time_col in self.raw_data.columns:
            self.raw_data[self.time_col] = pd.to_datetime(self.raw_data[self.time_col])

        # 过滤时间范围
        mask = (self.raw_data[self.time_col] >= self.start_date) & (self.raw_data[self.time_col] < self.end_date)
        self.data = self.raw_data[mask].copy()

        logger.info(f"加载数据完成:")
        logger.info(f"  原始数据行数: {len(self.raw_data)}")
        logger.info(f"  时间范围内行数: {len(self.data)}")
        logger.info(f"  数据列: {list(self.data.columns)}")

    def step1_get_unique_accounts(self) -> pd.DataFrame:
        """
        步骤1：获取时间范围内的所有不重复账户
        """
        logger.info("=" * 60)
        logger.info("步骤1：获取不重复账户")

        # 获取不重复账户
        unique_accounts = self.data[self.acc1].dropna()
        unique_accounts = unique_accounts[unique_accounts != '']
        unique_accounts = unique_accounts.unique()

        # 创建账户统计信息
        account_stats = self.data.groupby(self.acc1).agg({
            self.time_col: ['min', 'max', 'count'],
            self.amt_col: ['sum', 'mean', 'std']
        }).round(2)

        # 扁平化列名
        account_stats.columns = ['earliest_transaction', 'latest_transaction',
                                'transaction_count', 'total_amount', 'avg_amount', 'std_amount']
        account_stats = account_stats.reset_index().rename(columns={'index': self.acc1})

        # 记录统计信息
        self.sampling_stats['total_unique_accounts'] = len(unique_accounts)

        logger.info(f"发现 {len(unique_accounts)} 个不重复账户")
        logger.info(f"账户交易统计:")
        logger.info(f"  平均交易数: {account_stats['transaction_count'].mean():.1f}")
        logger.info(f"  最少交易数: {account_stats['transaction_count'].min()}")
        logger.info(f"  最多交易数: {account_stats['transaction_count'].max()}")

        return account_stats

    def step2_filter_and_sample_accounts(self, account_stats: pd.DataFrame) -> List[str]:
        """
        步骤2：排除指定账户并采样

        参数:
        account_stats: 账户统计信息DataFrame

        返回:
        采样的账户列表
        """
        logger.info("=" * 60)
        logger.info("步骤2：排除指定账户并采样")

        # 过滤掉排除的账户
        eligible_accounts = account_stats[~account_stats[self.acc1].isin(self.excluded_accounts)]

        logger.info(f"排除指定账户后剩余 {len(eligible_accounts)} 个账户")
        logger.info(f"排除的账户: {self.excluded_accounts}")

        # 如果账户数量不足，则全部选择
        if len(eligible_accounts) <= self.sample_size:
            sampled_accounts = eligible_accounts[self.acc1].tolist()
            logger.info(f"账户数量不足({len(eligible_accounts)} < {self.sample_size})，选择全部账户")
        else:
            # 随机采样
            sampled_accounts = eligible_accounts[self.acc1].sample(n=self.sample_size, random_state=42).tolist()
            logger.info(f"随机采样 {len(sampled_accounts)} 个账户")

        # 记录统计信息
        self.sampling_stats['eligible_accounts'] = len(eligible_accounts)
        self.sampling_stats['sampled_accounts'] = len(sampled_accounts)
        self.sampling_stats['sampling_percentage'] = round(
            len(sampled_accounts) / len(eligible_accounts) * 100, 2
        )

        return sampled_accounts

    def step3_sample_transactions_per_account(self, sampled_accounts: List[str]) -> pd.DataFrame:
        """
        步骤3：对每个采样账户，获取最近的100条交易记录

        参数:
        sampled_accounts: 采样的账户列表

        返回:
        采样的交易数据DataFrame
        """
        logger.info("=" * 60)
        logger.info("步骤3：获取每个账户的最近交易记录")

        sampled_transactions = []

        for i, account in enumerate(sampled_accounts):
            if i % 1000 == 0:
                logger.info(f"处理进度: {i+1}/{len(sampled_accounts)}")

            # 获取该账户的所有交易
            account_data = self.data[self.data[self.acc1] == account].copy()

            if len(account_data) == 0:
                continue

            # 按时间降序排序
            account_data = account_data.sort_values(self.time_col, ascending=False)

            # 获取最近的交易记录
            recent_transactions = account_data.head(self.records_per_account).copy()

            # 添加排名和统计信息
            recent_transactions['transaction_rank'] = range(1, len(recent_transactions) + 1)
            recent_transactions['total_transactions'] = len(account_data)

            sampled_transactions.append(recent_transactions)

        # 合并所有采样的交易记录
        if sampled_transactions:
            result_df = pd.concat(sampled_transactions, ignore_index=True)
        else:
            result_df = pd.DataFrame()

        # 记录统计信息
        self.sampling_stats['total_sampled_transactions'] = len(result_df)
        if len(sampled_accounts) > 0:
            self.sampling_stats['avg_transactions_per_account'] = round(
                len(result_df) / len(sampled_accounts), 2
            )
        else:
            self.sampling_stats['avg_transactions_per_account'] = 0

        logger.info(f"采样完成:")
        logger.info(f"  采样账户数: {len(sampled_accounts)}")
        logger.info(f"  采样交易记录数: {len(result_df)}")
        logger.info(f"  平均每账户记录数: {self.sampling_stats['avg_transactions_per_account']}")

        return result_df

    def sample_transactions(self, df: pd.DataFrame,show_report=False) -> Tuple[pd.DataFrame, Dict]:
        """
        执行完整的交易数据采样流程

        参数:
        df: 原始交易数据DataFrame

        返回:
        (采样的交易数据, 采样统计信息)
        """
        logger.info("开始交易数据采样流程")

        # 加载数据
        self.load_data(df)

        # 步骤1：获取不重复账户
        account_stats = self.step1_get_unique_accounts()

        # 步骤2：排除指定账户并采样
        sampled_accounts = self.step2_filter_and_sample_accounts(account_stats)

        # 步骤3：获取每个账户的最近交易记录
        sampled_data = self.step3_sample_transactions_per_account(sampled_accounts)

        # 添加采样时间戳
        sampled_data['sample_timestamp'] = datetime.now()

        # 生成采样报告
        if show_report:
            self.generate_sampling_report(sampled_data)

        return sampled_data, self.sampling_stats

    def generate_sampling_report(self, sampled_data: pd.DataFrame) -> None:
        """生成采样报告"""
        logger.info("=" * 60)
        logger.info("采样报告")

        print("\n" + "="*60)
        print("交易数据采样报告")
        print("="*60)

        print(f"\n📊 采样参数:")
        print(f"  时间范围: {self.start_date.strftime('%Y-%m-%d')} 到 {self.end_date.strftime('%Y-%m-%d')}")
        print(f"  排除账户: {list(self.excluded_accounts)}")
        print(f"  目标采样数: {self.sample_size}")
        print(f"  每账户记录数: {self.records_per_account}")

        print(f"\n📈 采样统计:")
        print(f"  原始数据记录数: {len(self.raw_data):,}")
        print(f"  时间范围内记录数: {len(self.data):,}")
        print(f"  不重复账户数: {self.sampling_stats.get('total_unique_accounts', 0):,}")
        print(f"  有效账户数: {self.sampling_stats.get('eligible_accounts', 0):,}")
        print(f"  采样账户数: {self.sampling_stats.get('sampled_accounts', 0):,}")
        print(f"  采样比例: {self.sampling_stats.get('sampling_percentage', 0):.2f}%")
        print(f"  采样记录数: {self.sampling_stats.get('total_sampled_transactions', 0):,}")
        print(f"  平均每账户记录数: {self.sampling_stats.get('avg_transactions_per_account', 0):.1f}")

        if not sampled_data.empty:
            print(f"\n💰 交易金额统计:")
            print(f"  总金额: {sampled_data[self.amt_col].sum():,.2f}")
            print(f"  平均金额: {sampled_data[self.amt_col].mean():.2f}")
            print(f"  最大金额: {sampled_data[self.amt_col].max():,.2f}")
            print(f"  最小金额: {sampled_data[self.amt_col].min():,.2f}")

            print(f"\n📅 时间范围:")
            print(f"  最早交易: {sampled_data[self.time_col].min().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"  最新交易: {sampled_data[self.time_col].max().strftime('%Y-%m-%d %H:%M:%S')}")

        print("\n" + "="*60)

    def save_sampled_data(self, sampled_data: pd.DataFrame, output_path: str) -> None:
        """
        保存采样数据到文件

        参数:
        sampled_data: 采样数据DataFrame
        output_path: 输出文件路径
        """
        try:
            if output_path.endswith('.csv'):
                sampled_data.to_csv(output_path, index=False)
            elif output_path.endswith('.parquet'):
                sampled_data.to_parquet(output_path, index=False)
            elif output_path.endswith('.xlsx'):
                sampled_data.to_excel(output_path, index=False)
            else:
                # 默认保存为CSV
                sampled_data.to_csv(output_path + '.csv', index=False)
                output_path += '.csv'

            logger.info(f"采样数据已保存到: {output_path}")
            print(f"\n💾 数据已保存到: {output_path}")

        except Exception as e:
            logger.error(f"保存数据时出错: {e}")
            print(f"\n❌ 保存数据失败: {e}")



class DataSampler(TransactionSampler):
    def __init__(self, start_date = '2024-01-01', end_date = '2024-02-01', 
                 excluded_accounts = ['acc1', 'acc2'], 
                 sample_size = 10000, 
                 records_per_account = 100, 
                 acc1='acctt', acc2='acc2', time_col='dt_time', amt_col='amount'):
        super().__init__(start_date, end_date, excluded_accounts, sample_size, records_per_account, acc1, acc2, time_col, amt_col)
        
    def sample(self, data, show_all_col=False, file_save_path=None,show_report=False):
        """
        执行数据采样流程

        参数:
        data : pd.DataFrame
            输入的交易数据表
        show_all_col : bool, default False
            是否显示所有列（包括内部统计列）
        file_save_path : str, optional
            保存文件的路径，如果提供则保存采样结果
        show_report : bool, default False
            是否显示采样报告

        返回:
        tuple : (pd.DataFrame, dict)
            采样的数据表和统计信息

        异常:
        ValueError : 当必需的列在数据表中不存在时抛出
        TypeError : 当输入数据类型不正确时抛出
        """
        # 验证输入数据类型
        if not isinstance(data, pd.DataFrame):
            raise TypeError(f"输入数据必须是pandas.DataFrame类型，当前类型: {type(data).__name__}")

        # 检查数据是否为空
        if data.empty:
            raise ValueError("输入数据表为空，无法进行采样")

        # 检查必需的列是否存在
        required_columns = [self.acc1, self.acc2, self.time_col, self.amt_col]
        missing_columns = []

        for col in required_columns:
            if col not in data.columns:
                missing_columns.append(col)

        # 如果有缺失的列，抛出详细的异常信息
        if missing_columns:
            error_msg = "数据表中缺少以下必需的列:\n"
            error_msg += f"缺失列: {missing_columns}\n"
            error_msg += f"数据表当前列: {list(data.columns)}\n"
            error_msg += f"期望的列名映射:\n"
            error_msg += f"  - 主账户列 (acc1): '{self.acc1}'\n"
            error_msg += f"  - 对手账户列 (acc2): '{self.acc2}'\n"
            error_msg += f"  - 时间列 (time_col): '{self.time_col}'\n"
            error_msg += f"  - 金额列 (amt_col): '{self.amt_col}'\n"
            error_msg += "\n解决方案:\n"
            error_msg += "1. 检查数据表列名是否正确\n"
            error_msg += "2. 在初始化DataSampler时指定正确的列名参数\n"
            error_msg += "3. 例如: DataSampler(acc1='your_acc_col', acc2='your_counterparty_col', time_col='your_time_col', amt_col='your_amount_col')"

            raise ValueError(error_msg)

        # 检查列中是否有数据
        empty_columns = []
        for col in required_columns:
            if data[col].isna().all():
                empty_columns.append(col)

        if empty_columns:
            error_msg = f"以下列虽然存在但全部为空值: {empty_columns}"
            raise ValueError(error_msg)

        # 记录验证通过的日志
        logger.info(f"数据验证通过:")
        logger.info(f"  数据行数: {len(data):,}")
        logger.info(f"  数据列数: {len(data.columns)}")
        logger.info(f"  必需列验证: ✓")

        # 执行采样流程
        try:
            df, stat = self.sample_transactions(data, show_report=show_report)
        except Exception as e:
            logger.error(f"数据采样过程中发生错误: {e}")
            raise RuntimeError(f"数据采样失败: {e}") from e

        # 处理显示列的选项
        if not show_all_col and not df.empty:
            columns_to_drop = []
            for col in ['transaction_rank', 'total_transactions', 'sample_timestamp']:
                if col in df.columns:
                    columns_to_drop.append(col)

            if columns_to_drop:
                df = df.drop(columns=columns_to_drop)
                logger.info(f"已移除内部统计列: {columns_to_drop}")

        # 保存文件（如果指定了路径）
        if file_save_path and not df.empty:
            try:
                self.save_sampled_data(df, file_save_path)
            except Exception as e:
                logger.error(f"保存文件时发生错误: {e}")
                raise RuntimeError(f"保存文件失败: {e}") from e

        logger.info(f"采样完成，返回 {len(df)} 条记录")
        return df, stat


def create_sample_data(num_accounts: int = 50000,
                      transactions_per_account: int = 50,
                      start_date: str = '2024-01-01',
                      end_date: str = '2024-02-01',
                      acc1: str = 'acctt',
                      acc2: str = 'acc2',
                      time_col: str = 'dt_time',
                      amt_col: str = 'amount') -> pd.DataFrame:
    """
    创建示例交易数据用于测试

    参数:
    num_accounts: 账户数量
    transactions_per_account: 每账户平均交易数
    start_date: 开始日期
    end_date: 结束日期
    acc1: 主账户列名
    acc2: 对手账户列名
    time_col: 时间列名
    amt_col: 金额列名

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
                time_col: transaction_time,
                acc2: counterpart,
                amt_col: amount
            })

    df = pd.DataFrame(data)
    logger.info(f"示例数据创建完成: {len(df)} 条交易记录")

    return df


def main():
    """主函数 - 演示交易数据采样流程"""

    print("🚀 交易数据采样脚本 - Python版本")
    print("=" * 60)

    # 参数配置
    config = {
        'start_date': '2024-01-01',
        'end_date': '2024-02-01',
        'excluded_accounts': ['acc1', 'acc2'],
        'sample_size': 10000,
        'records_per_account': 100
    }

    # 创建示例数据
    print("📝 创建示例数据...")
    sample_data = create_sample_data(
        num_accounts=50000,
        transactions_per_account=50,
        start_date=config['start_date'],
        end_date=config['end_date']
    )

    # 初始化采样器
    sampler = TransactionSampler(**config)

    # 执行采样
    print("\n🔄 开始执行数据采样...")
    sampled_data, stats = sampler.sample_transactions(sample_data)

    # 保存结果
    if not sampled_data.empty:
        output_file = 'sampled_transactions_202401.csv'
        sampler.save_sampled_data(sampled_data, output_file)

        # 显示前几行数据
        print(f"\n📋 采样数据预览 (前10条):")
        # 使用sampler的列名参数来显示正确的列
        display_cols = [sampler.acc1, sampler.time_col, sampler.acc2, sampler.amt_col, 'transaction_rank']
        available_cols = [col for col in display_cols if col in sampled_data.columns]
        print(sampled_data.head(10)[available_cols].to_string(index=False))

    print("\n✅ 采样流程完成!")


if __name__ == "__main__":
    main()