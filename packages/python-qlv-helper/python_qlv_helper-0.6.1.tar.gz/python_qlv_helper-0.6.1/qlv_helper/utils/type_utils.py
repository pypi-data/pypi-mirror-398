# -*- coding: utf-8 -*-
"""
# ---------------------------------------------------------------------------------------------------------
# ProjectName:  qlv-helper
# FileName:     type_utils.py
# Description:  数据类型工具模块
# Author:       zhouhanlin
# CreateDate:   2025/12/01
# Copyright ©2011-2025. Hunan xxxxxxx Company limited. All rights reserved.
# ---------------------------------------------------------------------------------------------------------
"""
import re
from collections import OrderedDict
from typing import Any, Optional, Dict


def get_key_by_index(ordered_dict: OrderedDict, index: int) -> Optional[str]:
    """有序字段根据索引获取值"""
    if index < 0 or index >= len(ordered_dict):
        return None
    return list(ordered_dict.keys())[index]


def get_value_by_index(ordered_dict: OrderedDict, index: int) -> Any:
    """有序字段根据索引获取值"""
    if index < 0 or index >= len(ordered_dict):
        return None
    key = list(ordered_dict.keys())[index]
    return ordered_dict[key]


def safe_convert_advanced(value, return_type='auto'):
    """
    增强版安全转换
    Args:
        value: 要转换的值
        return_type: 'auto'|'int'|'float' - 指定返回类型
    """
    if value is None:
        return None

    # 如果已经是目标类型，直接返回
    if return_type == 'int' and isinstance(value, int):
        return value
    elif return_type == 'float' and isinstance(value, float):
        return value
    elif return_type == 'auto' and isinstance(value, (int, float)):
        return value

    # 转换为字符串处理
    str_value = str(value).strip()

    if not str_value:
        return value

    # 处理百分比格式
    if str_value.endswith('%'):
        try:
            num_value = float(str_value.rstrip('%')) / 100.0
            if return_type == 'int':
                return int(round(num_value))
            elif return_type == 'float' or return_type == 'auto':
                return num_value
        except ValueError:
            pass

    # 处理货币格式（如 ¥100.50, $1,000.00）
    currency_pattern = r'^[^\d\-.]*([\-]?\d+(?:,\d{3})*(?:\.\d+)?)[^\d]*$'
    match = re.match(currency_pattern, str_value)
    if match:
        try:
            cleaned = match.group(1).replace(',', '')
            num_value = float(cleaned)

            if return_type == 'int':
                return int(round(num_value))
            elif return_type == 'float':
                return num_value
            elif return_type == 'auto':
                # 如果是整数，返回int，否则返回float
                return int(num_value) if num_value.is_integer() else num_value
        except ValueError:
            pass

    # 常规数字转换
    try:
        # 移除空格和特殊字符（保留数字、小数点、负号）
        cleaned = re.sub(r'[^\d\.\-]', '', str_value)
        if cleaned and cleaned != '-':
            num_value = float(cleaned)

            if return_type == 'int':
                return int(round(num_value))
            elif return_type == 'float':
                return num_value
            elif return_type == 'auto':
                return int(num_value) if num_value.is_integer() else num_value
    except ValueError:
        pass

    # 所有转换都失败，返回原值
    return value


def convert_cn_to_en(data: Dict[str, Any], header_map: OrderedDict[str, str]) -> Dict[str, Any]:
    """把中文键转成英文键"""
    # 1. 构建中文 → 英文映射
    cn_to_en = {cn: en for en, cn in header_map.items()}

    # 2. 转换
    return {cn_to_en.get(k, k): v for k, v in data.items()}
