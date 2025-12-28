#! /usr/bin/env python3
# -*- coding:utf-8 -*-
# @Time : 2025/09/25 18:35
# @Author : JY
"""
字符串相关的操作/编码解码/md5/totp
"""
import time
import hmac
import hashlib
import base64
import struct
from urllib.parse import quote, unquote
import re
import json
from typing import Union


class strHelper:

    @staticmethod
    def generate_totp(secret: str, step: int = 0, time_step: int = 30, digits: int = 6, algorithm=hashlib.sha1) -> str:
        """
        生成 TOTP/MFA 动态验证码\n
        :param secret: Base32 编码的共享密钥（如 'JBSWY3DPEHPK3PXP'）
        :param step: 用这个参数得到当前时间步长前后的代码 -1表示前一个步长 0表示当前 1表示后一个步长
        :param time_step: 时间步长（秒），默认 30 秒
        :param digits: 验证码位数，默认 6 位
        :param algorithm: 哈希算法，默认 SHA-1，可选 SHA-256、SHA-512
        :return: 生成的动态验证码（6 位数字字符串）
        """
        # 1. 解码 Base32 密钥（去除空格，处理大小写）
        secret = secret.replace(' ', '').upper()
        key = base64.b32decode(secret)
        # 2. 计算当前时间步长（T =  Unix时间戳 // 步长）
        t = int((time.time() + step * time_step) // time_step)
        # 3. 将时间步长转换为 8 字节大端序（网络字节序）
        t_bytes = struct.pack('>Q', t)  # '>Q' 表示大端序 64 位整数
        # 4. 计算 HMAC 哈希
        hmac_hash = hmac.new(key, t_bytes, algorithm).digest()
        # 5. 动态截断（Dynamic Truncation）
        offset = hmac_hash[-1] & 0x0F  # 取哈希最后一字节的低 4 位作为偏移量
        truncated = struct.unpack('>I', hmac_hash[offset:offset + 4])[0]
        truncated &= 0x7FFFFFFF  # 清除最高位，确保为正数
        # 6. 生成指定位数的验证码
        totp = str(truncated % (10 ** digits)).zfill(digits)
        return totp

    @staticmethod
    def md5(string: str, algorithm: str = 'md5') -> str:
        """对字符串进行md5/sha256/sha512编码"""
        string = string if isinstance(string, str) else str(string)
        if algorithm == 'md5':
            hash_obj = hashlib.md5()
        elif algorithm == 'sha256':
            hash_obj = hashlib.sha256()
        elif algorithm == 'sha512':
            hash_obj = hashlib.sha512()
        else:
            raise Exception('algorithm error')
        hash_obj.update(string.encode('utf-8'))
        return hash_obj.hexdigest()

    @staticmethod
    def url_encode(string: str) -> str:
        string = string if isinstance(string, str) else str(string)
        return quote(string, 'utf-8')

    @staticmethod
    def url_decode(string: str) -> str:
        string = string if isinstance(string, str) else str(string)
        return unquote(string, 'utf-8')

    @staticmethod
    def base64_encode(string: str) -> str:
        string = str(string) if not isinstance(string, str) else string
        return base64.b64encode(string.encode('utf-8')).decode('utf-8')

    @staticmethod
    def base64_decode(string: str) -> str:
        """Base64编码在最后可能需要添加填充字符 '=' 以使编码后的字符串长度是 4 的倍数。如果输入的字符串没有正确的填充，就会导致解码错误。"""
        string = str(string)
        stringLen = string.__len__()
        yuShu = stringLen % 4
        addString = ''
        if yuShu > 0:
            addString = (4 - yuShu) * '='
        return base64.b64decode(string + addString).decode('utf-8')

    @staticmethod
    def re_split(string: str, pattern: str = None) -> list:
        """正则表达式分割字符串 默认用空格分割，多个空格会合并成一个处理"""
        pattern = r'\s+' if pattern is None else pattern
        return re.split(pattern, string)

    @staticmethod
    def json_encode(obj: Union[list, dict]) -> str:
        """转成json字符串"""
        return json.dumps(obj, ensure_ascii=False)

    @staticmethod
    def json_decode(string: str) -> Union[list, str]:
        """json字符串转为对象"""
        return json.loads(string)

    @staticmethod
    def reverse(string: str) -> str:
        """字符串倒序"""
        return string[::-1]

    @staticmethod
    def sort(string: str, sort_func=None, reverse=False) -> str:
        if sort_func is not None:
            return ''.join(sorted(string, key=sort_func, reverse=reverse))
        else:
            return ''.join(sorted(string, reverse=reverse))

    @staticmethod
    def is_int(string: str) -> bool:
        """判断字符串是否为整数格式"""
        if not isinstance(string, str):
            string = str(string)
        # 正则表达式：^开头 $结尾，[+-]?可选正负号，\d+至少1位数字
        integer_pattern = re.compile(r'^[+-]?\d+$')
        return bool(integer_pattern.match(string))

    @staticmethod
    def is_float(string: str) -> bool:
        """判断字符串是否为规范小数格式（含小数点，前后各至少1位数字）"""
        if not isinstance(string, str):
            string = str(string)
        # 正则表达式：^开头 $结尾，[+-]?可选正负号，\d+至少1位数字，\.小数点
        decimal_pattern = re.compile(r'^[+-]?\d+\.\d+$')
        return bool(decimal_pattern.match(string))

    @staticmethod
    def is_number(string: str) -> bool:
        """判断是否是整数或小数类型的字符串"""
        return strHelper.is_int(string) or strHelper.is_float(string)

    @staticmethod
    def trans_to_number(string: str, default=None) -> Union[int, float]:
        """把字符串转换为数字"""
        if strHelper.is_int(string):
            return int(string)
        if strHelper.is_float(string):
            return float(string)
        return default


if __name__ == '__main__':
    a_string = '2'
    # print(strHelper.is_float(a_string))
    # print(strHelper.is_int(a_string))
    # print(strHelper.is_number('12.3'))
    # print(strHelper.trans_to_number('12.3f0'))

    # print(strHelper.md5(a_string,algorithm='sha256'))
    # print(strHelper.md5(a_string,algorithm='sha512'))
    # print(strHelper.md5(a_string))
    # print(strHelper.sort(a_string))

    # test = {'a0': 1, 'a1': '好的'}
    # res = strHelper.json_encode(test)
    # res = strHelper.json_decode(res)
    # print(type(res), res)
