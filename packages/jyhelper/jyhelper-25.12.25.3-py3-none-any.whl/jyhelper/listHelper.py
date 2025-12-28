#! /usr/bin/env python3
# -*- coding:utf-8 -*-
# @Time : 2025/09/26 10:36 
# @Author : JY
"""
默认都不修改原数据
"""

from typing import Union, Any, List, Callable


class listHelper:
    def __init__(self):
        pass

    @staticmethod
    def explode(data: List, n: int) -> List:
        """将列表分割 每一份n的长度"""
        return [data[i:i + n] for i in range(0, len(data), n)]

    @staticmethod
    def del_by_value(data: List, value: Any) -> List:
        """
        根据值从list中删除数据\n
        :param data:
        :param value: 待删除的数据,可以是 str表示单个元素,也可以是list表示多个元素依次删除
        :return:
        """
        if not isinstance(value, list):
            value = [value]
        return [x for x in data if x not in value]

    @staticmethod
    def del_by_index(data: List, index: Union[int, List[int]]) -> List:
        """
        根据索引从list中删除数据\n
        :param data:
        :param index: 索引 int | list[int]
        :return:
        """
        if not isinstance(index, list):
            index = [index]
        return [data[i] for i in range(len(data)) if i not in index]

    @staticmethod
    def sort(data: List, sort_func: Callable[[Any], Any] = None, reverse: bool = False) -> List:
        if sort_func is not None:
            return sorted(data, key=sort_func, reverse=reverse)
        else:
            return sorted(data, reverse=reverse)

    @staticmethod
    def unique(data: List) -> List:
        """去重且保留原列表中元素首次出现的顺序\nlist(set(data))也可以去重,但顺序会变"""
        seen = set()
        return [x for x in data if not (x in seen or seen.add(x))]


if __name__ == '__main__':
    data1 = [1, 2, 3, 4]
    data2 = [1, 5, 4, 9, 11, 91, 84]
    print(listHelper.sort(data2, sort_func=lambda x: str(x)))
