# -*- coding:utf-8 -*-
# ProjectName：huojiweiguoba
# FileName：decorator.py
# Time：2025/7/15 上午9:22
# Author：侯文杰
# IDE：PyCharm
import time
import functools
from typing import List, Dict

def retry(max_retries: int = 3, wait_time: float = 1, exception_items: List[Dict] = None):
    """
    请求重试装饰器
    :param max_retries: 最大重试次数
    :param wait_time: 每次重试等待时间(秒)
    :param exception_items: 异常匹配规则列表
    """
    if exception_items is None:
        exception_items = []
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            retries = 0
            last_exception = None
            while retries <= max_retries:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    print(f"[retry]装饰器，重试次数：{retries}-{str(e)}")
                    last_exception = e
                    should_retry = False
                    # 检查异常是否匹配任何规则
                    for item in exception_items:
                        type_match,msg_match = False,False
                        # 检查异常类型
                        if "error_type" in item:
                            if isinstance(e, item["error_type"]):
                                type_match = True
                        else:
                            type_match = True
                        # 检查异常消息
                        if "error_msg" in item:
                            if item["error_msg"] in str(e):
                                msg_match = True
                        else:
                            msg_match = True
                        # 检查异常消息
                        if type_match and msg_match:
                            should_retry = True
                            break
                    # 如果没有匹配任何规则，则不再重试
                    if not should_retry:
                        raise e
                    retries += 1
                    if retries <= max_retries:
                        time.sleep(wait_time)
            # 重试次数用尽，抛出最后捕获的异常
            raise last_exception
        return wrapper
    return decorator