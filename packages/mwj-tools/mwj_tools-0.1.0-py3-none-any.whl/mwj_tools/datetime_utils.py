# -*- coding: utf-8 -*-
"""
@Time : 2025/12/25 16:29
@Email : Lvan826199@163.com
@公众号 : 梦无矶测开实录
@File : datetime_utils.py
"""
__author__ = "梦无矶小仔"

"""
日期时间通用处理工具模块
提供时间计算、转换、格式化等常用功能
"""
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta
import time
from typing import Union, Tuple, Optional


class DateTimeUtils:
    """日期时间处理工具类"""

    @staticmethod
    def now(fmt: str = None) -> Union[datetime, str]:
        """
        获取当前时间

        Args:
            fmt: 格式化字符串，如'%Y-%m-%d %H:%M:%S'

        Returns:
            格式化后的时间字符串或datetime对象
        """
        current = datetime.now()
        return current.strftime(fmt) if fmt else current

    @staticmethod
    def add_time(
            base_time: Union[datetime, str] = None,
            days: int = 0,
            hours: int = 0,
            minutes: int = 0,
            months: int = 0
    ) -> datetime:
        """
        时间加减计算

        Args:
            base_time: 基准时间，默认为当前时间
            days: 加减天数
            hours: 加减小时数
            minutes: 加减分钟数
            months: 加减月数

        Returns:
            计算后的datetime对象
        """
        if base_time is None:
            base_time = datetime.now()
        elif isinstance(base_time, str):
            base_time = datetime.fromisoformat(base_time)

        if months:
            # 使用relativedelta处理月份加减（考虑不同月份天数）
            result = base_time + relativedelta(months=months)
            result += timedelta(days=days, hours=hours, minutes=minutes)
        else:
            result = base_time + timedelta(days=days, hours=hours, minutes=minutes)

        return result

    @staticmethod
    def to_timestamp(dt: Union[datetime, str] = None) -> float:
        """
        将datetime转换为时间戳

        Args:
            dt: datetime对象或时间字符串

        Returns:
            时间戳（浮点数，单位秒）
        """
        if dt is None:
            dt = datetime.now()
        elif isinstance(dt, str):
            dt = datetime.fromisoformat(dt)

        return dt.timestamp()

    @staticmethod
    def from_timestamp(timestamp: float) -> datetime:
        """
        将时间戳转换为datetime对象

        Args:
            timestamp: 时间戳

        Returns:
            datetime对象
        """
        return datetime.fromtimestamp(timestamp)

    @staticmethod
    def time_difference(
            time1: Union[datetime, str],
            time2: Union[datetime, str] = None,
            unit: str = 'seconds'
    ) -> float:
        """
        计算两个时间的时间差

        Args:
            time1: 时间1
            time2: 时间2，默认为当前时间
            unit: 返回单位，可选：'seconds', 'minutes', 'hours', 'days'

        Returns:
            时间差数值
        """
        if isinstance(time1, str):
            time1 = datetime.fromisoformat(time1)
        if time2 is None:
            time2 = datetime.now()
        elif isinstance(time2, str):
            time2 = datetime.fromisoformat(time2)

        diff = abs((time2 - time1).total_seconds())

        units = {
            'seconds': 1,
            'minutes': 60,
            'hours': 3600,
            'days': 86400
        }

        return diff / units.get(unit, 1)

    @staticmethod
    def future_date(
            days_after: int,
            from_date: Union[date, str] = None,
            fmt: str = "%Y-%m-%d"
    ) -> str:
        """
        计算多少天之后的日期

        Args:
            days_after: 多少天后
            from_date: 起始日期，默认为今天
            fmt: 返回格式

        Returns:
            格式化后的日期字符串
        """
        if from_date is None:
            from_date = date.today()
        elif isinstance(from_date, str):
            from_date = date.fromisoformat(from_date)

        future = from_date + timedelta(days=days_after)
        return future.strftime(fmt)

    @staticmethod
    def format_time(
            dt: Union[datetime, str],
            fmt: str = "%Y-%m-%d %H:%M:%S"
    ) -> str:
        """
        格式化时间

        Args:
            dt: 时间对象或字符串
            fmt: 格式字符串

        Returns:
            格式化后的时间字符串
        """
        if isinstance(dt, str):
            dt = datetime.fromisoformat(dt)
        return dt.strftime(fmt)

    @staticmethod
    def is_weekend(dt: Union[datetime, str] = None) -> bool:
        """
        判断是否为周末

        Args:
            dt: 时间，默认为当前时间

        Returns:
            True如果是周末，否则False
        """
        if dt is None:
            dt = datetime.now()
        elif isinstance(dt, str):
            dt = datetime.fromisoformat(dt)

        return dt.weekday() >= 5

    @staticmethod
    def get_week_range(
            dt: Union[datetime, str] = None
    ) -> Tuple[date, date]:
        """
        获取给定日期所在周的起止日期

        Args:
            dt: 时间，默认为当前时间

        Returns:
            (周一开始日期, 周日结束日期)
        """
        if dt is None:
            dt = datetime.now()
        elif isinstance(dt, str):
            dt = datetime.fromisoformat(dt)

        # 获取星期几 (0=周一, 6=周日)
        weekday = dt.weekday()

        # 计算周一的日期
        start_date = dt.date() - timedelta(days=weekday)
        # 计算周日的日期
        end_date = start_date + timedelta(days=6)

        return (start_date, end_date)