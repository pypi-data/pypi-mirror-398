# -*- coding: utf-8 -*-
"""
---------------------------------------------
Created on 2025/5/25 20:56
@author: ZhangYundi
@email: yundi.xxii@outlook.com
---------------------------------------------
"""

from datetime import datetime
from typing import Optional
import os

import pandas as pd

DATE_FORMAT = "%Y-%m-%d"
TIME_FORMAT = "%H:%M:%S"
USERHOME = os.path.expanduser('~')  # 用户家目录

FILE = os.path.join(USERHOME, ".xcals")
FILE_URL = "https://raw.githubusercontent.com/link-yundi/xcals/refs/heads/main/.xcals"

def today():
    return datetime.today().strftime(DATE_FORMAT)

def now():
    return datetime.now().strftime(TIME_FORMAT)

def update():
    try:
        print(f"reading data from {FILE_URL}")
        pd.read_csv(FILE_URL, header=None, dtype=str).to_csv(FILE, index=False, header=False)
        print(f"save {FILE} done.")
    except Exception as e:
        print(f"更新交易日数据失败: {e}")

def get_tradingdays(beg_date: Optional[str] = None, end_date: Optional[str] = None) -> list:
    """
    获取交易日历
    :param beg_date: 开始日期
    :param end_date: 结束日期
    :return: 交易日历
    """
    s = pd.read_csv(FILE, header=None, dtype=str)[0]
    if beg_date is not None:
        s = s[s >= beg_date]
    if end_date is not None:
        s = s[s <= end_date]
    return s.to_list()


def get_recent_tradeday(date: Optional[str] = None) -> str:
    """
    获取最新的交易日

    Parameters
    ----------
    date: str
        指定的日期, 默认today

    Returns
    -------
    str
        最近一个交易日的日期
    """
    date = date if date is not None else datetime.today().strftime(DATE_FORMAT)
    tradedays = get_tradingdays(end_date=date)
    return tradedays[-1]


def shift_tradeday(date: str, num: int = 1) -> str:
    """
    获取指定日期的n天前或后的交易日
    如果指定日期不是交易日，则由该日期前的最新交易日开始shift
    Parameters
    ----------
    date: str
        指定的日期
    num: int
        前多少天或后多少天, 默认1天

    Returns
    -------
    str
        指定交易日的num天前或后的交易日
    """
    if num < 0:
        return get_tradingdays(end_date=date)[num - 1]
    recent_date = get_recent_tradeday(date)
    return get_tradingdays(beg_date=recent_date)[num]


def is_tradeday(date) -> bool:
    """
    是否是交易日

    Parameters
    ----------
    date: str
        日期，格式为 'YYYY-MM-DD'

    Returns
    -------
    bool
        如果给定日期是交易日，则返回 `True`；否则返回 `False`。
    """
    return date == shift_tradeday(date, num=0)


def is_reportdate(date: str) -> bool:
    """
    判断给定的日期是否为报告期

    Parameters
    ----------
    date: str
        日期

    Returns
    -------
    bool
    """
    date = pd.to_datetime(date)
    month = date.month
    day = date.day
    if month in [6, 9]:
        if day == 30:
            return True
    if month in [3, 12]:
        if day == 31:
            return True

    return False


def get_recent_reportdate(date: str) -> str:
    """获取给定日期之前（包括）最新的报告日期"""
    date_ = pd.to_datetime(date)
    year = date_.year
    month = date_.month
    day = date_.day
    report_months = [12, 3, 6, 9]
    day_map = {12: 31, 3: 31, 6: 30, 9: 30}
    if day == day_map.get(month, 0):
        return f"{year}-{month:02d}-{day:02d}"
    # 找到当前月份所属的季度索引（0-3）
    m_index = (month - 1) // 3
    if m_index < 1:
        year -= 1
    new_month = report_months[m_index]
    new_day = day_map[new_month]
    return f"{year}-{new_month:02d}-{new_day:02d}"


def shift_reportdate(report_date: str, num: int) -> str:
    """
    移动 num 个报告期

    Parameters
    ----------
    report_date: str
        当前的报告期, 格式为 'yyyy-mm-dd'
    num: int
        需要移动的报告期数，正数表示向后移动，负数表示向前移动

    Returns
    -------
    str
        移动后的报告日期, 格式为'yyyy-mm-dd'
    """
    assert is_reportdate(report_date), f"非报告日期: {report_date}"

    date_ = pd.to_datetime(report_date)
    year = date_.year
    month = date_.month
    report_months = [3, 6, 9, 12]
    day_map = {12: 31, 3: 31, 6: 30, 9: 30}
    # 找到当前月份所属的季度索引（0-3）
    m_index = (month // 3 - 1 + num % 4) % 4
    y_shift = (month // 3 - 1 + num) // 4
    new_month = report_months[m_index]
    new_day = day_map[new_month]
    return f"{year + y_shift}-{new_month:02d}-{new_day:02d}"


def get_tradingtime(beg_time: Optional[str] = None, end_time: Optional[str] = None, freq: str = "1s") -> list:
    """交易时间段"""
    beg_time_am = "09:30:00"
    end_time_am = "11:30:00"
    beg_time_pm = "13:00:00"
    end_time_pm = "15:00:00"
    time_am = pd.date_range(beg_time_am, end_time_am, freq=freq).strftime(TIME_FORMAT)
    time_pm = pd.date_range(beg_time_pm, end_time_pm, freq=freq).strftime(TIME_FORMAT)
    all_time = time_am.append(time_pm)
    if beg_time is not None:
        all_time = all_time[all_time >= beg_time]
    if end_time is not None:
        all_time = all_time[all_time <= end_time]
    return all_time.tolist()


_tradingtime_index = pd.date_range(start="09:30:00", end="11:30:00", freq="1s").strftime("%H:%M:%S").append(
    pd.date_range(start="13:00:00", end="15:00:00", freq="1s").strftime("%H:%M:%S"))
_tradingtime_secs = _tradingtime_index.size
_tradingtime_series = pd.Series(range(_tradingtime_secs), name="time_index", index=_tradingtime_index)


def shift_tradetime(time: str, delta: str) -> str:
    """
    移动交易时间: 最小单位为秒
    :param time: 当前时间
    :param delta: 时间差，格式为 'HH:MM:SS'
    :return: 移动后的时间
    """
    timeDelta = pd.Timedelta(delta)
    beg_time_am = "09:30:00"
    end_time_am = "11:30:00"
    beg_time_pm = "13:00:00"
    end_time_pm = "15:00:00"
    if time <= beg_time_am:
        time = beg_time_am
    elif end_time_am <= time < beg_time_pm:
        time = end_time_am
    elif time >= end_time_pm:
        time = end_time_pm
    time_index = _tradingtime_series[time]
    secs_shift = timeDelta.seconds
    if timeDelta.days < 0:
        if secs_shift > 0:
            secs_shift -= 86400  # 24*60*60
    new_time_index = time_index + secs_shift
    return _tradingtime_index[new_time_index % _tradingtime_secs]


def shift_tradedt(date: str, time: str, delta: str) -> (str, str):
    """
    移动交易 date, time
    """
    beg_time_am = "09:30:00"
    end_time_am = "11:30:00"
    beg_time_pm = "13:00:00"
    end_time_pm = "15:00:00"

    timeDelta = pd.Timedelta(delta)
    shift_days = timeDelta.days
    secs_shift = timeDelta.seconds
    if (shift_days < 0) & (secs_shift > 0):
        shift_days += 1
        secs_shift -= 86400  # 24*60*60

    if time <= beg_time_am:
        time = beg_time_am
    elif end_time_am <= time < beg_time_pm:
        time = end_time_am
    elif time >= end_time_pm:
        time = end_time_pm
    time_index = _tradingtime_series[time]

    new_time_index = time_index + secs_shift

    date = shift_tradeday(date, shift_days + new_time_index // _tradingtime_secs)
    time = _tradingtime_index[new_time_index % _tradingtime_secs]
    return date, time


def ceil_time(dt, interval: str = "1min")->str:
    """
    向上取整到指定间隔

    Example
    -------
        >>> dt = "09:31:59"
        >>> print(ceil_time(dt, interval='1min'))
        09:32:00
    """
    format_str = "%H:%M:%S"
    if isinstance(dt, str):
        dt = datetime.strptime(dt, format_str)
    # 转换为秒数
    interval_seconds = pd.Timedelta(interval).seconds

    # 计算总秒数
    total_seconds = dt.hour * 3600 + dt.minute * 60 + dt.second

    # 向上取整
    if total_seconds % interval_seconds != 0:
        total_seconds = ((total_seconds // interval_seconds) + 1) * interval_seconds

    # 创建新的时间对象
    new_hour = total_seconds // 3600
    new_minute = (total_seconds % 3600) // 60
    new_second = total_seconds % 60

    return dt.replace(hour=new_hour, minute=new_minute, second=new_second, microsecond=0).strftime(format_str)

def get_time_range(beg_time: Optional[str] = None, end_time: Optional[str] = None, freq: str = "1s") -> list:
    """交易时间段"""
    beg_time_am = "09:30:00"
    end_time_am = "11:30:00"
    beg_time_pm = "13:00:00"
    end_time_pm = "15:00:00"

    if not beg_time:
        beg_time = beg_time_am
    if not end_time:
        end_time = end_time_am

    if end_time_am < beg_time < beg_time_pm and end_time_am < end_time < beg_time_pm:
        return []

    if beg_time < beg_time_am:
        beg_time = beg_time_am
    elif end_time_am < beg_time < beg_time_pm:
        beg_time = beg_time_pm
    if end_time > end_time_pm:
        end_time = end_time_pm
    elif end_time_am < end_time < beg_time_pm:
        end_time = end_time_am

    time_range = pd.date_range(beg_time, end_time, freq=freq).strftime(TIME_FORMAT)
    overlap_noon = beg_time <= end_time_am and end_time >= beg_time_pm
    if not overlap_noon:
        return time_range.tolist()
    time_am = time_range[time_range <= end_time_am]
    # if len(time_am) > 0:
    end_am = time_am[-1]
    beg_pm = shift_tradetime(end_am, freq)
    freq_seconds = pd.Timedelta(freq).seconds
    # if freq_seconds
    interval = freq
    if not freq_seconds % 3600:
        interval = "1h"
    elif not freq_seconds % 60:
        interval = "1min"
    beg_pm = ceil_time(beg_pm, interval)
    time_pm = time_range[time_range >= beg_pm]
    time_range = time_am.append(time_pm)
    return time_range.tolist()