"""
@author: Rossi
@time: 2020-11-29

数字转换相关辅助函数
"""

import re


char2digit = {"一": 1, "二":2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7, "八": 8, "九": 9, "零": 0,
              "壹": 1, "贰":2, "叁": 3, "肆": 4, "伍": 5, "陆": 6, "柒": 7, "捌": 8, "玖": 9, "两": 2,
              "1":1, "2":2, "3":3, "4":4, "5":5, "6":6, "7":7, "8":8, "9":9, "0": 0}


digit = "一二三四五六七八九十0-9壹贰叁肆伍陆柒捌玖零"

# 完整数字的正则
number_pattern = re.compile(f"^([{digit}十拾百佰千仟万萬]+[億亿])?([{digit}十拾百佰千仟]+[万萬])?([{digit}十拾百佰千仟]+)?$")

# 万以下的数字的正则
sub_number_pattern = re.compile(f"^((?P<qian>[{digit}])[千仟])?((?P<bai>[{digit}]+)[百佰])?((?P<shi>[{digit}]*)[十拾])?(?P<ge>[{digit}]+)?$")

WAN = 10000
YI = 100000000
QIAN = 1000


def str2number(num_str):
    """
    转换中文数字字符串为int，不合法数字返回-1
    """
    if num_str is None or number_pattern.match(num_str) is None:
        return -1
    index_yi, index_wan = _find_split_positions(num_str)
    if index_yi == -1 and index_wan == -1:
        return _str2number(num_str)
    elif index_yi == -1:
        left_part, right_part = num_str[:index_wan], num_str[index_wan+1:]
        if right_part.startswith("零"):
            num = _str2number(right_part[1:])
            if num == -1:
                return -1
            return _str2number(left_part) * WAN + num
        else:
            num = _str2number(right_part)
            if num == -1:
                return -1
            elif num < 10:  # 三万二
                return _str2number(num_str[:index_wan]) * WAN + num * QIAN
            else:
                return _str2number(num_str[:index_wan]) * WAN + num
    elif index_wan == -1 or index_yi > index_wan:
        num = _str2number(num_str[index_yi+1:])
        if num == -1:
            return -1
        return str2number(num_str[:index_yi]) * YI + num  # 递归
    else:
        n1 = _str2number(num_str[index_wan+1:])
        n2 = _str2number(num_str[index_yi+1:index_wan])
        if n1 == -1 or n2 == -1:
            return -1
        return str2number(num_str[:index_yi]) * YI + n2 * WAN + n1  # 递归


def _find_split_positions(num_str):
    index_yi = num_str.find("亿")
    if index_yi == -1:
        index_yi = num_str.find("億")
    index_wan = num_str.rfind("万")
    if index_wan == -1:
        index_wan = num_str.rfind("萬")
    return index_yi, index_wan


def _str2number(num_str):
    """
    转换万以下的中文数字字符串为int，不合法数字返回-1
    """
    if num_str == "":
        return 0
    match = sub_number_pattern.match(num_str)
    if not match:
        return -1
    if num_str.isdigit():
        return int(num_str)
    num = 0
    try:
        num += (char2digit[match.group("qian")] if match.group("qian") is not None else 0) * 1000
        num += (char2digit[match.group("bai").replace("零","")] if match.group("bai") is not None else 0) * 100
        tens = match.group("shi")
        if tens is not None:
            tens = tens.replace("零", "")
            if tens == "":
                tens = "一"  # 十 -> 一十
            num += char2digit[tens] * 10
        unit = match.group("ge")
        if unit is not None:
            if unit.startswith("零"):
                num += char2digit[unit[1:]]
            elif match.group("shi") is not None:  # e.g. 三十五
                num += char2digit[unit]
            elif match.group("bai") is not None:  # e.g. 二百五
                num += char2digit[unit] * 10
            elif match.group("qian") is not None: # e.g. 三千三
                num += char2digit[unit] * 100
            else:
                num += char2digit[unit]
        return num
    except:  # 不合法数字
        return -1


def to_digit(s):
    """
    中文数字转换为阿拉伯数字，返回字符串
    """
    if s is None:
        return s
    digit = "".join([str(char2digit[chr]) for chr in s])
    return digit
