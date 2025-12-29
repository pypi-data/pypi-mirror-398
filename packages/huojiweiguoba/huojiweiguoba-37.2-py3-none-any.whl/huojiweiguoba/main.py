import hashlib

def inspect_none(data,return_bool = False):
    '''检测是否有空值'''
    if data:
        if return_bool:
            return True
        else:
            return data
    else:
        if return_bool:
            return False
        else:
            return None

def md5_encrypt(data):
    '''md5加密'''
    md5 = hashlib.md5()
    md5.update(data.encode('utf-8'))
    return md5.hexdigest()