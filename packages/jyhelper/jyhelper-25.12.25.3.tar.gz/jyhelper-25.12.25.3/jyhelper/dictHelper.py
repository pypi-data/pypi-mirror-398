#! /usr/bin/env python3
# -*- coding:utf-8 -*-
# @Time : 2025/09/26 10:36 
# @Author : JY
"""
默认都不修改原数据
"""

from typing import Callable, Any, Union, List


class dictHelper:
    def __init__(self):
        pass

    @staticmethod
    def sort_by_key(data: dict, sort_func: Callable[[Any], Any] = None, reverse: bool = False) -> dict:
        """
        按key对字典排序\n
        :param data: 待排序字典
        :param sort_func: 排序方法,不传默认按key的值比较 例传: lambda x:int(x) 整数排序
        :param reverse: 是否倒序
        :return: 排序后的字典
        """
        if sort_func is not None:
            return dict(sorted(data.items(), key=lambda x: sort_func(x[0]), reverse=reverse))
        else:
            return dict(sorted(data.items(), key=lambda x: x[0], reverse=reverse))

    @staticmethod
    def sort_by_value(data: dict, sort_func: Callable[[Any], Any] = None, reverse: bool = False) -> dict:
        """
        按value对字典排序\n
        :param data: 待排序字典
        :param sort_func: 排序方法,不传默认按value的值比较 例传: lambda x:int(x) 整数排序
        :param reverse: 是否倒序
        :return: 排序后的字典
        """
        if sort_func is not None:
            return dict(sorted(data.items(), key=lambda x: sort_func(x[1]), reverse=reverse))
        else:
            return dict(sorted(data.items(), key=lambda x: x[1], reverse=reverse))

    @staticmethod
    def del_by_key(data: dict, key: Union[str, List[str]]) -> dict:
        """
        根据条件，删除字典中的数据\n
        :param data: 字典
        :param key: key的值 str/list
        :return: 新字典
        """
        if not isinstance(key, list):
            key = [key]
        new_data = data.copy()
        for row in key:
            new_data.pop(row, None)
        return new_data

    @staticmethod
    def del_by_value(data: dict, value: Union[str, int, bool, List[Any]]) -> dict:
        """
        根据条件，删除字典中的数据\n
        :param data: 字典
        :param value: value的值 str/list
        :return: 新字典
        """
        if not isinstance(value, list):
            value = [value]
        # 使用字典推导式创建新字典，排除要删除的数据
        return {k: v for k, v in data.items() if v not in value}

    class myDict(dict):
        """
            支持嵌套赋值的字典类：\n
            1. 可通过普通字典初始化（自动递归转换为 dictHelper.myDict）\n
            2. 支持 dictHelper.myDict()['a']['b'] = 1 这类嵌套赋值,不用提前设定默认值\n
            3. 取值不要data['a']['b']这样,这样如果取一个不存在的key会自动创建,应该 data.get('a').get('b')
            """

        def __init__(self, initial_data=None):
            # 调用父类 dict 的构造函数，先初始化空字典
            super().__init__()

            # 处理初始化参数：若传入字典，递归转换为 dictHelper.myDict
            if initial_data is not None:
                # 校验参数类型（仅支持字典或 None）
                if not isinstance(initial_data, dict):
                    raise TypeError("initial_data must be a dict or None")

                # 递归遍历初始字典，转换每一层子字典
                self._from_dict(initial_data)

        def _from_dict(self, data):
            """辅助方法：将普通字典递归转换为 dictHelper.myDict"""
            for key, value in data.items():
                # 若值是字典，递归创建 dictHelper.myDict；否则直接赋值
                if isinstance(value, dict):
                    nested_value = dictHelper.myDict(value)  # 子字典转换为 dictHelper.myDict
                    self[key] = nested_value
                else:
                    self[key] = value  # 非字典值（如 int/str）直接保留

        def __getitem__(self, key):
            """重写 [] 取值：不存在的键自动创建 dictHelper.myDict"""
            if key not in self:
                self[key] = dictHelper.myDict()  # 自动创建嵌套实例
            return super().__getitem__(key)

        def get(self, key: str, default=None):
            """重写 get 方法：保持与 __getitem__ 逻辑一致"""
            if key not in self:
                return default if default is not None else dictHelper.myDict()
            return super().get(key, default)

        def to_dict(self) -> dict:
            """辅助方法：将 dictHelper.myDict 递归转换回普通 dict（便于序列化/打印）"""
            result = {}
            for key, value in self.items():
                # 若值是 dictHelper.myDict，递归转换为普通 dict；否则直接保留
                if isinstance(value, dictHelper.myDict):
                    result[key] = value.to_dict()
                else:
                    result[key] = value
            return result


if __name__ == '__main__':
    dataa = {'b1': 1, 'c1': 1, 'a12': 12, 'a9': 9, 'a88': 88, '98': None}
    print('原始数据', dataa)
    res = dictHelper.del_by_value(dataa, [1, 12, None])
    print('原始数据', dataa)
    print('------------------')
    print('修后数据', res)
    print('-------------')
    conf = {'a': {'d': 'd'}}
    dataa = dictHelper.myDict(conf)
    dataa['a']['b']['c'] = 100
    dataa['a']['b']['d'] = 20
    print(dataa.get('a').get('sd', []))
