#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project ：maskmark_python 
@File    ：rule_engine.py
@IDE     ：PyCharm 
@Author  ：Handk
@Date    ：2025/3/31 15:21 
@Describe：规则引擎，实现根据规则的决策
"""
from ..config import Conf
from ..service.mark_service import *
from ..service.mask_service import *
from ..utils.util import *

# 处理路由表
rule_map = {
    "str"  : mask_str_service,
    "kv"   : mask_kv_service,
    "json" : mask_json_service,
    "log"  : mask_log_service,
    "digit": mask_digit_service,
    "image": mark_image_service,
    "pdf"  : mark_pdf_service,
    "word" : mark_word_service,
}


class R_Engine:
    """
        规则引擎类
    """

    def __init__(self, rule_file=None):
        self.configer = Conf(rule_file)

    def handle_mask(self, data, data_type=None, rule=None):
        """
        脱敏策略决策函数
        :param data: 输入数据
        :param data_type: 数据类型
        :param rule: 优先使用的规则
        :return: 处理后的数据
        """
        # 如果存在指定规则
        if rule:
            # 判断规则是否适用
            if check_rule(data_type,rule):
                # 如果适用，直接调用对应的处理函数
                return rule_map[data_type].handle(data, rule)
            # 如果规则不适用，抛出异常
            raise ValueError("指定规则有误")
        # 如果没有指定规则，则根据数据类型获取对应的规则   
        else:
            # 符合对应数据类型的规则
            type_rule_list = self.configer.filtered_conf(rule_class="mask", rule_type=data_type)
            if type_rule_list is None:
                raise TypeError("无匹配的脱敏规则")

            # 对于字符串、数字类型等简单数据，进行常规规则匹配
            if data_type in ["str", "digit"]:
                return std_type_handle(type_rule_list,data,rule_map,data_type)

            # 对于字典类型数据，根据键名匹配规则
            if data_type == "kv":
                return kv_handle(type_rule_list, data,rule_map,self.configer)
            return data

    def handle_mark(self, file_path, file_type,rule=None):
        """
        水印策略决策函数
        :param file_path: 文件路径
        :param file_type: 文件类型
        :param rule: 优先使用的规则
        :return: 是否成功处理，0代表完成，1代表存在异常
        """
        # 如果存在指定规则
        if rule:
            # 判断规则是否适用
            if check_rule(file_type, rule):
                # 如果适用，直接调用对应的处理函数
                return rule_map[file_type].handle(file_path, rule)
            # 如果规则不适用，抛出异常
            raise ValueError("指定规则不适用于此文件类型")
        # 如果没有指定规则，则根据数据类型获取对应的规则
        else:
            # 根据文件类型寻找符合对应场景的规则
            rule_list = self.configer.filtered_conf("mark", rule_type=file_type)
            if rule_list is None:
                raise TypeError("无水印规则匹配该文件类型")
            for rule in rule_list:
                # 判断规则是否适用
                try:
                    is_target_match = re.search(re.compile(rule.get("Target")), file_path)
                except Exception as e:
                    print(f'错误类型:{type(e)},记录:[{rule.get("Target")},{file_path}]')
                if is_target_match:
                    rule = {"Method":rule.get("Method"),"Content":rule.get("Content")}
                    return rule_map[file_type].handle(file_path, rule)
            raise ValueError("无水印规则匹配该文件")
