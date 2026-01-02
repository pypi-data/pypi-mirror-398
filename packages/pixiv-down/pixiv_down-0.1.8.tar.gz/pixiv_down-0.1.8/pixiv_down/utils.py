import json
import logging
import time
from functools import wraps
from typing import Literal

from pixivpy3.utils import JsonDict
from zhconv_rs import is_hans

JP_CHR = (
    {chr(i) for i in range(0x3041, 0x3097)}
    | {chr(i) for i in range(0x309D, 0x30FB)}
    | {chr(i) for i in range(0x30FC, 0x30FF)}
    | {chr(i) for i in range(0x31F0, 0x31FF)}
)


def jp_chars(word: str) -> set[str]:
    """单词中的日文字符"""
    return JP_CHR & set(word)


def is_chars(word: str) -> bool:
    """判断是否是普通字符"""
    return all(ord(c) < 0x2E81 for c in word)  # 从 0x2e81 出现中、日、韩等文字


def get_lang(word: str) -> Literal['en', 'jp', 'hans', 'hant']:
    """获取字符语言"""
    if is_chars(word):
        return 'en'
    elif jp_chars(word):
        return 'jp'
    elif is_hans(word):
        return 'hans'
    else:
        return 'hant'


def params_to_str(args=None, kwargs=None):
    """将参数格式化为字符串"""
    s = ''
    if args:
        s += ', '.join(f'{a}' for a in sorted(args))
    if kwargs:
        if s:
            s += ', '
        s += ', '.join(f'{k}={v}' for k, v in sorted(kwargs.items()))
    return s


def singleton(cls):
    """单例装饰器"""
    instance = None

    @wraps(cls)
    def deco(*args, **kwargs):
        nonlocal instance
        if instance is None:
            instance = cls(*args, **kwargs)
        return instance

    return deco


def retry(checker=None, exceptions=(Exception,)):
    """
    @checker: 结果检查器，Callable 对象。接收被装饰函数的结果作为参数，返回 True 时进行重试
    @exceptions: 指定异常发生时，自动重试
    """

    def deco(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            seconds = [5, 10, 15, 30, 30, 30, 60, 60, 120]  # 总时长 6 分钟
            for n in seconds:
                try:
                    result = func(*args, **kwargs)
                    if callable(checker):
                        checker(result)
                    return result
                except exceptions as e:
                    logging.error(f'retry after {n} sec due to `{e.__class__.__name__}: {e}`.')
                    time.sleep(n)
                    continue
            else:
                s_arg = params_to_str(args, kwargs)
                logging.error(f'Retry Failed: {func.__name__}({s_arg})')

        return wrapper

    return deco


def save_jsonfile(data, filename: str, compress=True):
    if not filename:
        raise ValueError('`filename` can not be null.')
    if not filename.endswith('.json'):
        filename = f'{filename}.json'
    with open(filename, 'w') as fp:
        if compress:
            json.dump(data, fp, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
        else:
            json.dump(data, fp, ensure_ascii=False, sort_keys=True, indent=4)


def print_json(json_data: str | bytes | dict, keys=()):
    """打印 JSON 数据"""
    if isinstance(json_data, (str, bytes)):
        j_dict = JsonDict(json.loads(json_data))
    else:
        j_dict = JsonDict(json_data)

    if 'ALL' in keys:
        json_str = json.dumps(j_dict, sort_keys=True, indent=4, ensure_ascii=False)
        print(json_str)
    else:
        for k in keys:
            v = j_dict.get(k)
            if isinstance(v, (dict, list)):
                v = json.dumps(v, sort_keys=True, indent=4, ensure_ascii=False)
            print(f'{k} = {v}')
