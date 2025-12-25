#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
测试maskmark SDK的默认内置规则功能
该脚本用于验证当未指定规则文件时，SDK是否能正确使用默认内置规则
"""
from maskmark import DataMaskingSDK
import os
import tempfile


def test_default_mask_rules():
    """
    测试默认脱敏规则是否正常工作
    """
    print("\n=== 测试默认脱敏规则 ===")
    
    # 创建临时目录并切换到该目录，确保没有conf.toml和rule.toml文件
    with tempfile.TemporaryDirectory() as temp_dir:
        original_dir = os.getcwd()
        os.chdir(temp_dir)
        
        try:
            # 检查临时目录中是否有配置文件
            print(f"当前测试目录: {temp_dir}")
            print(f"目录内容: {os.listdir(temp_dir)}")
            
            # 创建SDK实例（应该使用默认规则）
            print("\n创建DataMaskingSDK实例...")
            sdk = DataMaskingSDK()
            print("SDK实例创建成功！")
            
            # 测试中文姓名脱敏
            name1 = "张三"
            name2 = "李四三"
            name3 = "欧阳修"
            masked_name1 = sdk.mask(name1)
            masked_name2 = sdk.mask(name2)
            masked_name3 = sdk.mask(name3)
            print(f"\n中文姓名脱敏测试:")
            print(f"原始姓名: {name1} -> 脱敏后: {masked_name1}")
            print(f"原始姓名: {name2} -> 脱敏后: {masked_name2}")
            print(f"原始姓名: {name3} -> 脱敏后: {masked_name3}")
            
            # 测试手机号脱敏
            phone = "13812345678"
            masked_phone = sdk.mask(phone)
            print(f"\n手机号脱敏测试:")
            print(f"原始手机号: {phone} -> 脱敏后: {masked_phone}")
            
            # 测试身份证号脱敏
            id_card = "110101199001011234"
            masked_id_card = sdk.mask(id_card)
            print(f"\n身份证号脱敏测试:")
            print(f"原始身份证号: {id_card} -> 脱敏后: {masked_id_card}")
            
            # 测试数字保留位数
            number = 1234.5678
            masked_number = sdk.mask(number)
            print(f"\n数字保留位数测试:")
            print(f"原始数字: {number} -> 处理后: {masked_number}")
            
            # 测试字典类型数据
            user_data = {"user_name": "张三", "user_id": "110101199001011234", "phone": "13812345678"}
            masked_user_data = sdk.mask(user_data.copy())
            print(f"\n字典数据脱敏测试:")
            print(f"原始数据: {user_data}")
            print(f"脱敏后: {masked_user_data}")
            
            # 测试JSON字符串类型数据
            json_data = '{"user_name": "李四", "user_id": "110101199001011234", "phone": "13812345678"}'
            masked_json_data = sdk.mask(json_data)
            print(f"\nJSON字符串数据脱敏测试:")
            print(f"原始数据: {json_data}")
            print(f"脱敏后: {masked_json_data}")
            
            print("\n=== 测试完成 ===")
            return True
        except Exception as e:
            print(f"\n测试失败: {e}")
            return False
        finally:
            # 切换回原始目录
            os.chdir(original_dir)


if __name__ == "__main__":
    success = test_default_mask_rules()
    print(f"\n默认规则测试{'成功' if success else '失败'}")