from tpf.conf import ParamConfig
pc = ParamConfig()
import pandas as pd 
identity = ['ACCT_NUM','PARTY_ID','OPP_PARTY_ID','ACCT','TCAC','TSTM']
cols = ['ACCT_NUM','PARTY_ID','OPP_PARTY_ID','ACCT','TCAC','TSTM', 'DT_TIME', 'PARTY_CLASS_CD',   'CCY', 'AMT',   'AMT_VAL','CNY_AMT','ACCBAL', 'DEBIT_CREDIT','CASH_FLAG', 'OPP_ORGANKEY', 'OACCTT', 'DT_TIME', 'OTBKAC', 'CHANNEL', 'RMKS',  'CBCDIR', 'AMTFLG', 'BALFLG', 'CNY_AMT', 'ACCBAL', 'RMKCDE', 'TDDS', 'RCDTYP', 'CCY_A', 'INTAMT_A', 'INTRAT_A',  'PBKTYP', 'CNT_CST_TYPE', 'CNT_INBANK_TYPE', 'CFRC_COUNTRY', 'CFRC_AREA', 'TRCD_AREA', 'TRCD_COUNTRY', 'TXTPCD',   'RCVPAYFLG', 'SYS_FLAG', 'TXN_CHNL_TP_ID', 'FLAG',  'OVERAREA_IND']
num_type = ['AMT', 'AMT_VAL','CNY_AMT','ACCBAL','INTAMT_A', 'INTRAT_A']


data_file = "/ai/wks/leadingtek/scripts/tra11.csv"
df = pd.read_csv(data_file,usecols=cols)
df = df[cols]
pc.lg(f"df.head():\n{df.head()}")

