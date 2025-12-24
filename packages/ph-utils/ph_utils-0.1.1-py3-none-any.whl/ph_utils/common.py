# Copyright (c) [2023] [Tenny]
# [ph-utils] is licensed under Mulan PSL v2.
# You can use this software according to the terms and conditions of the Mulan PSL v2.
# You may obtain a copy of Mulan PSL v2 at:
#         http://license.coscl.org.cn/MulanPSL2
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY OR FIT FOR A PARTICULAR PURPOSE.
# See the Mulan PSL v2 for more details.
# !/usr/bin/env python3
import json
import math
from datetime import date, datetime
from decimal import Decimal
from random import choice, randint, randrange


def is_empty(data=None):
    """判断字符串是否为空字符串

    Args:
        data (str): 待验证的字符串

    Returns:
        bool: 是否为空, 例如: ""、None
    """
    return False if data else True


def is_blank(data=None):
    """判断字符串是否为空, 忽略前后空格

    Args:
        data (str, optional): 待验证的字符串. Defaults to None.

    Returns:
        bool: 是否为空, 例如: ""、None、"   "
    """
    if data:
        data = data.strip()
    return is_empty(data)


def random(
    len=16, min=None, max=None, include_end=True, only_num=False, first_zero=True
):
    """生成随机数

    Args:
        len (int, optional): 生成的随机数长度. Defaults to 16.
        min (int, optional): 生成指定区间随机数时的区间最小值. Defaults to None.
        max (int, optional): 生成指定区间随机数时的区间最大值. Defaults to None.
        include_end (bool, optional): 生成指定区间随机数时是否包含 max. Defaults to True.
        only_num (bool, optional): 生成指定长度随机数时, 是否指定生成的随机数只包含数字. Defaults to False.
        first_zero (bool, optional): 生成的随机数, 首字符是否允许包含 0. Defaults to False.

    Returns:
        int|str: 生成的随机数
    """
    if min and max:  # 生成介于 min~max 之间的随机数
        return randint(min, max) if include_end else randrange(min, max)
    else:
        random_base = "9876543210QWERTYUIOPLKJHGFDSAZXCVBNMqwertyuioplkjhgfdsazxcvbnm"
        if only_num:  # 生成纯数字的随机数
            random_base = random_base[0:10]
        random_res = "".join(choice(random_base) for _ in range(len))
        if not first_zero:  # 生成的随机数首字符是否允许为 0
            while random_res.startswith("0"):
                random_res = "".join(choice(random_base) for _ in range(len))
        return random_res


class JsonEncoder2(json.JSONEncoder):
    """JSON 序列化增强版, 支持 datetime、Decimal、date"""

    def default(self, o):
        if isinstance(o, datetime):
            return o.strftime("%Y-%m-%d %H:%M:%S")
        elif isinstance(o, date):
            return o.strftime("%Y-%m-%d")
        elif isinstance(o, Decimal):
            return str(o)
        return super().default(o)


def json_dumps(obj, ensure_ascii=False, format=False, indent=None):
    """将字典对象格式化为 JSON 字符串, 支持对于 datetime、Decimal、date 类型的格式化

    Args:
        obj (dict|list): 待格式化的对象
        ensure_ascii (bool, optional): 是否进行unicode编码, 中文会被特殊编码. Defaults to False.
        format (bool, optional): 是否进行格式化输出, 分隔符之间会有空格拆分. Defaults to False.

    Returns:
        str: json格式的字符串
    """
    separators = (",", ":")
    if format:
        separators = None
        if indent is None:
            indent = 2
    return json.dumps(
        obj,
        cls=JsonEncoder2,
        ensure_ascii=ensure_ascii,
        separators=separators,
        indent=indent,
    )


def mask_phone(phone):
    """手机号屏蔽

    Args:
        phone (str): 手机号

    Returns:
        str: 将手机号中间部分遮盖
    """
    if is_blank(phone):
        return ""
    start = int(len(phone) / 3)
    end = math.ceil((len(phone) % 3) / 2)
    end = start * 2 + end
    mask_tag = "".join(["*" for item in range(end - start)])
    return f"{phone[0:start]} {mask_tag} {phone[end:]}"


def has(data: dict | list | tuple, key):
    """验证字典是否包含某个 key, 有key且值不为None
       或者列表是否包含某个元素

    Args:
        data (dict): 字典或者列表
        key (str): 检查的key或者元素值

    e.g.:
        a = {"a": None}
        has(a, "a") => False
        a = ["a"]
        has(a, "a") => True

    Returns:
        bool: 检查是否有key且值不为None
    """
    if isinstance(data, dict):
        if key in data and data[key] is not None:
            return True
        return False
    elif isinstance(data, list) or isinstance(data, tuple):
        return key in data
    else:
        return False


def has_more(data: dict | list | tuple, keys: list | tuple):
    """检查字典或者列表是否包含多个key或者元素的值

    Args:
        data (dict): 字典或者列表
        keys (list|tuple): 要检查的key的列表或者元素列表

    Returns:
        bool: True - 包含所有的 key
    """
    is_has = True
    for key in keys:
        if not has(data, key):
            is_has = False
            break
    return is_has
