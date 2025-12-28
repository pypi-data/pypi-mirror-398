#! /usr/bin/env python3
# -*- coding:utf-8 -*-
# @Time : 2023/11/14 14:03
# @Author : JY
"""
文件操作相关
有些文件中文会报错，可以尝试encoding=‘gbk’
"""

import os
import shutil
import hashlib
import inspect
import datetime
import zipfile
import base64
import mimetypes
import requests

from typing import Generator, Callable, Any, List, Union


class fileHelper:
    ENCODING_UTF8 = 'utf-8'
    ENCODING_GBK = 'gbk'

    def __init__(self):
        pass

    @staticmethod
    def read(file_path: str, encoding: str = ENCODING_UTF8) -> str:
        """一次性读取txt文件的全部内容"""
        with open(file_path, 'r', encoding=encoding) as f:
            content = f.read()
        return content

    @staticmethod
    def read_by_line(file_path: str, encoding: str = ENCODING_UTF8) -> Generator[str, None, None]:
        """按行读取txt的内容,返回一个生成器对象，如果想要数组结果，可以使用list把结果转一下：list(file.readTxtFileByLine('x.txt'))"""
        with open(file_path, 'r', encoding=encoding) as f:
            # 按行读取内容
            line = f.readline()
            while line:
                # 去除换行符并处理每行内容
                line = line.rstrip()
                # 打印每行内容或进行其他操作
                yield line
                line = f.readline()

    @staticmethod
    def write_append(file_path: str, content: str, encoding: str = ENCODING_UTF8, newline: str = "\n") -> None:
        """以追加的形式写文件 文件不存在会自动创建"""
        with open(file_path, 'a', encoding=encoding, newline=newline) as f:
            f.write(content)

    @staticmethod
    def write_new(file_path: str, content: str, encoding: str = ENCODING_UTF8, newline: str = "\n") -> None:
        """清空文件后写入 文件不存在会自动创建"""
        with open(file_path, 'w', encoding=encoding, newline=newline) as f:
            f.write(content)

    @staticmethod
    def count_lines(file_path: str, encoding: str = ENCODING_UTF8) -> int:
        """得到文件的行数"""
        with open(file_path, 'r', encoding=encoding) as f:
            line_count = sum(1 for line in f)
        return line_count

    @staticmethod
    def rename(old_file: str, new_file: str, cover: bool = True) -> bool:
        """
            重命名文件
            shutil.move(old_file, new_file) # 会覆盖已有的文件
            os.rename(old_file,new_file) # 不会覆盖，并且会报异常
        """
        try:
            if cover:
                shutil.move(old_file, new_file)
            else:
                os.rename(old_file, new_file)
            return True
        except Exception as e:
            print(str(e))
            return False

    @staticmethod
    def del_file(file_name: str) -> bool:
        """"删除文件或者文件夹"""
        try:
            if os.path.isdir(file_name):
                shutil.rmtree(file_name)
                return True
            elif os.path.isfile(file_name):
                os.remove(file_name)
                return True
            else:
                return False
        except Exception as e:
            print(str(e))
            return False

    @staticmethod
    def isdir(file_name: str) -> bool:
        """是否是目录"""
        return os.path.isdir(file_name)

    @staticmethod
    def isfile(file_name: str) -> bool:
        """是否是文件"""
        return os.path.isfile(file_name)

    @staticmethod
    def mkdir(directory: str) -> bool:
        """递归创建多层目录（父目录不存在则自动创建，类似 mkdir -p）"""
        try:
            # 创建目录
            os.makedirs(directory)
            return True
        except FileExistsError:
            return True
        except OSError as e:
            print(f"mkdir '{directory}' error：{e}")
            return False

    @staticmethod
    def get_file_md5(file_path: str, algorithm: str = 'md5') -> str:
        """计算单个文件的 MD5/sha256/sha512 值"""
        if algorithm == 'md5':
            hash_obj = hashlib.md5()
        elif algorithm == 'sha256':
            hash_obj = hashlib.sha256()
        elif algorithm == 'sha512':
            hash_obj = hashlib.sha512()
        else:
            raise Exception('algorithm error')
        with open(file_path, 'rb') as f:
            # 逐块读取文件内容进行加密计算
            for chunk in iter(lambda: f.read(4096), b""):
                hash_obj.update(chunk)
        return hash_obj.hexdigest()

    @staticmethod
    def get_folder_md5(folder_path: str, algorithm: str = 'md5') -> str:
        """计算文件夹的 MD5/sha256/sha512 值"""
        if algorithm == 'md5':
            hash_obj = hashlib.md5()
        elif algorithm == 'sha256':
            hash_obj = hashlib.sha256()
        elif algorithm == 'sha512':
            hash_obj = hashlib.sha512()
        else:
            raise Exception('algorithm error')

        # 递归遍历文件夹中的所有文件
        for root, dirs, files in os.walk(folder_path):
            dirs.sort()
            files.sort()
            for file_name in files:  # 按文件名排序，确保一致性
                file_path = os.path.join(root, file_name)
                # 计算文件的 MD5 值并更新到文件夹 MD5 值中
                file_hash = fileHelper.get_file_md5(file_path, algorithm=algorithm)
                hash_obj.update(file_hash.encode(fileHelper.ENCODING_UTF8))  # 合并文件 MD5
        return hash_obj.hexdigest()

    @staticmethod
    def list_folder_files(folder_path: str, sort_file: bool = True, only_list_this_dir: bool = False,
                          return_file: bool = None, return_dir: bool = None,
                          return_file_and_dir: bool = None, follow_links: bool = False,
                          on_error: Callable[[Any], Any] = None,
                          ignore_dirs: List[str] = None) -> Generator[str, None, None]:
        """
        列出文件夹中的内容\n
        默认递归列出文件夹和子文件夹中的全部文件\n
        :param folder_path: 文件夹路径
        :param sort_file: 是否排序文件, 排序文件可以使每次调用的结果一致 默认排序
        :param only_list_this_dir: 是否只遍历当前目录不遍历子目录
        :param return_file: 返回文件 默认
        :param return_dir: 返回目录
        :param return_file_and_dir: 返回文件和目录
        :param follow_links: 是否会跟随符号链接（symlink）遍历指向的目录；默认不跟随，避免循环遍历
        :param on_error: 函数类型，用于处理遍历过程中出现的错误（如权限不足），默认 None（直接抛出异常）
        :param ignore_dirs: 忽略目录 如 ['.svn','.git']
        :return: 生成器（generator）
        """
        if not os.path.exists(path=folder_path):
            raise Exception('Folder Path Not Exists')
        if return_file is None and return_dir is None and return_file_and_dir is None:
            return_file = True
        if sum([bool(return_file), bool(return_dir), bool(return_file_and_dir)]) != 1:
            raise Exception('return_file, return_dir, return_file_and_dir 只能设置其中一个参数为True')
        if return_file_and_dir:
            return_file = True
            return_dir = True
        for root, dirs, files in os.walk(folder_path, onerror=on_error, followlinks=follow_links):
            if ignore_dirs is not None:
                dirs[:] = [d for d in dirs if d not in ignore_dirs]
            if sort_file:
                dirs.sort()
                files.sort()
            if return_dir:
                for dir_name in dirs:
                    yield os.path.join(root, dir_name)
            if return_file:
                for file_name in files:  # 按文件名排序，确保一致性
                    yield os.path.join(root, file_name)
            if only_list_this_dir:
                break

    @staticmethod
    def get_current_path(include_file_name: bool = False, dir_level: int = 0) -> Union[str, None]:
        """
        :param include_file_name:是否返回包含文件名的路径
        :param dir_level:路径定位 0表示当前文件夹 1表示上一层 2表示上上层
        :return: file_path|dir_path
        """
        try:
            # 获取调用栈：栈帧列表，每个帧包含调用信息
            # stack()[0]：当前方法（getFilePath）的帧
            # stack()[1]：调用当前方法的帧（即调用者的位置）
            caller_frame = inspect.stack()[1]
            # 从调用帧中提取文件名
            caller_file = caller_frame.filename
            # 包含文件名的绝对路径
            caller_abs_file = os.path.abspath(caller_file)
            if include_file_name:
                return caller_abs_file
            else:
                # 提取目录路径（去掉文件名）
                caller_dir = os.path.dirname(caller_abs_file)
                caller_dir = caller_dir.split(os.sep)
                dir_level = abs(dir_level)
                caller_dir = caller_dir[0:caller_dir.__len__() - dir_level]
                # 预处理：修复Windows盘符（添加缺失的分隔符）
                if os.name == 'nt':  # 仅在Windows系统下处理
                    if len(caller_dir) > 0 and caller_dir[0].endswith(':'):
                        caller_dir[0] += os.sep  # 给盘符添加系统分隔符（\）
                else:
                    # linux下 ['','data','a'] 会解析为 data/a而非/data/a 处理这种情况
                    if len(caller_dir) > 0 and caller_dir[0] == '':
                        caller_dir[0] = os.sep
                return os.path.join(*caller_dir)
        except IndexError:
            # 处理调用栈不足的异常（极少发生）
            return None

    @staticmethod
    def get_size(file_path: str, size_name: str = 'B', precision: int = 2) -> float:
        """得到文件/目录的大小"""
        total_size = 0
        allow_size_name = ("B", "KB", "MB", "GB", "TB")
        size_name = size_name.upper()
        if size_name not in allow_size_name:
            raise Exception('getFileSize.size_name need in %s' % str(allow_size_name))
        if not os.path.exists(file_path):
            raise Exception(f"File or path not exists: {file_path}")
        """获取单个文件的大小（字节）"""
        if os.path.isfile(file_path):
            total_size = os.path.getsize(file_path)
        """递归计算目录的总大小（字节）"""
        if os.path.isdir(file_path):
            for root, dirs, files in os.walk(file_path):
                for one_file in files:
                    sub_file_path = os.path.join(root, one_file)
                    try:
                        total_size += os.path.getsize(sub_file_path)
                    except PermissionError:
                        print(f"No Permission: {sub_file_path}，passed")
                    except FileNotFoundError:
                        print(f"File Not Found: {sub_file_path}，passed")
                    except Exception as e:  # 捕获其他所有未处理的异常
                        print(f"Unexpected error with {sub_file_path}：{type(e).__name__} - {str(e)}，passed")
        if size_name == 'B':
            pass
        elif size_name == 'KB':
            total_size = round(total_size / 1024, precision)
        elif size_name == 'MB':
            total_size = round(total_size / 1024 / 1024, precision)
        elif size_name == 'GB':
            total_size = round(total_size / 1024 / 1024 / 1024, precision)
        elif size_name == 'TB':
            total_size = round(total_size / 1024 / 1024 / 1024 / 1024, precision)
        return total_size

    @staticmethod
    def get_modify_time(file_path: str, get_timestamp: bool = False) -> Union[int, str]:
        """
        获取文件/文件夹的最后修改时间
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")
        stat_info = os.stat(file_path)
        return int(stat_info.st_mtime) if get_timestamp else datetime.datetime.fromtimestamp(
            stat_info.st_mtime).strftime('%Y-%m-%d %H:%M:%S')

    @staticmethod
    def get_parent_dir(dir_name: str) -> str:
        """
        得到上层目录\n
        :param dir_name:
        :return: 上层目录的绝对路径
        """
        if not os.path.isdir(dir_name):
            raise Exception('参数[dir_name]不是一个有效的目录')
        dir_name = os.path.abspath(dir_name)
        # dir_name = os.path.normpath(dir_name)  # 默认abspath操作就已经包含了normpath
        return os.path.normpath(dir_name.rstrip(dir_name.split(os.path.sep)[-1]))

    @staticmethod
    def pack(src: str, to=None, compressLevel: int = None) -> str:
        """
        打包文件夹或者文件\n
        :param src: 要打包的「源目录」,会递归打包该目录下所有文件 / 子目录  注意:得到的压缩包不包含目录本身,双击点开就是目录下的内容
        :param to: 打包后的文件名,默认不设置 = 目录同名.zip 且和目录位于同级目录  可以只设置文件名,也可以目录和文件名同时设置
        :param compressLevel: 单个文件的时候的压缩率 compressLevel=0（最快）~9（最优），默认 6
        :return: 打包后的文件绝对路径, 打包目录:可以放在不存在的目录中,会自动创建 打包单个文件: 必须放在已存在的文件夹中,不然会报错
        """
        if os.path.isdir(src):
            src = os.path.abspath(src)  # 统一转换为绝对路径
            if to is None:
                to = src + '.zip'  # 标准化路径（处理末尾分隔符、多分隔符）
            if to.endswith('.zip'):
                houzui = '.zip'
                file_type = 'zip'
            elif to.endswith('.tar'):
                houzui = '.tar'
                file_type = 'tar'
            elif to.endswith('.tar.gz'):
                houzui = '.tar.gz'
                file_type = 'gztar'
            elif to.endswith('.tar.bz2'):
                houzui = '.tar.bz2'
                file_type = 'bztar'
            elif to.endswith('.tar.xz'):
                houzui = '.tar.xz'
                file_type = 'xztar'
            else:
                raise Exception('后缀错误')
            out_file = to[:0 - len(houzui)]
            if not ('/' in out_file or '\\' in out_file):
                # 未设置目录(仅设置文件名),默认设置目录为打包的上层目录
                out_file = os.path.join(fileHelper.get_parent_dir(src), out_file)
            shutil.make_archive(base_name=out_file, format=file_type, root_dir=src)
            return os.path.abspath(out_file + houzui)
        elif os.path.isfile(src):
            src = os.path.abspath(src)  # 统一转换为绝对路径
            if to is None:
                to = src + '.zip'  # 标准化路径（处理末尾分隔符、多分隔符）
            else:
                if not to.endswith('.zip'):
                    raise Exception('单文件打包仅支持压缩为ZIP格式')
            if not ('/' in to or '\\' in to):
                # 未设置目录(仅设置文件名),默认设置目录为文件目录
                to = os.path.join(os.path.dirname(src), to)
            to = os.path.abspath(to)
            with zipfile.ZipFile(to, "w", compression=zipfile.ZIP_DEFLATED,
                                 compresslevel=6 if compressLevel is None else compressLevel) as zf:
                zf.write(src, arcname=os.path.basename(src))
            return to
        else:
            raise Exception('参数[src]不是一个合法的目录或文件')

    @staticmethod
    def unpack(filename: str, unpack_dir: str = None, file_type: str = None) -> str:
        """
        自动识别压缩包格式（或指定格式），解压到目标目录，支持跨平台、自动创建解压目录、过滤解压文件等。\n
        :param filename: 压缩包路径（必选，绝对/相对路径均可）
        :param unpack_dir: 解压目录（可选，默认当前目录；不存在则自动创建）
        :param file_type: 解压格式（可选，None=自动识别；识别失败时手动指定，如 'zip'）
        :return: 解压后的目录绝对路径
        """
        if not os.path.isfile(filename):
            raise Exception('参数[filename]不是有效的文件')
        shutil.unpack_archive(filename, extract_dir=unpack_dir, format=file_type)
        return os.path.abspath(unpack_dir) if unpack_dir is not None else os.path.abspath('.')

    @staticmethod
    def to_base64data(file_path: str, mime_type: str = None) -> str:
        """
        把文件转换为base64格式的Data URI格式数据\n
        :param file_path: 资源文件的绝对/相对路径/网络资源的完整URL（如 'https://example.com/image.png'）
        :param mime_type: 可选，手动指定 MIME 类型（如 'image/png'），默认自动识别
        :return: 完整的 Data URI 字符串
        """
        if file_path.startswith('http:') or file_path.startswith('https:') or file_path.startswith('//'):  # 网络内容
            # 发送 GET 请求获取资源（stream=True 支持大文件流式读取）
            response = requests.get(file_path, stream=True)
            # 检查请求是否成功（状态码 200）
            response.raise_for_status()
            # 1. 优先从响应头获取 MIME 类型
            if not mime_type:
                mime_type = response.headers.get('Content-Type')
                # 2. 若响应头无 MIME 类型，从 URL 扩展名推断
                if not mime_type:
                    mime_type, _ = mimetypes.guess_type(file_path)
                    # 3. 若仍无法推断，默认使用二进制流类型
                    if not mime_type:
                        mime_type = 'application/octet-stream'
            # 读取响应的二进制数据（大文件建议分块读取，此处简化处理）
            file_data = response.content
        else:
            # 检查文件是否存在
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"文件不存在：{file_path}")
            # 自动识别 MIME 类型（如果未手动指定）
            if not mime_type:
                # mimetypes.guess_type 返回 (mime_type, encoding)，取第一个值
                mime_type, _ = mimetypes.guess_type(file_path)
                # 若无法识别，默认使用二进制流类型
                if not mime_type:
                    mime_type = 'application/octet-stream'
            # 读取文件二进制数据
            with open(file_path, 'rb') as f:
                file_data = f.read()
        # Base64 编码（返回 bytes，需解码为字符串）
        base64_data = base64.b64encode(file_data).decode('utf-8')
        # 拼接 Data URI
        return f"data:{mime_type};base64,{base64_data}"

    @staticmethod
    def replace_content(file_path: str, old: str, new: str) -> None:
        fileHelper.write_new(file_path=file_path, content=fileHelper.read(file_path).replace(old, new))


if __name__ == '__main__':
    # print(fileHelper.pack(src=r'D:\downloads\新建文件夹 (4)\a\BoxGacha.sql', to=r'BoxGacha.sql.zip'))
    # print(fileHelper.unpack(filename=r'D:\downloads\新建文件夹 (4)\a\b.zip',unpack_dir=r'D:\downloads\新建文件夹 (4)\\a\\'))
    # print(fileHelper.unpack(filename=r'D:\downloads\新建文件夹 (4)\a\BoxGacha.sql.zip'))
    # print(fileHelper.pack(src=r'./', to='sz.zip'))
    pass
    # fileHelper.write_append('a.log',content="sdfsdf\nsdfsd好的f\na\n")
    # for row in fileHelper.list_folder_files('D:\code\myPythonPackages',only_list_this_dir=False,return_file_and_dir=True,ignore_dirs=['.svn','.idea']):
    #     print(row)
    #     pass

    # print(fileHelper.get_folder_md5('D:\code\\test'))
