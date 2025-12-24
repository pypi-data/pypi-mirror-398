import asyncio
import copy
import random
from typing import Dict, Any
from . import constants

import hashlib

def get_url_string_md5(url: str) -> str:
    """计算URL字符串本身的MD5值"""
    # 统一使用UTF-8编码（URL通常为ASCII字符，但需处理特殊字符）
    url_bytes = url.encode('utf-8')
    md5_hash = hashlib.md5(url_bytes).hexdigest()
    return md5_hash


def get_file_hash(file_path: str):
    """计算文件的哈希值"""
    hash_md5 = hashlib.md5()
    with open(file_path, 'rb') as f:
        # 读取文件内容，按块更新哈希值
        for chunk in iter(lambda: f.read(4096), constants.EMPTY_BYTE):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def chinese_number_to_arabic(chinese_str):
    # 基本数字映射（包含零）
    chinese_digits = {
        '零': 0, '一': 1, '二': 2, '三': 3, '四': 4, '五': 5,
        '六': 6, '七': 7, '八': 8, '九': 9,
        '十': 10, '百': 100, '千': 1000,
        '万': 10000, '亿': 100000000,
        '点': '.'  # 添加点映射
    }

    # 处理空字符串
    if not chinese_str:
        return 0

    # 处理纯阿拉伯数字（整数或小数）
    if chinese_str.replace('.', '', 1).isdigit() and chinese_str.count('.') <= 1:
        return float(chinese_str) if '.' in chinese_str else int(chinese_str)

    # 内部函数：解析节内数字（0-9999范围）
    def parse_section(s):
        # 尝试直接转换阿拉伯数字
        if s.replace('.', '', 1).isdigit() and s.count('.') <= 1:
            return float(s) if '.' in s else int(s)

        # 处理带"点"的小数
        if '点' in s:
            integer_part = ""
            decimal_part = ""
            point_found = False
            for char in s:
                if char == '点':
                    point_found = True
                elif point_found:
                    decimal_part += char
                else:
                    integer_part += char

            integer_val = parse_section(integer_part) if integer_part else 0
            decimal_val = 0
            factor = 0.1
            for char in decimal_part:
                if char in '0123456789':
                    d = int(char)
                    decimal_val += d * factor
                    factor *= 0.1
                elif char in chinese_digits and chinese_digits[char] < 10:
                    d = chinese_digits[char]
                    decimal_val += d * factor
                    factor *= 0.1
            return integer_val + decimal_val

        # 解析纯中文整数（支持多个单位）
        result = 0
        temp = 0
        last_unit_value = 1  # 跟踪上一个单位的值

        for char in s:
            if char in '0123456789':
                # 阿拉伯数字直接赋值
                temp = int(char)
            elif char in chinese_digits:
                digit = chinese_digits[char]
                if digit < 10:  # 基本数字（0-9）
                    temp = digit
                else:  # 单位（十、百、千）
                    # 处理连续单位（如"零4百零五"）
                    if temp == 0 and result > 0 and digit > last_unit_value:
                        # 大单位前无数值，但前面已有数字（如"三百五"）
                        result += digit
                    else:
                        # 单位前无数值时视为1（如"十"->10）
                        if temp == 0:
                            temp = 1
                        result += temp * digit
                        temp = 0  # 重置临时值
                    last_unit_value = digit

        # 处理最后可能的数字
        return result + temp

    # 按顺序处理大单位：亿、万
    for unit in ['亿', '万']:
        if unit in chinese_str:
            parts = chinese_str.split(unit, 1)  # 只分割一次
            left_part = parts[0] or '零'  # 处理空字符串情况
            right_part = parts[1] if len(parts) > 1 else ''

            # 递归解析左右部分
            left_num = chinese_number_to_arabic(left_part)
            right_num = chinese_number_to_arabic(right_part) if right_part else 0

            # 处理特殊情况：单位后的"零"开头（如"万零五百"）
            # 只有当"零"后面跟着数字时才跳过
            if right_part and right_part.startswith('零') and len(right_part) > 1 and right_part[
                1] in '0123456789一二三四五六七八九':
                right_num = chinese_number_to_arabic(right_part[1:])

            return left_num * chinese_digits[unit] + right_num

    # 处理千、百、十单位（节内解析）
    return parse_section(chinese_str)

def deep_merge(dest: Dict[str, Any], src: Dict[str, Any], overwrite: bool = True) -> Dict[str, Any]:
    """
    安全深度合并两个字典，避免覆盖危险属性

    Args:
        dest: 目标字典
        src: 源字典
        overwrite: 是否覆盖已存在的非字典值

    Returns:
        合并后的字典
    """
    # 防止修改原始字典
    result = copy.deepcopy(dest)

    for key, value in src.items():
        # 跳过特殊属性
        if key.startswith('__'):
            continue

        if key in result:
            # 如果目标值和源值都是字典，递归合并
            if isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = deep_merge(result[key], value, overwrite)
            # 如果源值是 None，跳过（避免意外覆盖）
            elif value is None:
                continue
            # 根据 overwrite 决定是否覆盖非字典值
            elif overwrite:
                result[key] = value
        else:
            # 添加新键值对
            result[key] = value

    return result

def snake_to_camel(snake_str, pascal_case=False):
    """
    将蛇形命名转换为驼峰命名
    :param snake_str: 蛇形命名的字符串
    :param pascal_case: 是否转换为帕斯卡命名（首字母大写），默认为 False（小驼峰）
    :return: 驼峰命名的字符串
    """
    components = snake_str.split('_')
    # 如果是帕斯卡命名，首字母大写；否则首字母小写
    if pascal_case:
        return ''.join(x.title() for x in components)
    else:
        # 小驼峰：第一个单词首字母小写，其余单词首字母大写
        return components[0] + ''.join(x.title() for x in components[1:])