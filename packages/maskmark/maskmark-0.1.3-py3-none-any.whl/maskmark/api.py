#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project ：maskmark_py
@File    ：api.py
@IDE     ：PyCharm
@Author  ：Handk
@Date    ：2025/2/21 17:04
@Describe：应用层函数集合，提供给外部的调用API
"""

import json
from .engine.rule_engine import R_Engine
import filetype
from .utils.util import is_json


class DataMaskingSDK:
    """
    数据脱敏SDK
    """

    def __init__(self, rule_file=None):
        self.eng = R_Engine(rule_file)

    def mask(self, data, rule=None):
        """脱敏入口函数

        :param data: 输入数据
        :param rule: 该数据指定使用的规则，此规则优先级高于配置文件中的规则
        :return:处理结果
        """

        # 判断数据类型，决定选用哪一类规则进行匹配
        # 如果为json字符串
        if is_json(data):
            # 将json字符串转化为字典
            kv_data = json.loads(data)
            # 将返回结果转为json字符串
            return json.dumps(self.eng.handle_mask(kv_data, "kv",rule),ensure_ascii=False)
        # 如果为字符串
        if isinstance(data, str):
            return self.eng.handle_mask(data, "str",rule)
        # 如果为数字
        if isinstance(data, int) or isinstance(data, float):
            return self.eng.handle_mask(data, "digit",rule)
        # 如果为字典
        if isinstance(data, dict):
            return self.eng.handle_mask(data, "kv",rule)
        # 如果为其他类型则认为不支持
        raise TypeError("数据类型不支持")



class DataMarkingSDK:
    """
    水印处理SDK
    """

    def __init__(self, rule_file=None):
        self.eng = R_Engine(rule_file)

    def mark(self, file_path,rule=None):
        """
        水印处理函数
        :param file_path: 文件路径
        :return: 处理结果，0代表成功，1代表失败
        """
        # 如果指定规则，则将文件路径作为规则中的Target
        if rule:
            rule["Target"] = file_path
        
        # 判断文件类型
        file_kind = filetype.guess(file_path)
        if file_kind is None:
            raise ValueError(f"未知的文件{file_path}")
        if "image" in file_kind.mime:
            return self.eng.handle_mark(file_path, "image",rule)
        if "pdf" in file_kind.mime:
            return self.eng.handle_mark(file_path, "pdf",rule)
        if "word" in file_kind.mime:
            return self.eng.handle_mark(file_path, "word",rule)
        raise ValueError(f'不支持的文件{file_path}')
