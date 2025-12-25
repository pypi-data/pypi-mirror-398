"""
# 伪算法 - 基于a01_create_dwd_bb11_trans.sql脚本功能分析
#
# 1. 初始化环境设置
#    - 设置SQL*Plus环境参数（关闭回显、反馈、验证等）
#    - 配置错误处理机制
#
# 2. 表结构清理
#    - 删除已存在的表（如果存在）：bb11_trans1, temp_parties, temp_organ_config
#    - 使用异常处理避免表不存在的错误
#
# 3. 动态创建主交易表 bb11_trans1
#    - 接收分区日期范围参数（开始日期、结束日期）
#    - 动态生成日期分区（每个日期一个分区）
#    - 创建包含95个字段的交易明细表：
#      * 核心标识：TICD, TSTM, DT_TIME
#      * 我方信息：PARTY_ID, PARTY_NAME, PARTY_CLASS_CD, ACCT_NUM
#      * 交易属性：TSDR, CASH_IND, OVERAREA_IND, CNY_AMT, CRAT, USD_AMT等
#      * 对方信息：TCNM, TCAC, OPP_PARTY_ID等
#      * 交易细节：TX_CD, TX_TYPE_CD, TSTP, CHANNEL等
#      * 扩展信息：ORGANKEY, CARD_NUM, SUBJECTNO等字段
#
# 4. 创建临时辅助表
#    - temp_parties：客户信息临时表（6个字段）
#    - temp_organ_config：机构配置临时表（11个字段）
#
# 5. 生成测试数据
#    - 向temp_parties插入500条客户数据：
#      * 400条个人客户（80%）
#      * 100条企业客户（20%）
#      * 包含随机生成的中文姓名、证件类型、证件号码
#    - 向temp_organ_config插入机构配置数据：
#      * 多种渠道类型：手机银行、网银、ATM、柜面、POS等
#      * 多种币种：CNY, USD, HKD, EUR, JPY
#      * 包含汇率信息
#
# 6. 添加表和字段注释
#    - 为bb11_trans1表添加详细注释
#    - 为每个字段添加业务含义说明
#
# Python实现目标：
# 1. 将SQL表结构转换为Pandas DataFrame
# 2. 生成模拟数据
# 3. 保存为CSV文件到/ai/data/tmp目录

"""

import pandas as pd
import numpy as np
import os
from datetime import datetime, timedelta
import random

# 确保输出目录存在
output_dir = '/ai/data/tmp'
os.makedirs(output_dir, exist_ok=True)

def create_bb11_trans1_dataframe(parties_df, num_rows=1000):
    """
    创建bb11_trans1表的DataFrame
    基于SQL脚本中的95个字段结构，客户信息来自temp_parties表
    """
    # 定义字段和数据类型
    columns = [
        'TICD', 'TSTM', 'DT_TIME', 'PARTY_ID', 'PARTY_NAME', 'PARTY_CLASS_CD', 'ACCT_NUM',
        'TSDR', 'CASH_IND', 'OVERAREA_IND', 'CNY_AMT', 'CRAT', 'USD_AMT', 'CRTP', 'CURR_CD',
        'CHANNEL', 'OPP_ISPARTY', 'TCNM', 'TCAC', 'TX_CD', 'TX_TYPE_CD', 'TSTP',
        'ORGANKEY', 'CATP', 'CARD_NUM', 'CARD_TYPE', 'SUBJECTNO', 'AMT_VAL', 'DES', 'CRSP',
        'TSCT', 'TRCD_COUNTRY', 'TRCD_AREA', 'TX_GO_COUNTRY', 'TX_GO_AREA', 'OPP_SYSID',
        'CFRC_COUNTRY', 'CFRC_AREA', 'CFCT', 'CFIC', 'CFIN', 'OPP_PARTY_ID', 'TCAT', 'TCIT',
        'TCID', 'TCIT_EXP', 'OPP_PARTY_CLASS_CD', 'OPP_PBC_PARTY_CLASS_CD', 'OPP_OFF_SHORE_IND',
        'OPP_CTVC', 'BKNM', 'BITP', 'BKID', 'BITP_EXP', 'BKNT', 'AGENT_TEL', 'ORG_TRANS_RELA',
        'TELLER', 'RECEIVE_PAY_TYPE', 'RECEIVE_PAY_NUM', 'TSTP_TYPE_F', 'TSTP_TYPE_F_DESC',
        'TSTP_TYPE_F_CD', 'PAYMENT_TRANS_NUM', 'IS_MERCH', 'MCC_MERCH', 'MERCH_NO', 'TRAN_IP',
        'TRANS_TYPE', 'TEMP1', 'TEMP2', 'LAST_UPD_USR', 'BUSINESSTYPE', 'FX_DECLARATION_NUM',
        'REMIT_CHANNEL', 'USE_CARD_FLAG', 'INTERNAL_ACCT_NUM', 'ACCT_NUM_R', 'CHANNEL_N',
        'PHONE_NUM', 'TR_STATUS_CD', 'TYPE_CD', 'CALENDAR_TIME', 'PHONE_NUM_C', 'ACCT_TYPE',
        'CTAC_NAME', 'CORP_ORG', 'ORGANKEY_PARTY'
    ]

    # 从temp_parties表中随机选择客户作为交易参与方
    selected_parties = parties_df.sample(n=num_rows, replace=True)

    # 生成对方客户信息（也来自temp_parties表，但与主客户不同）
    opp_parties = parties_df.sample(n=num_rows, replace=True)

    # 生成模拟数据
    data = {
        'TICD': [f'TX{i:08d}' for i in range(num_rows)],
        'TSTM': [(datetime.now() - timedelta(days=random.randint(0, 365))).strftime('%Y-%m-%d') for _ in range(num_rows)],
        'DT_TIME': [(datetime.now() - timedelta(days=random.randint(0, 365), hours=random.randint(0, 23))).strftime('%Y-%m-%d %H:%M:%S') for _ in range(num_rows)],
        # 从temp_parties表获取客户信息
        'PARTY_ID': selected_parties['PARTY_ID'].values,
        'PARTY_NAME': selected_parties['PARTY_NAME'].values,
        'PARTY_CLASS_CD': selected_parties['PARTY_CLASS_CD'].values,
        'ACCT_NUM': selected_parties['ACCT_NUM'].values,
        'ORGANKEY': selected_parties['ORGAN_KEY'].values,  # 从客户表中获取机构信息
        'ORGANKEY_PARTY': selected_parties['ORGAN_KEY'].values,
        'PHONE_NUM': selected_parties['PHONE_NUM'].values,
        'PHONE_NUM_C': selected_parties['PHONE_NUM'].values,
        'TSDR': np.random.choice(['01', '02'], num_rows),
        'CASH_IND': np.random.choice(['00', '01'], num_rows),
        'OVERAREA_IND': np.random.choice(['0', '1', ''], num_rows),
        'CNY_AMT': np.round(np.random.uniform(-100000, 100000, num_rows), 2),
        'CRAT': np.round(np.random.uniform(-100000, 100000, num_rows), 2),
        'USD_AMT': np.round(np.random.uniform(-15000, 15000, num_rows), 2),
        'CRTP': np.random.choice(['CNY', 'USD', 'HKD', 'EUR', 'JPY'], num_rows),
        'CURR_CD': np.random.choice(['1', '2'], num_rows),
        'CHANNEL': np.random.choice(['1', '2', '3', '4', '5', '6'], num_rows),
        'OPP_ISPARTY': np.random.choice(['0', '1', '2'], num_rows),
        # 从temp_parties表获取对方客户信息
        'TCNM': opp_parties['PARTY_NAME'].values,
        'TCAC': opp_parties['ACCT_NUM'].values,
        'OPP_PARTY_ID': opp_parties['PARTY_ID'].values,
        'TX_CD': np.random.choice(['1001', '1002', '9001', '9002'], num_rows),
        'TX_TYPE_CD': np.random.choice(['01', '02', '03', '04'], num_rows),
        'TSTP': np.random.choice(['001', '002', '003', '004'], num_rows),
        'CATP': np.random.choice(['10', '20', '30', '40'], num_rows),
        'CARD_NUM': [f'CARD{i:012d}' if random.random() > 0.3 else '' for i in range(num_rows)],
        'CARD_TYPE': np.random.choice(['10', '20', '30', '90', ''], num_rows),
        'SUBJECTNO': [f'SUB{i:06d}' for i in range(num_rows)],
        'AMT_VAL': np.round(np.random.uniform(0, 1000000, num_rows), 2),
        'DES': ['交易描述' + str(i) for i in range(num_rows)],
        'CRSP': ['交易用途' + str(i) for i in range(num_rows)],
        'TSCT': np.random.choice(['001', '002', '003', ''], num_rows),
        'TRCD_COUNTRY': np.random.choice(['CN', 'US', 'HK', 'JP', ''], num_rows),
        'TRCD_AREA': np.random.choice(['110000', '310000', '440300', ''], num_rows),
        'TX_GO_COUNTRY': np.random.choice(['CN', 'US', 'HK', 'JP', ''], num_rows),
        'TX_GO_AREA': np.random.choice(['110000', '310000', '440300', ''], num_rows),
        'OPP_SYSID': [f'SYS{i:08d}' if random.random() > 0.5 else '' for i in range(num_rows)],
        'CFRC_COUNTRY': np.random.choice(['CN', 'US', 'HK', 'JP', ''], num_rows),
        'CFRC_AREA': np.random.choice(['110000', '310000', '440300', ''], num_rows),
        'CFCT': np.random.choice(['11', '12', '13', ''], num_rows),
        'CFIC': [f'BK{i:08d}' if random.random() > 0.7 else '' for i in range(num_rows)],
        'CFIN': ['银行' + str(i) if random.random() > 0.7 else '' for i in range(num_rows)],
        'TCAT': np.random.choice(['10', '20', '30', ''], num_rows),
        'TCIT': np.random.choice(['110001', '110023', '610099', ''], num_rows),
        'TCID': [f'ID{i:012d}' if random.random() > 0.6 else '' for i in range(num_rows)],
        'TCIT_EXP': ['证件类型' + str(i) if random.random() > 0.8 else '' for i in range(num_rows)],
        'OPP_PARTY_CLASS_CD': np.random.choice(['C', 'I', ''], num_rows),
        'OPP_PBC_PARTY_CLASS_CD': np.random.choice(['01', '02', '03', ''], num_rows),
        'OPP_OFF_SHORE_IND': np.random.choice(['0', '1', ''], num_rows),
        'OPP_CTVC': np.random.choice(['01', '02', '03', ''], num_rows),
        'BKNM': ['代理人' + str(i) if random.random() > 0.8 else '' for i in range(num_rows)],
        'BITP': np.random.choice(['110001', '110023', ''], num_rows),
        'BKID': [f'AGENT{i:012d}' if random.random() > 0.8 else '' for i in range(num_rows)],
        'BITP_EXP': ['代理人证件类型' if random.random() > 0.9 else '' for i in range(num_rows)],
        'BKNT': np.random.choice(['CN', 'US', 'HK', ''], num_rows),
        'AGENT_TEL': [f'1{i:010d}' if random.random() > 0.8 else '' for i in range(num_rows)],
        'ORG_TRANS_RELA': np.random.choice(['01', '02', '03', ''], num_rows),
        'TELLER': [f'TELL{i:04d}' for i in range(num_rows)],
        'RECEIVE_PAY_TYPE': np.random.choice(['01', '02', ''], num_rows),
        'RECEIVE_PAY_NUM': [f'PAY{i:010d}' if random.random() > 0.7 else '' for i in range(num_rows)],
        'TSTP_TYPE_F': np.random.choice(['11', '12', '13', ''], num_rows),
        'TSTP_TYPE_F_DESC': ['非柜台交易方式' + str(i) if random.random() > 0.9 else '' for i in range(num_rows)],
        'TSTP_TYPE_F_CD': [f'IP{i:010d}' if random.random() > 0.8 else '' for i in range(num_rows)],
        'PAYMENT_TRANS_NUM': [f'ORDER{i:012d}' if random.random() > 0.7 else '' for i in range(num_rows)],
        'IS_MERCH': np.random.choice(['0', '1', ''], num_rows),
        'MCC_MERCH': np.random.choice(['5812', '5814', '5411', ''], num_rows),
        'MERCH_NO': [f'MERCH{i:08d}' if random.random() > 0.8 else '' for i in range(num_rows)],
        'TRAN_IP': ['192.168.' + str(random.randint(1, 255)) + '.' + str(random.randint(1, 255)) if random.random() > 0.3 else '' for i in range(num_rows)],
        'TRANS_TYPE': np.random.choice(['01', '02', '03', '04'], num_rows),
        'TEMP1': ['备注1' + str(i) if random.random() > 0.9 else '' for i in range(num_rows)],
        'TEMP2': ['备注2' + str(i) if random.random() > 0.9 else '' for i in range(num_rows)],
        'LAST_UPD_USR': [f'USER{i:03d}' for i in range(num_rows)],
        'BUSINESSTYPE': np.random.choice(['A1', 'A2', 'A3', 'A4'], num_rows),
        'FX_DECLARATION_NUM': [f'FX{i:010d}' if random.random() > 0.9 else '' for i in range(num_rows)],
        'REMIT_CHANNEL': np.random.choice(['1', '2', '3', ''], num_rows),
        'USE_CARD_FLAG': np.random.choice(['11', '12', '13', ''], num_rows),
        'INTERNAL_ACCT_NUM': [f'INT{i:010d}' if random.random() > 0.8 else '' for i in range(num_rows)],
        'ACCT_NUM_R': [f'REL{i:010d}' if random.random() > 0.7 else '' for i in range(num_rows)],
        'CHANNEL_N': np.random.choice(['1', '2', '3', '4', '5', '6'], num_rows),
        'PHONE_NUM': [f'1{i:010d}' if random.random() > 0.5 else '' for i in range(num_rows)],
        'TR_STATUS_CD': np.random.choice(['0001', '0002', '0003', ''], num_rows),
        'TYPE_CD': np.random.choice(['01', '02', '03', ''], num_rows),
        'CALENDAR_TIME': [(datetime.now() - timedelta(days=random.randint(0, 365), hours=random.randint(0, 23))).strftime('%Y-%m-%d %H:%M:%S') for _ in range(num_rows)],
        'PHONE_NUM_C': [f'1{i:010d}' if random.random() > 0.5 else '' for i in range(num_rows)],
        'ACCT_TYPE': np.random.choice(['10', '20', '30', ''], num_rows),
        'CTAC_NAME': ['账户名称' + str(i) for i in range(num_rows)],
        'CORP_ORG': [f'CORG{i:06d}' for i in range(num_rows)],
        'ORGANKEY_PARTY': [f'ORG{i:09d}' for i in range(num_rows)]
    }

    df = pd.DataFrame(data)
    return df

def create_temp_parties_dataframe(organ_config_df):
    """
    创建temp_parties表的DataFrame
    基于SQL脚本中的500条客户数据，机构信息来自temp_organ_config表
    """
    # 生成500条客户数据
    party_ids = [f'P{i:06d}' for i in range(1, 501)]
    acct_nums = [f'A{i:010d}' for i in range(1, 501)]
    party_class_cd = ['I'] * 400 + ['C'] * 100  # 400个人 + 100企业

    # 从机构配置表中获取机构信息，为每个客户分配机构
    organ_keys = organ_config_df['ORGAN_KEY'].unique()

    # 为每个客户随机分配机构信息
    assigned_organ_keys = [np.random.choice(organ_keys) for _ in range(500)]
    assigned_organ_names = [organ_config_df[organ_config_df['ORGAN_KEY'] == org_key]['ORGAN_NAME'].iloc[0] for org_key in assigned_organ_keys]
    assigned_country_codes = [organ_config_df[organ_config_df['ORGAN_KEY'] == org_key]['COUNTRY_CODE'].iloc[0] for org_key in assigned_organ_keys]
    assigned_area_codes = [organ_config_df[organ_config_df['ORGAN_KEY'] == org_key]['AREA_CODE'].iloc[0] for org_key in assigned_organ_keys]
    assigned_area_names = [organ_config_df[organ_config_df['ORGAN_KEY'] == org_key]['AREA_NAME'].iloc[0] for org_key in assigned_organ_keys]

    # 生成姓名
    surnames = ['赵', '钱', '孙', '李', '周', '吴', '郑', '王', '冯', '陈']
    given_names = ['伟', '芳', '娜', '敏', '静', '强', '磊', '洋']

    party_names = []
    for i in range(500):
        if i < 400:  # 个人
            surname = np.random.choice(surnames)
            given_name = np.random.choice(given_names)
            party_names.append(surname + given_name)
        else:  # 企业
            # 使用分配的机构所在城市
            city = assigned_area_names[i].replace('市', '').replace('特别行政区', '')
            companies = ['科技', '贸易', '实业', '投资']
            types = ['有限公司', '股份有限公司']
            party_names.append(city + np.random.choice(companies) + np.random.choice(types))

    # 证件类型
    cert_types = []
    for i in range(500):
        if i < 400:  # 个人
            cert_types.append(np.random.choice(['110001', '110023', '119019']))
        else:  # 企业
            cert_types.append(np.random.choice(['610099', '610047', '610005']))

    # 证件号码（使用地区编码）
    cert_ids = []
    for i in range(500):
        if i < 400:  # 个人身份证，使用分配的地区编码
            area_code = assigned_area_codes[i][:4]  # 取前4位作为地区编码
            cert_ids.append(f'{area_code}19700101{i:04d}')
        else:  # 企业
            cert_ids.append(f'91{i:014d}')

    # 生成联系电话（基于地区）
    phone_nums = []
    for i in range(500):
        if i < 400:  # 个人手机号
            phone_nums.append(f'1{random.randint(3,9):d}{random.randint(100000000, 999999999)}')
        else:  # 企业座机
            area_code = assigned_area_codes[i]
            phone_nums.append(f'{area_code[:3]}-{random.randint(10000000, 99999999)}')

    data = {
        'PARTY_ID': party_ids,
        'ACCT_NUM': acct_nums,
        'PARTY_CLASS_CD': party_class_cd,
        'PARTY_NAME': party_names,
        'CERT_TYPE': cert_types,
        'CERT_ID': cert_ids,
        # 新增机构相关字段
        'ORGAN_KEY': assigned_organ_keys,
        'ORGAN_NAME': assigned_organ_names,
        'COUNTRY_CODE': assigned_country_codes,
        'AREA_CODE': assigned_area_codes,
        'AREA_NAME': assigned_area_names,
        'PHONE_NUM': phone_nums,
        'EMAIL': [f'party{i}@example.com' if random.random() > 0.3 else '' for i in range(500)]
    }

    df = pd.DataFrame(data)
    return df

def create_temp_organ_config_dataframe():
    """
    创建temp_organ_config表的DataFrame
    基于SQL脚本中的机构配置数据
    """
    data = {
        'CHANNEL_CODE': ['6', '6', '6', '6', '2', '2', '2', '2', '4', '4', '4', '1', '1', '1', '1', '1', '5', '01', '01', '01', '02', '03'],
        'CHANNEL_NAME': ['手机银行', '手机银行', '手机银行', '手机银行', '网银', '网银', '网银', '网银', 'ATM', 'ATM', 'ATM', '柜面', '柜面', '柜面', '柜面', '柜面', 'POS', '其他互联网', '其他互联网', '其他互联网', '自助设备', '第三方渠道'],
        'WEIGHT': [35, 35, 35, 35, 25, 25, 25, 25, 15, 15, 15, 10, 10, 10, 10, 10, 8, 4, 4, 4, 2, 1],
        'CURRENCY_CODE': ['CNY', 'USD', 'HKD', 'EUR', 'CNY', 'USD', 'EUR', 'JPY', 'CNY', 'HKD', 'USD', 'CNY', 'USD', 'EUR', 'HKD', 'JPY', 'CNY', 'CNY', 'USD', 'HKD', 'CNY', 'CNY'],
        'CURRENCY_WEIGHT': [90, 5, 3, 2, 85, 8, 4, 3, 95, 4, 1, 70, 20, 5, 3, 2, 100, 92, 5, 3, 100, 100],
        'EXCHANGE_RATE': [1.0000, 7.2200, 0.9200, 7.8500, 1.0000, 7.2200, 7.8500, 0.0520, 1.0000, 0.9200, 7.2200, 1.0000, 7.2200, 7.8500, 0.9200, 0.0520, 1.0000, 1.0000, 7.2200, 0.9200, 1.0000, 1.0000],
        'ORGAN_KEY': ['103100000001'] * 4 + ['102100000001'] * 4 + ['104100000001'] * 3 + ['105100000001'] * 5 + ['301100000001', '307100000001', '307100000001', '307100000001', '306100000001', '308100000001'],
        'ORGAN_NAME': ['中国农业银行北京分行'] * 4 + ['中国工商银行上海分行'] * 4 + ['中国银行深圳分行'] * 3 + ['中国建设银行广州分行'] * 5 + ['招商银行杭州分行', '平安银行成都分行', '平安银行成都分行', '平安银行成都分行', '兴业银行武汉分行', '浦发银行西安分行'],
        'COUNTRY_CODE': ['CN'] * 21 + ['HK'] * 1,
        'AREA_CODE': ['110000'] * 4 + ['310000'] * 4 + ['440300'] * 3 + ['440100'] * 4 + ['999077'] * 1 + ['330100', '510100', '510100', '510100', '420100', '610100'],
        'AREA_NAME': ['北京市'] * 4 + ['上海市'] * 4 + ['深圳市'] * 3 + ['广州市'] * 4 + ['香港特别行政区'] * 1 + ['杭州市', '成都市', '成都市', '成都市', '武汉市', '西安市']
    }

    df = pd.DataFrame(data)
    return df

def main():
    """
    主函数：创建所有DataFrame并保存为CSV文件
    """
    print("开始创建DataFrame并生成CSV文件...")

    # 创建temp_organ_config表DataFrame（先创建，因为其他表需要引用它）
    print("创建temp_organ_config表DataFrame...")
    temp_organ_config_df = create_temp_organ_config_dataframe()

    # 创建temp_parties表DataFrame（引用temp_organ_config表）
    print("创建temp_parties表DataFrame...")
    temp_parties_df = create_temp_parties_dataframe(temp_organ_config_df)

    # 创建bb11_trans1表DataFrame（引用temp_parties表）
    print("创建bb11_trans1表DataFrame...")
    bb11_trans1_df = create_bb11_trans1_dataframe(temp_parties_df, 1000)

    # 保存为CSV文件
    print("保存CSV文件到", output_dir)
    bb11_trans1_df.to_csv(f'{output_dir}/bb11_trans1.csv', index=False, encoding='utf-8-sig')
    temp_parties_df.to_csv(f'{output_dir}/temp_parties.csv', index=False, encoding='utf-8-sig')
    temp_organ_config_df.to_csv(f'{output_dir}/temp_organ_config.csv', index=False, encoding='utf-8-sig')

    print("CSV文件生成完成！")
    print(f"文件列表:")
    print(f"- {output_dir}/bb11_trans1.csv ({len(bb11_trans1_df)}行)")
    print(f"- {output_dir}/temp_parties.csv ({len(temp_parties_df)}行)")
    print(f"- {output_dir}/temp_organ_config.csv ({len(temp_organ_config_df)}行)")

if __name__ == "__main__":
    main()

