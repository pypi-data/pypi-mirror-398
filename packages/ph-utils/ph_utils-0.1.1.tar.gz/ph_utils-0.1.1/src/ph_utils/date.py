# Copyright (c) [2023] [Tenny]
# [ph-utils] is licensed under Mulan PSL v2.
# You can use this software according to the terms and conditions of the Mulan PSL v2.
# You may obtain a copy of Mulan PSL v2 at:
#         http://license.coscl.org.cn/MulanPSL2
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY OR FIT FOR A PARTICULAR PURPOSE.
# See the Mulan PSL v2 for more details.
#!/usr/bin/env python3
"""日期时间处理的工具类"""

import re
from datetime import datetime, timedelta
from typing import Union, overload, Optional, TypeAlias, Literal

OriDateType: TypeAlias = datetime | str | int | None
UnitType: TypeAlias = Literal['date'] | None

# 情况1：format 是 str → 返回 str
@overload
def start_of(
    ori_date: OriDateType = ...,
    unit: UnitType = ...,
    format: str = ...,
    is_end: bool = ...,
) -> str: ...

# 情况2：format 是 None → 返回 datetime
@overload
def start_of(
    ori_date: OriDateType = ...,
    unit: UnitType = ...,
    format: None = ...,
    is_end: bool = ...,
) -> datetime: ...

def start_of(
    ori_date: OriDateType=None, unit: UnitType = "date", format: str | None = None, is_end=False
):
    """设置到一个时间的开始

    Args:
        ori_date (datetime | str | int, optional): 能够被 parse() 解析的日期时间. Defaults to None.
        unit (str, optional): 设置到某个单位时间的开始, 支持的单位列表: date - 当天 00:00. Defaults to 'date'.
        format (str, optional): 格式化显示的值，如果为 None 则返回 datetime形式否则返回时间戳, 支持的值: 's' - UNIX时间戳, 'ms' - 精确到毫秒的时间戳. Defaults to None.
        is_end (bool, optional): 是否设置到结束时间. Defaults to False.
    Returns:
        datetime | int: 日期
        
    Examples:
        >>> # 获取今天的开始时间 (datetime 对象)
        >>> start_of()
        datetime.datetime(2023, 10, 27, 0, 0, 0)
        
        >>> # 获取指定日期的结束时间戳 (秒)
        >>> start_of("2023-10-27", unit="date", format="s", is_end=True)
        1698422399
        
        >>> # 获取指定日期的开始时间戳 (毫秒)
        >>> start_of("2023-10-27", format="ms")
        1698336000000
    """
    _start_dict = {"date": {"hour": 0, "minute": 0, "second": 0, "microsecond": 0}}
    _end_dict = {
        "date": {"hour": 23, "minute": 59, "second": 59, "microsecond": 999999}
    }
    uni_data = _end_dict[unit] if is_end is True else _start_dict[unit]
    ori_date = parse(ori_date).replace(**uni_data)
    return timestamp(ori_date, format) if format in ("s", "ms") else ori_date
    

def end_of(ori_date: OriDateType = None, unit: UnitType = "date", format: str | None = None):
    """设置一个时间的结束

    Args:
        dt (datetime, optional): 日期. Defaults to None.
        unit (str, optional): 单位. Defaults to 'date'.
        format (str, optional): 格式化输出, s - 10位时间戳, ms - 13位时间戳. Defaults to None.

    Returns:
        datetime: 日期
    """
    return start_of(ori_date, unit, format, True)


def set(ori_date=None, values=None):
    """设置某个时刻的时间, 例如: set(xx, '00:00:00') 或者 set(xx, { 'hour': 00, 'minute': 00 })

    Args:
        ori_date (datetime, optional): 日期. Defaults to None.
        values (dict, optional): 设置的时间, { hour, minute, second }. Defaults to None.

    Returns:
        datetime: 日期
    """
    ori_date = parse(ori_date)
    if values is not None:
        if isinstance(values, str):
            sreplace = {}
            rmatch = re.search(r"(\d{2}):?(\d{2}):?(\d{2})$", values)
            if rmatch:
                sreplace = {
                    "hour": int(rmatch.group(1)),
                    "minute": int(rmatch.group(2)),
                    "second": int(rmatch.group(3)),
                }
            rmatch = re.search(r"^(\d{4})[-/]?(\d{2})[-/]?(\d{2})", values)
            if rmatch:
                sreplace["year"] = int(rmatch.group(1))
                sreplace["month"] = int(rmatch.group(2))
                sreplace["day"] = int(rmatch.group(3))
            values = sreplace
    if values and isinstance(values, dict):
        ori_date = ori_date.replace(**values)
    return ori_date


def timestamp(ori_date=None, unit="s"):
    """获取时间戳(int)

    Args:
        ctime (float, optional): 指定时间. Defaults to 当前时间.
        unit (str, optional): 精确等级, s - 精确到秒, ms - 精确到毫秒. Defaults to 's'.

    Returns:
        int: 10/13位的时间戳数字
    """
    tm = 0
    if isinstance(ori_date, int):
        tm = ori_date
    else:
        tm = parse(ori_date).timestamp()
    return int(round(tm * 1000) if unit == "ms" else tm)
    
def format(ori_date=None, pattern="%Y-%m-%d"):
    """将当前日期格式化为指定格式的字符串形式

    Args:
        ori_date (any, optional): 能够被 parse 解析的日期
        pattern (str, optional): 待格式化的形式. 默认: '%Y%m%d'. %Y-%m-%d %H:%M:%S

    Returns:
        str: 正确格式化后的日期字符串
    """
    return parse(ori_date).strftime(pattern)


def parse(dt_str=None, fmt=None):
    """解析字符串格式的日期为 datetime 类型

    Args:
        dt_str (str): 日期的字符串形式
        fmt (str, optional): 格式样式. Defaults to '%Y-%m-%d'.

    Returns:
        datetime: datetime
    """
    if not dt_str:
        return datetime.now()
    if isinstance(dt_str, datetime):
        return dt_str
    if isinstance(dt_str, int):
        return datetime.fromtimestamp(dt_str)
    if not fmt:
        return datetime.fromisoformat(dt_str)
    return datetime.strptime(dt_str, fmt)


def _plus_month(ori_date, month):
    """日期增加月份

    Args:
        ori_date (datetime): 日期
        month (int): 增加的月份

    Returns:
        datetime: 增加后的日期
    """
    # 计算年份和月份的增量
    years, months = divmod(abs(month), 12)
    if month > 0:  # 增加
        # 计算新的年份和月份
        new_year = ori_date.year + years
        new_month = ori_date.month + months

        # 处理月份超过12的情况
        if new_month > 12:
            new_year += 1
            new_month -= 12
    else:
        # 计算新的年份和月份
        new_year = ori_date.year - years
        new_month = ori_date.month - months

        # 处理月份小于1的情况
        if new_month < 1:
            new_year -= 1
            new_month += 12

    # 构造新的日期对象
    return ori_date.replace(year=new_year, month=new_month)


def _plus_year(ori_date, year):
    """日期增加年份

    Args:
        ori_date (datetime): 日期
        year (int): 增加的年份

    Returns:
        datetime: 增加后的日期
    """
    new_year = ori_date.year + year
    return ori_date.replace(year=new_year)


def add(ori_date=None, delta=None):
    """将日期进行加法操作, 通常用于计算几天、几月、几年之后的日期

    Args:
        ori_date (datetime | str, optional): 待添加的日期. Defaults to None.
        delta (dict, optional): { days - 天, months - 月, years - 年 }. Defaults to None.

    Returns:
        datetime: 添加后的日期
    """
    if not delta:
        delta = {"days": 0}
    ori_date = parse(ori_date)
    if "years" in delta:  # 年份
        ori_date = _plus_year(ori_date, delta["years"])
        del delta["years"]
    if "months" in delta:  # 月份
        ori_date = _plus_month(ori_date, delta["months"])
        del delta["months"]
    if delta:
        diff = timedelta(**delta)
        ori_date = ori_date + diff
    return ori_date


def subtract(ori_date=None, delta=None):
    """将日期进行加法操作, 通常用于计算几天、几月、几年之前的日期

    Args:
        ori_date (datetime | str, optional): 原始日期. Defaults to None.
        delta (dict, optional): { days - 天, months - 月, years - 年 }. Defaults to None.

    Returns:
        datetime: 添加后的日期
    """
    if not delta:
        delta = {"days": 0}
    for key in delta:
        delta[key] = -delta[key]
    return add(ori_date, delta)


def sub(ori_date=None, delta=None):
    """subtract 函数别名"""
    return subtract(ori_date, delta)


def diff(start=None, end=None, result="days"):
    """计算两个日期之前的间隔

    Args:
        start (any, optional): 开始时间. Defaults to None.
        end (any, optional): 结束时间. Defaults to None.
        result (str, optional): 返回类型, days - 返回两个日期相隔多少天. Defaults to 'days'.

    Returns:
        timedelta | int: 日期间隔
    """
    # 先转成时间戳，再进行计算, 避免出现时区问题
    diff_num = timestamp(end) - timestamp(start)
    delta = timedelta(diff_num / 86400)
    if result == "days":
        return delta.days
    else:
        return delta
