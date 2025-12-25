import json
import re


def is_json(data):
    """
    判断是否为json数据
    """
    try:
        json_object = json.loads(data)
        # 判断解析结果是否为字典类型，排除字符串内全部为数字的情况
        if isinstance(json_object,dict):
            return True
    except Exception:
        return False

def check_rule(data_type,rule:dict):
    # 确保适用类型、规则目标、规则方法存在
    if {'Type', 'Target', 'Method'}.issubset(rule.keys()):
        if rule.get('Type')==data_type:
            return True
    return False

def kv_handle(rule_list, kv_data, rule_map,config_manager):
    """
    对kv数据选择合适的处理规则进行处理
    """
    # 遍历kv数据
    for key in kv_data.keys():
        # 值为kv数据，递归处理
        if isinstance(kv_data[key],dict):
            kv_handle(rule_list,kv_data[key],rule_map,config_manager)
            continue

        # 值为一般数据
        # 遍历可处理键值对数据的规则列表
        for type_rule in rule_list:
            # 判断规则是否适用
            if type_rule.get("Target")==key:
                # 基于规则描述所指定的现有规则处理
                if type_rule.get("Method") == "rule":
                    rule_des = type_rule.get("Content").get("rule")
                    # 找到规则描述对应的规则,默认规则描述只对应一个规则
                    result = config_manager.filtered_conf(rule_des=rule_des)
                    if len(result)>0:
                        # 规则描述对应的规则存在，将其内容作为规则
                        item_rule=result[0]
                        # 整合规则
                        rule = {'Target': type_rule['Target'], 'Method': item_rule["Method"],
                            'Content': item_rule["Content"]}
                    else:
                        raise ValueError("选取的规则不存在")
                else:
                    # 直接使用规则内容作为规则
                    rule = {'Target': type_rule.get('Target'), 'Method': type_rule.get("Method"),
                            'Content': type_rule.get("Content")}
                # 将规则传递给处理函数,返回结果替换目标键对应的值
                kv_data = rule_map['kv'].handle(kv_data, rule)
    # kv数据处理完毕，返回所有处理后的结果
    return kv_data

def std_type_handle(rule_list, data, rule_map,data_type):
    for type_rule in rule_list:
        # 判断规则是否适用
        try:
            is_target_match = re.fullmatch(re.compile(type_rule.get("Target")), str(data))
        except Exception as e:
            ValueError(f'错误类型:{type(e)},记录:[{type_rule.get("Target")},{data}]')
            return None
        # 对于匹配的规则，根据规则调用函数处理
        if is_target_match:
            rule = {'Target': type_rule.get('Target'), 'Method': type_rule.get("Method"),
                    'Content': type_rule.get("Content")}
            return rule_map[data_type].handle(data, rule)
    # 若无匹配规则，抛出异常
    raise ValueError("无匹配的脱敏规则")