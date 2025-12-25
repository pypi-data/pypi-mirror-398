#!/usr/bin/env python3
"""
测试 _categorical_function_not_num_date 方法的逻辑
"""
import pandas as pd
import numpy as np

def test_categorical_function_not_num_date():
    """测试分类列判断函数"""

    # 模拟DataToFeature类中的方法
    def _categorical_function_not_num_date(df, num_type=[], date_type=[]):
        # 如果num_type为空，自动推断数值列
        if num_type is None or len(num_type) == 0:
            num_type = df.select_dtypes('number').columns.tolist()

        # 获取所有列名
        col_all = df.columns.tolist()

        # 排除数值列和指定的日期列
        exclude_cols = set(num_type) | set(date_type)
        categorical_cols = list(set(col_all) - exclude_cols)

        # 创建分类列判断函数
        def is_categorical(col: str) -> bool:
            return col in categorical_cols

        return is_categorical

    # 创建测试数据
    test_data = pd.DataFrame({
        'id': [1, 2, 3],
        'name': ['Alice', 'Bob', 'Charlie'],
        'age': [25, 30, 35],
        'salary': [50000.0, 60000.0, 70000.0],
        'join_date': pd.to_datetime(['2020-01-01', '2019-05-15', '2021-03-20']),
        'is_active': [True, False, True],
        'department': ['IT', 'HR', 'Finance']
    })

    print("测试数据:")
    print(test_data.dtypes)
    print("\n")

    # 测试1：不提供num_type和date_type，自动推断
    print("测试1：自动推断数值列")
    func1 = _categorical_function_not_num_date(test_data)
    print("数值列（自动推断）:", test_data.select_dtypes('number').columns.tolist())
    print("分类列（推断结果）:", [col for col in test_data.columns if func1(col)])
    print("预期分类列应该是：['name', 'department']")
    print("\n")

    # 测试2：提供num_type和date_type
    print("测试2：指定num_type和date_type")
    num_type = ['age', 'salary']
    date_type = ['join_date']
    func2 = _categorical_function_not_num_date(test_data, num_type, date_type)
    print("指定数值列:", num_type)
    print("指定日期列:", date_type)
    print("分类列（指定结果）:", [col for col in test_data.columns if func2(col)])
    print("预期分类列应该是：['id', 'name', 'is_active', 'department']")
    print("\n")

    # 测试3：只有num_type，无date_type
    print("测试3：只有num_type，无date_type")
    num_type = ['age', 'salary']
    func3 = _categorical_function_not_num_date(test_data, num_type, [])
    print("指定数值列:", num_type)
    print("分类列（结果）:", [col for col in test_data.columns if func3(col)])
    print("预期分类列应该是：['id', 'name', 'join_date', 'is_active', 'department']")

if __name__ == "__main__":
    test_categorical_function_not_num_date()