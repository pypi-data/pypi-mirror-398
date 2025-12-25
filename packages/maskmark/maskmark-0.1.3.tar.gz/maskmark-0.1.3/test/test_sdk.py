#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
SDK测试脚本
验证maskmarkSDK是否能正常导入和使用
"""

from maskmark import DataMaskingSDK, DataMarkingSDK

print("测试开始：验证maskmarkSDK导入和基本功能")
print(f"成功导入DataMaskingSDK: {DataMaskingSDK}")
print(f"成功导入DataMarkingSDK: {DataMarkingSDK}")

# 尝试创建实例
try:
    masking_sdk = DataMaskingSDK()
    marking_sdk = DataMarkingSDK()
    print("成功创建SDK实例！")
    print("测试成功完成！")
except Exception as e:
    print(f"创建SDK实例时出错: {e}")
    print("测试失败。")

sdk=DataMarkingSDK()

result=sdk.mark("./test_file/test.pdf")
print(result)
