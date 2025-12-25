#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
maskmark SDK默认内置规则
该文件包含了SDK的默认处理规则集合，在未收到指定规则时使用
"""

# 默认脱敏规则集合
DEFAULT_MASK_RULES = [
    {
        'RuleDes': '中文姓名脱敏规则（两个字：李#）',
        'Type': 'str',
        'Target': "^[\\u4e00-\\u9fa5]{2}$",
        'Method': 'mask',
        'Content': {'m_type': 're', 'char': '\\1#', 'pattern': '^(\\S)\\S$'}
    },
    {
        'RuleDes': '中文姓名脱敏规则（三字:张##）',
        'Type': 'str',
        'Target': "^[\\u4e00-\\u9fa5]{3}$",
        'Method': 'mask',
        'Content': {'m_type': 'text', 'char': '#', 'pattern': '\\S{2}$'}
    },
    {
        'RuleDes': '中文姓名脱敏规则（四字:宇文##）',
        'Type': 'str',
        'Target': "^[\\u4e00-\\u9fa5]{4}$",
        'Method': 'mask',
        'Content': {'m_type': 'text', 'char': '#', 'pattern': '\\S{2}$'}
    },
    {
        'RuleDes': '身份证号',
        'Type': 'str',
        'Target': '^[1-9]\\d{5}(18|19|([23]\\d))\\d{2}((0[1-9])|(10|11|12))(([0-2][1-9])|10|20|30|31)\\d{3}[0-9Xx]$',
        'Method': 'mask',
        'Content': {'m_type': 're', 'char': '\\1*********\\2', 'pattern': '^(\\d{6})\\d{9}(\\d{3})$'}
    },
    {
        'RuleDes': '手机号，满足三大运营商格式要求,遮蔽规则',
        'Type': 'str',
        'Target': '^(13[0-9]|14[5-9]|15[0-3,5-9]|16[2,5-7]|17[0-8]|18[0-9]|19[1,8,9])\\d{8}$',
        'Method': 'mask',
        'Content': {'m_type': 're', 'char': '\\1****\\2', 'pattern': '^(\\d{3})\\d{4}(\\d{4})$'}
    },
    {
        'RuleDes': '对任意整数值保留到指定位数',
        'Type': 'digit',
        'Target': '^-?\\d+$',
        'Method': 'round',
        'Content': {'place': -1}
    },
    {
        'RuleDes': '浮点数保留指定位数',
        'Type': 'digit',
        'Target': '^[-+]?\\d+\\.\\d*([eE][-+]?\\d+)?$',
        'Method': 'round',
        'Content': {'place': 1}
    },
    {
        'RuleDes': 'KV规则-基于已有规则-用户名',
        'Type': 'kv',
        'Target': 'user_name',
        'Method': 'rule',
        'Content': {'rule': '中文姓名脱敏规则（两个字：李#）'}
    },
    {
        'RuleDes': 'KV规则-内置规则-用户编号',
        'Type': 'kv',
        'Target': 'user_id',  # 假设为8位数字
        'Method': 'mask',
        'Content': {'m_type': 're', 'char': '\\1****\\2', 'pattern': '^(\\d{6})\\d*(\\d{4})$'}
    },
    {
        'RuleDes': 'KV规则-内置规则-电话',
        'Type': 'kv',
        'Target': 'phone',  # 假设为8位数字
        'Method': 'mask',
        'Content': {'m_type': 're', 'char': '\\1****\\2', 'pattern': '^(\\d{3})\\d*(\\d{4})$'}
    }
]

# 默认水印规则集合
DEFAULT_MARK_RULES = [
    {
        'RuleDes': '对图片添加水印',
        'Type': 'image',
        'Target': ".*\.png$",
        'Method': 'text',
        'Content': {'d': {'name': '测试员'}, 'template': '{name}-{Date}-{Time}'}
    },
    {
        'RuleDes': '对PDF添加水印',
        'Type': 'pdf',
        'Target': ".*\.pdf$",
        'Method': 'text',
        'Content': {'d': {'name': '测试员'}, 'template': '{name}-{Date}-{Time}'}
    },
    {
        'RuleDes': '对word添加水印',
        'Type': 'word',
        'Target': ".*\.docx$",
        'Method': 'text',
        'Content': {'d': {'name': '测试员'}, 'template': '{name}-{Date}-{Time}'}
    }
]

# 通用配置
COMMON_CONFIG = {
    'Version': 1.0
}

# 获取指定类型的默认规则
def get_default_rules(rule_type):
    """
    获取指定类型的默认规则
    
    :param rule_type: str, 规则类型，可选值：'mask'（脱敏规则）、'mark'（水印规则）
    :return: list, 对应类型的默认规则列表
    """
    if rule_type == 'mask':
        return DEFAULT_MASK_RULES.copy()
    elif rule_type == 'mark':
        return DEFAULT_MARK_RULES.copy()
    else:
        return []

# 获取默认的通用配置
def get_common_config():
    """
    获取默认的通用配置
    
    :return: dict, 通用配置
    """
    return COMMON_CONFIG.copy()