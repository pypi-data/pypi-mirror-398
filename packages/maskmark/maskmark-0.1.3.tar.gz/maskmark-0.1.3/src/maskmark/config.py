#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project ：maskmark_py
@File    ：config.py
@IDE     ：PyCharm
@Author  ：Handk
@Date    ：2025/2/21 18:41
@Describe：配置层函数集合，提供：
        1. 默认配置或读取外部配置
        2. 负责对不同类型的数据寻找对应的脱敏或水印方法，以及方法对应的参数
"""
import toml
import os
from .default_rules import get_default_rules, get_common_config


def load_toml_config(file_path):
    """
    从指定的文件路径加载TOML配置文件。

    :param file_path: str, 配置文件的路径
    :return: dict, 解析后的配置信息
    """
    with open(file_path, 'r', encoding='utf-8') as file:
        config = toml.load(file)
    check_config(config)
    return config


def check_config(config_object):
    """
    检查配置是否合法

    :param config_object：配置对象
    :return 配置是否合法，0代表合法，1代表存在错误
    """
    # TODO:检查配置文件
    return 0


class Conf:
    """
    配置管理类
    """

    def __init__(self, config_file=None):
        # 水印配置
        self.mark_config = None
        # 脱敏配置
        self.mask_config = None
        # 公共配置
        self.common_config = None

        self.load_conf(config_file)

    def load_conf(self, config_file,debug=False):
        """
        载入新的配置
        :param config_file: 配置文件路径
        """
        # 检查配置文件是否存在
        if config_file is not None and os.path.exists(config_file):
            try:
                self.all_config = load_toml_config(config_file)
                if check_config(self.all_config):
                    raise ValueError("规则配置文件不合法，请检查配置文件")
                self.mask_config = self.all_config.get("MaskRule")
                self.mark_config = self.all_config.get("MarkRule")
                # 正常情况下两者必不相等，若相等说明没有配置文件
                # 有两种可能：1. 用户忘记添加配置了；2. 用户在调用时临时指定了配置
                # 综上这里仅作提示
                if self.mark_config == self.mask_config:
                    print("检测到规则配置文件脱敏配置为空")
            except Exception as e:
                print(f"加载规则配置文件失败: {e}\n使用默认内置规则")
                self._load_default_rules()
        else:
            if debug:
                print(f"规则配置文件 {config_file} 不存在，使用默认内置规则")
            self._load_default_rules()
            
    def _load_default_rules(self):
        """
        加载默认内置规则
        """
        self.common_config = get_common_config()
        self.mask_config = get_default_rules('mask')
        self.mark_config = get_default_rules('mark')

    def filtered_conf(self, rule_class=None, rule_des=None, rule_type="all") -> list:
        """
        根据条件筛选返回合适的配置。
        :param rule_class: 规则种类（mask/mark）
        :param rule_des: 规则描述，用于搜索特定的某条规则
        :param rule_type: 规则适用的数据类型
        :return: 
        """
        # 当存在rule_des时，说明函数需要根据规则描述搜索对应规则
        if rule_des is not None:
            # 在水印规则中遍历
            for rule in self.mark_config:
                # 匹配到目标规则
                if rule.get("RuleDes") == rule_des:
                    return [rule]
            # 在脱敏规则中遍历
            for rule in self.mask_config:
                # 匹配到目标规则
                if rule.get("RuleDes") == rule_des:
                    return [rule]
            # 若未指定规则描述，报错
            raise ValueError(f"未找到规则描述为 {rule_des} 的规则")

        # 检查参数合法性
        if rule_class not in ["mask", "mark"]:
            raise ValueError("rule_class 必须为 \"mask\" 或 \"mark\"")
        if rule_type not in ["all", "kv", "str", "json", "digit", "image", "pdf", "word"]:
            raise ValueError("rule_type 参数有误")

        filtered_rule = []
        # 对于脱敏水印
        if rule_class == "mask":
            if self.mask_config is None:
                raise ValueError("脱敏配置为空，请检查配置文件")
            for mask_rule in self.mask_config:
                # 规则适用场景为所有或与目标场景匹配，则加入返回结果中
                if mask_rule.get('Type') in ['all', rule_type]:
                    filtered_rule.append(mask_rule)
        if rule_class == "mark":
            if self.mark_config is None:
                raise ValueError("水印配置为空，请检查配置文件")
            for mark_rule in self.mark_config:
                if mark_rule.get('Type') == rule_type:
                    filtered_rule.append(mark_rule)

        return filtered_rule
