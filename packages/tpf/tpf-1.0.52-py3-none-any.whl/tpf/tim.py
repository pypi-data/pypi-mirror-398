import time
from datetime import datetime


def month_before(n=1):
    """N月以前
    - 以12为进制计算年月
    - 202308 1月以前就是202307 
    
    测试
    ------------------ 
    当前时间:2023-08 

    month_before(n=1)
    '202307'

    month_before(n=7)
    '202301'

    month_before(n=8)
    '202212'

    month_before(n=12)
    '202208'

    month_before(n=20)
    '202112'

    """
    t = time.localtime(time.time())
    year=t[0]
    month=t[1]
    interval = n 
    
    interval_month = interval%12
    interval_month
    if interval <= month:
        new_month = month - interval
        new_year = year
        if new_month == 0 :
            new_year = year - 1 
            new_month = 12
    else:
        new_month = month - interval  
        interval_year  = int((0-new_month)/12)
        new_year = year - (interval_year+1)
        new_month = new_month%12
        if new_month == 0 :
            new_month = 12
        
    res = "{}{}".format(new_year, '%02d'%new_month)
    return res 


def current_time():
    tim = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))
    return tim 

def hms():
    tim = time.strftime('%H%M%S',time.localtime(time.time()))
    return tim 

def tim1():
    t1 = datetime.now()
    print(t1)
    return t1 


def diff_second(starttime,message=None):
    """
    时间距离tim1的秒数
    """
    endtime = datetime.now()
    t2 = (endtime - starttime).seconds
    print("[use seconds]: ",t2)
    print("\n")
    return endtime


def format_hms(seconds):
    """将秒转化为时分秒"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{seconds:05.2f}"



