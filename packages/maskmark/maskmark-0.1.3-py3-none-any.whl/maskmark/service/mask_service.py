#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project ：maskmark_py
@File    ：mask_service.py
@IDE     ：PyCharm
@Author  ：Handk
@Date    ：2025/3/12 19:56
@Describe：服务层脱敏函数集合，利用底层算法实现一系列能力
"""
from .interface import ServiceInterface
from ..core.mask import *


class Mask_str(ServiceInterface):
    def handle(self, string, rule):
        """
        对字符串的脱敏
        :param string: 待处理的字符串
        :param rule: 脱敏规则
        :return: 处理后的字符串
        """
        # 根据规则类型判断要调用的核心算法
        rule_type = rule.get("Method")

        # 替换脱敏
        if rule_type == "mask":
            if rule['Content'].get("pattern") is None:
                rule['Content']["pattern"] = rule.get("Target")
            return self.handle_mask(string, rule.get("Content"))
        # 哈希处理
        if rule_type == "hash":
            return self.handle_hash(string, rule.get("Content"))
        # 截取处理
        if rule_type == "truncate":
            return self.handle_truncate(string, rule.get("Content"))
        print('不支持的规则类型')
        return string

    def handle_mask(self, string, rule):
        """
        遮蔽处理
        :param string: 输入字符串
        :param rule: 处理规则，字典形式，必须包含char(遮蔽字符)、m_type(遮蔽方式)、pattern(遮蔽部分)
        :return: 处理后的字符串
        """
        # 遮蔽字符
        char = rule.get("char")
        # 遮蔽方式
        method = rule.get("m_type")
        # 遮蔽部分
        pattern = rule.get("pattern")

        if None in [char, method, pattern]:
            raise KeyError("字符串脱敏规则配置缺失，请检查")

        if method not in ["text", "re"]:
            raise ValueError("字符串脱敏规则配置值异常，请检查")

        # 基于文本，逐个替换
        if method == "text":
            # 创建正则表达式对象
            pattern_regex = re.compile(pattern)
            # 待替换的字符串部分
            match_str = re.findall(pattern_regex, string)
            # 默认匹配结果唯一，则根据第一个元素的长度生成新的替换字符
            char = len(match_str[0]) * char
            return mask(string, char, pattern_regex)

        # 基于正则表达式替换
        pattern_regex = re.compile(pattern)
        return mask(string, char, pattern_regex)

    def handle_hash(self, string, rule):
        """
        hash处理
        :param string: 输入字符串
        :param rule: 处理规则，字典形式，必须包含hash_type(哈希算法类型)
        :return: 处理后的字符串
        """
        # 哈希算法类型
        hash_type = rule.get("hash_type")
        if hash_type is None:
            raise KeyError("字符串脱敏规则配置缺失，请检查")

        # 调用核心算法
        return hash(string, hash_type)
    
    def handle_truncate(self, string, rule):
        """
        截取处理
        :param string: 输入字符串
        :param rule: 处理规则，字典形式，必须包含start(保留数据开始位置)、end(保留数据结束位置)
        :return: 处理后的字符串
        """
        # 判断规则是否合法
        # 截取的保留数据开始位置和结束位置不能同时缺失
        if "start" not in rule and "end" not in rule:
            raise KeyError("截取脱敏规则配置未指定截取范围，请检查")
        # 保留数据开始位置，未指定则从头开始
        start = rule.get("start", 0)
        # 保留数据结束位置，未指定则保留到字符串末尾
        end = rule.get("end", len(string))
        if start>end:
            raise ValueError("截取脱敏规则配置值异常，请检查")
        # 调用核心算法截取字符串
        # 如果配置了反选标志，则保留start~end之外的部分
        if rule.get("inverse"):
            return inverse_truncate(string, start, end)
        # 否则保留start~end之间的部分
        return truncate(string, start, end)


class Mask_digit(ServiceInterface):
    def handle(self, data, rule):
        """
        对数值型数据进行脱敏
        :param data: 数值数据
        :param rule: 脱敏规则
        :return: 处理后的数据
        """

        # 根据规则类型判断要调用的核心算法
        rule_type = rule.get("Method")

        # 取位脱敏
        if rule_type == "round":
            return self.handle_round(data, rule.get("Content"))
        # 偏移量脱敏
        if rule_type == "offset":
            return self.handle_offset(data, rule.get("Content"))
        # 哈希脱敏
        if rule_type == "hash":
            return self.handle_hash(data, rule.get("Content"))

    def handle_round(self, data, rule):
        """
        取位
        :param data: 数值数据
        :param rule: 脱敏规则
        :return: 处理后的数据
        """
        place = rule.get("place")
        if place == 0:
            return data
        return round_mask(data, place)

    def handle_offset(self, data, rule):
        """
        偏移处理
        :param data:
        :param rule:
        :return:
        """
        offset = rule.get("offset")
        if offset is None:
            raise KeyError("数值脱敏规则偏移处理配置缺失，请检查")
        return offset(data, offset)

    def handle_hash(self, data, rule):
        """
        哈希处理
        :param data: 数值数据
        :param rule: 脱敏规则，必须包含hash_type(哈希算法类型)
        :return: 处理后的数据
        """
        # 哈希算法类型
        hash_type = rule.get("hash_type")
        if hash_type is None:
            raise KeyError("数值脱敏规则配置缺失，请检查")

        # 调用核心算法
        return hash(data, hash_type)


class Mask_log(ServiceInterface):
    def handle(self, log_file_path, rule):
        """
        对日志文件中的内容进行脱敏
        :param log_file_path: 日志文件路径
        :param rule: 脱敏规则
        :return: 是否完成脱敏，0代表完成，1代表异常
        """
        pass


class Mask_kv(ServiceInterface):
    def handle(self, kv, rule):
        """
        对kv类型数据的脱敏，注意仅对值进行处理
        :param kv: 待处理的KV类型
        :param rule: 脱敏规则
        :return: 处理后的KV类型数据
        """
        # 空值直接返回
        if kv is None:
            return kv
        # 检查规则是否包含目标键
        if rule.get("Target") is None:
            raise KeyError("脱敏规则配置缺失，请检查")
        # 根据kv_value的类型，调用对应的处理函数
        kv_value = kv.get(rule.get("Target"))
        # 字符串类型
        if isinstance(kv_value, str):
            kv[rule.get("Target")] = mask_str_service.handle(kv_value, rule)
        # 数值类型
        if isinstance(kv_value, int) or isinstance(kv_value, float):
            kv[rule.get("Target")] = mask_digit_service.handle(kv_value, rule)
        # 其他类型无法处理，直接返回原值
        return kv


class Mask_json(ServiceInterface):
    def handle(self, json_data, rule):
        """
        对json类型数据的脱敏
        :param json_data: 待处理的json数据
        :param rule: 脱敏规则
        :return: 处理后的json数据
        """
        pass



# 脱敏服务注册
mask_str_service = Mask_str()
mask_kv_service = Mask_kv()
mask_json_service = Mask_json()
mask_log_service = Mask_log()
mask_digit_service = Mask_digit()
