import math
import re

def subset(data:list,size:int):
    '''切片列表'''
    Maxpage = math.ceil(len(data) / size)
    for page in range(Maxpage):
        b = data[page * size:(page + 1) * size]
        yield b

def draw_chinese(str_data):
    '''提取字符串中的 汉字'''
    return ''.join(re.findall('[\u4e00-\u9fa5]',str_data))

def del_chinese(str_data):
    '''删除字符串中的 汉字'''
    return re.sub('[\u4e00-\u9fa5]','',str_data)