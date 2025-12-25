#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project ：maskmark_py
@File    ：mask.py
@IDE     ：PyCharm
@Author  ：Handk
@Date    ：2025/2/21 19:03
@Describe：脱敏算法包
"""

import hashlib
import random
import re
import string

from gmssl import sm3, func


def mask(data, mask_char='*', pattern=None):
    """
    遮蔽的底层实现
    :param data: 输入的字符串
    :param mask_char: 遮蔽所用的替换符
    :param pattern: 应遮蔽的部分，应为正则表达式对象
    :return: 处理结果
    """
    return re.sub(pattern, mask_char, data)


def hash(data, algorithm='sha256'):
    """
    哈希处理的底层实现
    :param data: 输入的字符串
    :param algorithm: 哈希算法，支持SHA256，SM3
    :return: 处理结果
    """
    data = str(data)
    if algorithm.lower() not in ['sha256', 'sm3']:
        raise ValueError('不支持的哈希算法')
    if algorithm.lower() == 'sm3':
        # SM3算法需要将数据转换为字节列表,对于字符数据，直接调用encode,对于数值数据，先转换为字符串
        data = str(data).encode('utf-8')
        # 使用gmssl库的sm3函数进行哈希计算，返回结果为字符串
        return sm3.sm3_hash(func.bytes_to_list(data))
    hash_func = getattr(hashlib, algorithm)
    return hash_func(data.encode()).hexdigest()


def randomize(data, length=0):
    """
    替换为随机字符
    :param length: 随机字符串长度，0代表和输入数据长度一致
    :param data:输入数据
    :return:随机字符串长度
    """
    if length == 0:
        return ''.join(random.choice(string.ascii_letters) for _ in range(len(data)))
    return ''.join(random.choice(string.ascii_letters) for _ in range(length))


def truncate(data, start, end):
    """
    截断处理的底层实现
    :param data: 数据
    :param start: 保留数据开始位置
    :param end: 保留数据停止位置
    :return: 处理结果
    """
    return data[start:end]

def inverse_truncate(data, start, end):
    """
    逆截断处理的底层实现
    :param data: 数据
    :param start: 头部数据保留结束位置
    :param end: 尾部数据保留开始位置
    :return: 处理结果
    """
    return data[:start] + data[end:]


def offset(value, offset):
    """
    对数值加上或减去一个固定偏移量。

    :param value: float or int, 待脱敏的原始数值
    :param offset: float or int, 偏移量
    :return: float or int, 脱敏后的数值
    """
    return value + offset


def round_mask(value, digits):
    """
    将数值数据保留到指定位数
    :param value: float or int
    :param digits: 指定位数，1代表第一个小数位，0代表取整，-1代表个位，以此类推
    :return: 处理后的数据
    """
    return round(value, digits)
