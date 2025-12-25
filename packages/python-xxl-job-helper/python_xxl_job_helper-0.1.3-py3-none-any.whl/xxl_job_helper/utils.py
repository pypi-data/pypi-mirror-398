# -*- coding: utf-8 -*-
"""
# ---------------------------------------------------------------------------------------------------------
# ProjectName:  python-xxl-job-helper
# FileName:     utils.py
# Description:  工具模块
# Author:       ASUS
# CreateDate:   2025/12/22
# Copyright ©2011-2025. Hunan xxxxxxx Company limited. All rights reserved.
# ---------------------------------------------------------------------------------------------------------
"""
from datetime import datetime, timedelta

CRON_FIELDS_LEN = 7


class QuartzCronError(ValueError):
    pass


def datetime_to_quartz_cron(dt: datetime) -> str:
    """
    datetime -> Quartz Cron (秒 分 时 日 月 ? 年)
    """
    return f"{dt.second} {dt.minute} {dt.hour} {dt.day} {dt.month} ? {dt.year}"


def quartz_cron_to_datetime(cron: str) -> datetime:
    """
    Quartz Cron -> datetime
    仅支持固定时间点，不支持 */n、区间等复杂表达式
    """
    parts = cron.strip().split()
    if len(parts) != CRON_FIELDS_LEN:
        raise QuartzCronError(f"Cron 字段数错误，应为 7 位，当前为 {len(parts)}")

    sec, minute, hour, day, month, week, year = parts

    if week != "?":
        raise QuartzCronError("当前仅支持 week 为 '?' 的 cron")

    try:
        return datetime(
            year=int(year),
            month=int(month),
            day=int(day),
            hour=int(hour),
            minute=int(minute),
            second=int(sec),
        )
    except ValueError as e:
        raise QuartzCronError(f"Cron 转 datetime 失败: {e}")


def validate_quartz_cron(cron: str) -> bool:
    """
    校验是否是 XXL-JOB / Quartz 可接受的定时点 cron
    """
    try:
        quartz_cron_to_datetime(cron)
        return True
    except QuartzCronError:
        return False


def cron_next_seconds(cron: str, seconds: int) -> str:
    """
    在 cron 时间点基础上 + N 秒，返回新的 cron
    常用于：
    - 本次任务执行完成
    - N 秒后重新触发
    """
    dt = quartz_cron_to_datetime(cron)
    new_dt = dt + timedelta(seconds=seconds)
    return datetime_to_quartz_cron(new_dt)


def cron_last_seconds(cron: str, seconds: int) -> str:
    """
    在 cron 时间点基础上 - N 秒，返回新的 cron
    常用于：
    - 本次任务执行完成
    - N 秒前触发时间，即为上一次
    """
    dt = quartz_cron_to_datetime(cron)
    new_dt = dt - timedelta(seconds=seconds)
    return datetime_to_quartz_cron(new_dt)


if __name__ == '__main__':
    # datetime → cron（最常用）
    dt = datetime(2025, 12, 22, 16, 12, 12)
    cron = datetime_to_quartz_cron(dt)
    print(cron)
    # 12 12 16 22 12 ? 2025

    # cron → datetime
    cron = "12 12 16 22 12 ? 2025"
    dt = quartz_cron_to_datetime(cron)
    print(dt)
    # 2025-12-22 16:12:12

    # cron 校验（在调用调度 API 前用）
    cron = "32 12 16 22 12 ? 2025"
    if not validate_quartz_cron(cron):
        raise RuntimeError("非法 cron 表达式")

    # 延迟10后运行
    current_cron = "12 12 16 22 12 ? 2025"
    next_cron = cron_next_seconds(current_cron, 10)
    print(next_cron)
    # 22 12 16 22 12 ? 2025

    # 上一次的运行
    current_cron = "12 12 16 22 12 ? 2025"
    next_cron = cron_last_seconds(current_cron, 10)
    print(next_cron)
    # 2 12 16 22 12 ? 2025
