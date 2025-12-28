#! /usr/bin/env python3
# -*- coding:utf-8 -*-
# @Time : 2020/12/16 16:07
# @Author : JY

import datetime
import time

"""
以下函数默认服务器时区为东八区（北京时间）
"""


class timeHelper:
    # 获取时间
    @staticmethod
    def getDate(timestamp: int = 0, format_str: str = '%Y-%m-%d %H:%M:%S') -> str:
        if timestamp == 0:
            return datetime.datetime.now().strftime(format_str)  # 现在
        else:
            return datetime.datetime.fromtimestamp(timestamp).strftime(format_str)

    # 获取日期
    @staticmethod
    def getDay(timestamp: int = 0, format_str: str = '%Y-%m-%d') -> str:
        if timestamp == 0:
            return datetime.datetime.now().strftime(format_str)  # 现在
        else:
            return datetime.datetime.fromtimestamp(timestamp).strftime(format_str)

    # 把时间戳转为UTC的日期
    @staticmethod
    def getDayUTC(timestamp: int, format_str: str = '%Y-%m-%d') -> str:
        return datetime.datetime.fromtimestamp(timestamp - 8 * 3600).strftime(format_str)

    # 返回今天的日期
    @staticmethod
    def today(xcjt: int = 0) -> str:
        return datetime.datetime.fromtimestamp(int(time.time()) + 86400 * xcjt).strftime('%Y-%m-%d')

    @staticmethod
    def yesterday() -> str:
        """返回昨天的日期"""
        return timeHelper.addDay(None, -1)

    # 获取时间戳
    @staticmethod
    def getTime(date: str = '', format_str: str = None) -> int:
        if date == '':
            return int(time.time())
        else:
            if format_str is None:
                if date.__len__() == 10:
                    format_str = '%Y-%m-%d'
                else:
                    format_str = '%Y-%m-%d %H:%M:%S'
            tm = time.strptime(date, format_str)
            return int(time.mktime(tm))

    @staticmethod
    def xcjt(small: str, big: str) -> int:
        big = big[:10] if big.__len__() != 10 else big
        small = small[:10] if small.__len__() != 10 else small
        format_str = '%Y-%m-%d'
        return int((int(time.mktime(time.strptime(big, format_str))) - int(
            time.mktime(time.strptime(small, format_str)))) / 86400 + 1)

    @staticmethod  # 用时间戳计算相差几天 自然天
    def xcjtStamp(small: int, big: int, timeZone: int = 8) -> int:
        pianYi = (8 - timeZone) * 3600
        xcjt = (timeHelper.getTime(timeHelper.getDay(big - pianYi)) - timeHelper.getTime(
            timeHelper.getDay(small - pianYi))) / 86400 + 1
        return int(xcjt)

    @staticmethod
    def getMonthFirstDay(day: str = None) -> str:
        day = day if day is not None else timeHelper.getDay()
        return day[:8] + '01'

    @staticmethod
    def getMonthEndDay(day: str = None) -> str:
        day = day if day is not None else timeHelper.getDay()
        year, month, tmp = day.split('-')
        if month == '12':
            nextMonth = 1
            year = str(int(year) + 1)
        else:
            nextMonth = int(month) + 1
        nextMonth = str(nextMonth) if nextMonth >= 10 else '0' + str(nextMonth)
        nextMonth = year + '-' + nextMonth + '-01'
        return timeHelper.getDay(timeHelper.getTime(nextMonth) - 86400)

    @staticmethod
    def getWeekFirstDay(day: str = None) -> str:
        weekday = datetime.datetime.strptime(day, "%Y-%m-%d").weekday()
        firstDay = timeHelper.getDay(timeHelper.getTime(day) - 86400 * weekday)
        return firstDay

    @staticmethod
    def getWeekEndDay(day: str = None) -> str:
        return timeHelper.getDay(timeHelper.getTime(timeHelper.getWeekFirstDay(day)) + 86400 * 6)

    # 星期几
    @staticmethod
    def getWeekJi(day: str = None) -> int:
        return datetime.datetime.strptime(day, "%Y-%m-%d").weekday() + 1

    @staticmethod
    def addDay(event_day: str = None, add_day: int = 1) -> str:
        if event_day is None:
            event_day = timeHelper.getDay()
        return timeHelper.getDay(timeHelper.getTime(event_day) + 86400 * add_day)

    # 转换时区
    @staticmethod
    def transDate(date: str, from_tz: int, to_tz: int) -> str:
        if not isinstance(from_tz, int) or not isinstance(to_tz, int):
            raise RuntimeError('from_tz 或者 to_tz 错误')
        stamp = timeHelper.getTime(date)
        stamp = stamp + (to_tz - from_tz) * 3600
        if date.__len__() == 10:
            return timeHelper.getDay(stamp)
        else:
            return timeHelper.getDate(stamp)

    @staticmethod
    def checkIsDay(day: str) -> bool:
        if day.__len__() != 10:
            return False
        try:
            time.strptime(day, "%Y-%m-%d")
            return True
        except ValueError:
            return False

    @staticmethod
    def checkIsDate(date: str) -> bool:
        if date.__len__() != 19:
            return False
        try:
            time.strptime(date, '%Y-%m-%d %H:%M:%S')
            return True
        except ValueError:
            return False

    @staticmethod
    def sleep(seconds: int) -> None:
        time.sleep(seconds)

    # 得到一个日期列表(默认包含首尾)
    @staticmethod
    def getDayList(startDate: str, endDate: str, stepLen: int = 86400, includeTail: bool = True) -> list:
        if timeHelper.checkIsDay(startDate) and timeHelper.checkIsDay(endDate):
            formatStr = '%Y-%m-%d'
        elif timeHelper.checkIsDate(startDate) and timeHelper.checkIsDate(endDate):
            formatStr = '%Y-%m-%d %H:%M:%S'
        else:
            raise Exception('startDate或者endDate日期格式不对')
        timeStart = timeHelper.getTime(startDate)
        timeEnd = timeHelper.getTime(endDate)
        res = []
        for i in range(timeStart, timeEnd + int(includeTail), stepLen):
            res.append(timeHelper.getDay(i, formatStr))
        return res

    @staticmethod
    def get_hour(date: str = None, year: bool = False, month: bool = False, day: bool = False, minute: bool = False,
                 second: bool = False) -> int:
        """返回日期字符串中的小时部分 转换为整数返回"""
        if date is None:
            date = timeHelper.getDate()
        i1 = 11
        i2 = 13
        if year:
            i1 = 0
            i2 = 4
        if month:
            i1 = 5
            i2 = 7
        if day:
            i1 = 8
            i2 = 10
        if minute:
            i1 = 14
            i2 = 16
        if second:
            i1 = 17
            i2 = 19
        return int(date[i1:i2])


if __name__ == '__main__':
    # day = '2023-11-12'
    # print(timeHelper.getWeekFirstDay(day=day), timeHelper.getWeekEndDay(day=day))
    # timeHelper.sleep(10)
    # print(timeHelper.getWeekJi(day))

    # for row in timeHelper.getDayList('2024-01-01 00:00:00','2024-01-02 00:00:00',includeTail=False,stepLen=3600):
    #     print(row)

    print(timeHelper.get_hour('2024-11-22 13:25:35', year=True))
    print(timeHelper.get_hour('2024-11-22 13:25:35', month=True))
    print(timeHelper.get_hour('2024-11-22 13:25:35', day=True))
    print(timeHelper.get_hour('2024-11-22 13:25:35'))
    print(timeHelper.get_hour('2024-11-22 13:25:35', minute=True))
    print(timeHelper.get_hour('2024-11-22 13:25:35', second=True))
