import datetime
import time
from typing import Literal

def get_local_now_date():
    '''获取电脑当前时间'''
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
def update_date(date,cycle:Literal['days','minutes','seconds','hours'],num,format='%Y-%m-%d %H:%M:%S'):
    '''
    日期增加或者减少 天 分 秒 时
    :date 日期
    :cycle ['days','minutes','seconds','hours']
    :num 增加或者减少的数量 +1 -1
    '''
    now = datetime.datetime.strptime(date, format)
    date = (now + datetime.timedelta(**{cycle:num})).strftime(format)
    return date