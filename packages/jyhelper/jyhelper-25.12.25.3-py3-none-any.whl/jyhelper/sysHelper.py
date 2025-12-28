#! /usr/bin/env python3
# -*- coding:utf-8 -*-
# @Time : 2025/01/13 18:35 
# @Author : JY
"""
系统相关的操作
"""
import concurrent.futures
import datetime
import json
import locale
import subprocess
import sys
import time
from typing import Union, Callable, List, Any


class _RunCmdResult:
    """run_cmd的返回值"""

    def __init__(self, code: int, cmd: str, stdout=None, stderr=None):
        self.code = code
        self.success = True if code == 0 else False
        self.cmd = cmd
        self.stdout = stdout if stdout is not None else ''
        self.stderr = stderr if stderr is not None else ''

    def __str__(self):
        return json.dumps(
            {'code': self.code, 'success': self.success, 'cmd': self.cmd, 'stdout': self.stdout, 'stderr': self.stderr},
            ensure_ascii=False, indent=2)

    # 转换为可序列化的字典
    def to_dict(self):
        return {'code': self.code, 'success': self.success, 'cmd': self.cmd, 'stdout': self.stdout,
                'stderr': self.stderr}


class _RunTaskResult:
    """run_tasks的返回值"""

    def __init__(self, success: bool, results: list, exceptions: list):
        for i, row in enumerate(results):
            if isinstance(row, _RunCmdResult):
                results[i] = row.to_dict()
        for i, row in enumerate(exceptions):
            if isinstance(row, _RunCmdResult):
                exceptions[i] = row.to_dict()
        self.success = success
        self.results = results
        self.exceptions = exceptions

    def __str__(self):
        return json.dumps(
            {'success': self.success, 'results': self.results, 'exceptions': self.exceptions},
            ensure_ascii=False, indent=2)

    def to_dict(self):
        return {'success': self.success, 'results': self.results, 'exceptions': self.exceptions}


class sysHelper:

    @staticmethod
    def run_command(command, printInfo=True, returnStr=False, returnJson=False, encoding_utf8=False, encoding_gbk=False,
                    timeout=None, get_error=False):
        """
        执行命令,实时输出结果,阻塞执行完成后返回结果\n
        不再更新,替换为 sysHelper.run_cmd\n
        :param command: 执行的命令
        :param printInfo: 是否打印info信息
        :param returnStr: 返回字符串 默认返回list
        :param returnJson: 返回json解析后的python可直接操作对象
        :param encoding_utf8:
        :param encoding_gbk:
        :param timeout: 超时时间 默认None不超时，可以设定一个秒数
        :param get_error: 报错的时候,是否返回错误信息替代结果
        :return: 默认list 可选字符串和json解析后的对象
        """
        res_lines = []
        encoding = locale.getpreferredencoding(False)
        if encoding_utf8:
            encoding = 'utf-8'
        if encoding_gbk:
            encoding = 'gbk'
        if printInfo:
            print(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), '--->', 'info', 'run:', command)
        start_time = time.time()
        # 3.7以下的版本 text=True 报错，修改为universal_newlines=True
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True,
                                   universal_newlines=True,
                                   encoding=encoding)  # stderr=subprocess.PIPE,可以捕获错误，不设置就是直接输出
        printRes = False
        while True:
            if timeout is not None and time.time() - start_time > timeout:
                process.kill()
                print(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), '--->', sysHelper.red('Error'),
                      sysHelper.red(f"Max allow {timeout} seconds, Time out!"))
                return None

            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                outStr = output.strip()
                res_lines.append(outStr)
                if printInfo:
                    if not printRes:
                        print(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), '--->', 'info', 'res:')
                        printRes = True
                    print(outStr)
                sys.stdout.flush()

        if returnStr:
            res_lines = '\n'.join(res_lines)
        if returnJson:
            res_lines = ''.join(res_lines)
            res_lines = json.loads(res_lines)
        exit_code = process.poll()
        if exit_code != 0:
            print(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), '--->', sysHelper.red('Error: '))
            error_lines = []
            for line in process.stderr:
                error_lines.append(line.strip())
                print(sysHelper.red(line.strip()))
            if isinstance(res_lines, list):
                for row in res_lines:
                    print(sysHelper.red(row))
            else:
                print(sysHelper.red(str(res_lines)))
            if get_error:
                if returnStr:
                    error_lines = '\n'.join(error_lines)
                if returnJson:
                    error_lines = ''.join(error_lines)
                    error_lines = json.loads(error_lines)
                return error_lines
            else:
                return None
        return res_lines

    @staticmethod
    def run_cmd(cmd: str, print_info: bool = True, stdout_json: bool = False, stdout_list: bool = False,
                stderr_json: bool = False, stderr_list: bool = False,
                encoding_utf8: bool = False, encoding_gbk: bool = False,
                timeout: int = None, word_dir: str = None, low_python_version: bool = False,
                ssh_cmd_print_ip: bool = True) -> _RunCmdResult:
        """
        执行命令,实时输出结果,阻塞执行完成后返回结果\n
        windows可以通过这样用执行powershell的命令 cmd = ["powershell.exe", "-Command", 'Get-Process | Select-Object -First 5 Name, Id, CPU | ConvertTo-Json']\n
        可以通过管道符向脚本输入 cmd = '(echo 1 & echo 2) | python.exe demo.py' 先后输入1和2\n
        :param cmd: 执行的命令
        :param print_info: 是否打印info信息
        :param stdout_json: 返回stdout json解析后的python可直接操作对象 默认是str
        :param stdout_list: 返回stdout list 默认是str
        :param stderr_json: 返回stderr json解析后的python可直接操作对象 默认是str
        :param stderr_list: 返回stderr list 默认是str
        :param encoding_utf8: 显示指定utf-8编码
        :param encoding_gbk: 显示指定gbk编码
        :param timeout: 超时时间 默认None不超时，可以设定一个秒数
        :param word_dir: 设置子进程的当前工作目录（命令执行时的起始目录），默认使用父进程的工作目录
        :param low_python_version: 3.7以下的版本 text=True 报错，修改为universal_newlines=True
        :param ssh_cmd_print_ip: 执行ssh x.x.x.x "xxx"命令的时候,在print的信息中添加目标机器IP
        :return: 默认str 可选字符串和json解析后的对象
        """
        # res = subprocess.run('ping a',capture_output=True,text=True)
        res_lines = []
        err_lines = []
        if print_info:
            print(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), '--->', 'run:', cmd)
        start_time = time.time()
        args = {'stdout': subprocess.PIPE, 'stderr': subprocess.PIPE, 'shell': True}
        if low_python_version:
            args['universal_newlines'] = True
        else:
            args['text'] = True
        if encoding_utf8:
            args['encoding'] = 'utf-8'
        if encoding_gbk:
            args['encoding'] = 'gbk'
        if word_dir is not None:
            args['cwd'] = word_dir
        ip_info = ''
        if ssh_cmd_print_ip and cmd.lstrip().startswith('ssh '):
            empty_space = ' '
            target_ip = sysHelper.get_ssh_cmd_ip(cmd)
            ip_info = "\033[36m[%s]:%s\033[0m" % (target_ip, empty_space * (16 - len(target_ip)))
        process = subprocess.Popen(cmd, **args)  # stderr=subprocess.PIPE,可以捕获错误，不设置就是直接输出
        hasPrintRes = False
        while True:
            if timeout is not None and time.time() - start_time > timeout:
                process.kill()
                if print_info:
                    print(ip_info + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), '--->', 'error:',
                          f"Max allow {timeout} seconds, Time out!")
                err_lines.append('timeout after %ss' % timeout)
                break

            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                outStr = output.rstrip()
                res_lines.append(outStr)
                if print_info:
                    if not hasPrintRes:
                        print(ip_info + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), '--->', 'res:')
                        hasPrintRes = True
                    print(ip_info + outStr)
                sys.stdout.flush()

        for line in process.stderr:
            line = line.rstrip()
            if print_info:
                if not hasPrintRes:
                    print(ip_info + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), '--->', 'res:')
                    hasPrintRes = True
                print(ip_info + line)
            err_lines.append(line)

        if stdout_list:
            # 返回list
            stdout = res_lines
        elif stdout_json:
            # 返回json
            res_lines = ''.join(res_lines)
            stdout = json.loads(res_lines)
        else:
            # 默认返回字符串
            stdout = '\n'.join(res_lines)

        if stderr_list:
            # 返回list
            stderr = err_lines
        elif stderr_json:
            # 返回json
            err_lines = ''.join(err_lines)
            stderr = json.loads(err_lines)
        else:
            # 默认返回字符串
            stderr = '\n'.join(err_lines)
        if print_info:
            print(ip_info + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), '--->', 'end')
        return _RunCmdResult(code=process.wait(), cmd=cmd, stdout=stdout, stderr=stderr)

    @staticmethod
    def red(msg: str) -> str:
        """print以后会显示亮红色字体"""
        return f"\033[91m{msg}\033[0m"

    @staticmethod
    def green(msg: str) -> str:
        """print以后会显示亮绿色字体"""
        return f"\033[92m{msg}\033[0m"

    @staticmethod
    def display_all_colors():
        """
        显示全部可用的颜色
        :return:
        """
        j = 0
        for i in range(108):
            if i in [2, 3, 5, 6, 8, 38, 39, 48, 49, 50, 98] or 10 <= i <= 20 or 22 <= i <= 29 or 52 <= i <= 89:
                continue
            msg = f"\033[{i}m" + r"\033[%sm内容\033[0m" % i + "\033[0m"
            if i < 10:
                msg += " "
            if i < 100:
                msg += " "
            print(msg, '', '', end='')
            j += 1
            if j % 8 == 0:
                print()

    @staticmethod
    def logError(msg1: str = '', msg2: str = '', msg3: str = '') -> None:
        """1个参数默认就是红色，2个或者3个参数msg2是红色"""
        if msg2 == '' and msg3 == '':
            print(sysHelper.red(msg1))
        elif msg2 != '' and msg3 == '':
            print(msg1, sysHelper.red(msg2))
        elif msg2 != '' and msg3 != '':
            print(msg1, sysHelper.red(msg2), msg3)

    @staticmethod
    def logInfo(msg1: str = '', msg2: str = '', msg3: str = '') -> None:
        if msg2 == '' and msg3 == '':
            print(sysHelper.green(msg1))
        elif msg2 != '' and msg3 == '':
            print(msg1, sysHelper.green(msg2))
        elif msg2 != '' and msg3 != '':
            print(msg1, sysHelper.green(msg2), msg3)

    @staticmethod
    def input(prompt: str, not_empty: bool = False, number_only: Union[bool, List] = None, default_value: Any = None,
              choice: list = None) -> str:
        """
        输入控制\n
        :param prompt: 显示给用户的提示
        :param not_empty: 不能为空
        :param number_only:
            True 表示只能输入数字
            [-10,10] 表示只能输入-10~10(包含前后)之间的数
            [None,1] 表示小于等于1的数
            [20,None] 表示大于等于20的数
        :param default_value: 默认值
        :param choice: 只能从这里面选 可以是list 也可以是str str会默认循环
        :return: 输入.strip()
        """
        while True:
            if default_value is not None:
                default_prompt = "[默认=%s]: " % default_value
                if default_prompt[0:-1] not in prompt:
                    prompt += default_prompt
            user_input = input(prompt).strip()
            if default_value is not None and not user_input:
                return default_value
            if not_empty and not user_input:
                print("输入无效,内容不能为空，请重新输入!")
                continue
            if number_only is not None:
                if user_input.startswith('-'):
                    number_check = user_input[1:]
                else:
                    number_check = user_input
                if not number_check.isdigit():
                    print("输入无效,只能输入整数，请重新输入!")
                    continue
                if isinstance(number_only, list) and len(number_only) == 2:
                    min_num = number_only[0]
                    max_num = number_only[1]
                    input_num = int(user_input)
                    if (min_num is not None and input_num < min_num) or (max_num is not None and input_num > max_num):
                        print("输入无效,范围[%s ~ %s]，请重新输入!" % (
                            min_num if min_num is not None else 'Min', max_num if max_num is not None else 'Max'))
                        continue
            if choice is not None:
                choice = [str(one_choice) for one_choice in choice]
                if user_input not in choice:
                    print(f"输入无效，请从 {choice} 中选择！")
                    continue
            return user_input

    @staticmethod
    def run_tasks(task_func: Union[Callable, List[Callable]], task_params: List[Union[list, dict]],
                  max_workers: int = 10, print_info: bool = True,
                  thread_mode: bool = True, process_mode: bool = False,
                  raise_exception: bool = False, re_run_exception: int = 0, last_run_info=None) -> _RunTaskResult:
        """
        任务类型	     推荐方案	         核心原因\n
        IO 密集型	 多线程           线程切换开销小，IO 等待时释放 GIL     爬虫（等待网页响应）、API 调用（等待返回结果）、日志写入（磁盘 IO 等待）\n
        CPU 密集型	 多进程	         突破 GIL 限制，利用多核并行计算       大规模数据排序、矩阵运算、视频帧处理\n
        :param task_func: 方法对象或者[方法对象,方法对象,方法对象]
        :param task_params: 参数数组 例: [['a','b'],['a','c'],['b','d'],{'a':1,'b':2}]  或者 如果只有一个参数的话['a','b','c']
                            !!注意!! 参数列表中某行只有一个参数且是None([None]),那么参数是[None]的那部分任务不会执行
        :param max_workers: 线程/进程 数量
        :param print_info: 打印执行信息
        :param thread_mode: 线程模式(默认)
        :param process_mode: 进程模式
        :param raise_exception: 执行遇到异常是否抛出
        :param re_run_exception: 遇到异常任务的重跑次数,重跑完成后,再根据raise_exception的值决定是否抛出异常
                                !!注意!! 任务的成功失败,重跑与否,是看是否有异常抛出,而不是看任务的返回值
        :param last_run_info: 上次执行的结果,重跑异常的时候需要这个参数,主调用不需要传
        :return: success, results, exceptions
        """

        def empty_task(p):
            pass

        if process_mode:
            thread_mode = False
        process_or_thread_pool = None  # 线程或进程池
        if thread_mode:
            process_or_thread_pool = concurrent.futures.ThreadPoolExecutor(max_workers=max_workers)
        if process_mode:
            process_or_thread_pool = concurrent.futures.ProcessPoolExecutor(max_workers=max_workers)
        # 对参数格式化
        task_params = [one if (isinstance(one, list) or isinstance(one,dict)) else [one] for one in task_params]
        # 如果task_func是数组,判断和task_params的个数是否一致
        if isinstance(task_func, list):
            if len(task_func) != len(task_params):
                raise Exception('task_func和task_params列表个数不一致')
        if print_info:
            print(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), '--->', "任务开始", "任务数量", task_params.__len__())
        with process_or_thread_pool as executor:
            futures = []
            for i, one_param in enumerate(task_params):
                #  executor.submit(funcName, p1, p2,..)
                # 重跑到时候,为了使参数的index和原参数的index对齐,成功的参数用None代替,所以这里,当遇到None参数的时候,执行个空方法
                one_param_list = one_param if isinstance(one_param,list) else []
                one_param_dict = one_param if isinstance(one_param,dict) else {}
                future = executor.submit(empty_task if len(one_param_list) == 1 and one_param_list[0] is None else (
                    task_func if not isinstance(task_func, list) else task_func[i]),
                                         *one_param_list, **one_param_dict)
                futures.append(future)

            # 监控线程池中剩余的任务数量
            all_futures = futures.__len__()
            while True:
                time.sleep(1)
                unfinished_count = sum(not future.done() for future in futures)
                if print_info:
                    print(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), '--->',
                          f"完成进度: {all_futures - unfinished_count}/{all_futures}")
                if unfinished_count == 0:
                    break
            results = []
            exceptions = []
            index = 0
            for future in futures:
                if future.exception() is None:
                    results.append(future.result())
                    exceptions.append(None)
                else:
                    results.append(None)
                    exceptions.append(
                        datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S') + " param_index:%s %s -> %s -> %s" % (
                            index, (task_func.__name__ if not isinstance(task_func, list) else task_func[
                                index].__name__) + '(' + str(task_params[index])[1:-1] + ')',
                            type(future.exception()).__name__, str(future.exception())))
                index += 1
            success = True if sum(0 if one is None else 1 for one in exceptions) == 0 else False

            # 合并上次和本次执行的结果
            if last_run_info is not None:
                success = success or last_run_info[0]
                results = [last_run_info[1][i] if last_run_info[1][i] is not None else results[i] for i in
                           range(len(results))]
                # exceptions默认就是最新的exceptions

            if raise_exception and not success and re_run_exception == 0:
                exception_str = "\n"
                for one in exceptions:
                    if one is not None:
                        exception_str += f"{one}\n"
                raise Exception(exception_str)
            if print_info:
                all_num = task_params.__len__()
                except_num = sum(0 if one is None else 1 for one in exceptions)
                success_num = all_num - except_num
                print(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), '--->', '执行完成', f"总数: {all_num}",
                      sysHelper.green(f"成功: {success_num}"),
                      sysHelper.red(f"失败: {except_num}") if except_num > 0 else sysHelper.green(f"失败: {except_num}"))
                if except_num > 0:
                    for one in exceptions:
                        if one is None:
                            continue
                        print(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), '--->', '失败详情', one)
            if re_run_exception > 0 and not success:
                print(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), '--->', '开始重跑失败的任务',
                      f"当前执行完剩余{re_run_exception - 1}次")
                # 构建新的参数列表
                new_task_params = []
                index = 0
                for row in exceptions:
                    if row is None:
                        new_task_params.append(None)
                    else:
                        new_task_params.append(task_params[index])
                    index += 1
                """
                # 测试代码
                if re_run_exception == 4:
                    new_task_params = [
                        None,
                        [1, 1],
                        [1, 0],
                        None,
                    ]
                if re_run_exception <= 3:
                    new_task_params = [
                        None,
                        None,
                        [1, 1],
                        None,
                    ]
                """

                return sysHelper.run_tasks(task_func=task_func, task_params=new_task_params,
                                           max_workers=max_workers,
                                           print_info=print_info, thread_mode=thread_mode,
                                           process_mode=process_mode,
                                           raise_exception=raise_exception,
                                           re_run_exception=re_run_exception - 1,
                                           last_run_info=(success, results, exceptions))
            return _RunTaskResult(success=success, results=results, exceptions=exceptions)

    @staticmethod
    def get_ssh_cmd_ip(cmd: str) -> str:
        """得到ssh远程命令中的IP部分"""
        ip = cmd.lstrip().replace('ssh', '').lstrip()
        if ip.startswith('-p '):
            ip = ip.replace('-p ', '').split(' ')[1].strip()
        ip = ip.split(' ')[0].strip()
        if '@' in ip:
            ip = ip.split('@')[1]
        return ip

    @staticmethod
    def show_run_info(func: Callable) -> Callable:
        """
        显示函数的执行信息,源函数执行完毕后打印\n
        装饰器: 定义方法的时候加上 sysHelper.show_run_info\n
        函数使用: func2 = sysHelper.show_run_info(func)  调用 func2(*args, **kwargs)\n
        :param func:
        :return:
        """
        def wrapper(*args, **kwargs):
            func_name = func.__name__
            start = time.time()
            strat_date = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            result = func(*args, **kwargs)  # 执行原函数
            end = time.time()
            print(f"\n==== 执行函数 {func_name} 执行报告 ====")
            print('开始时间:', strat_date)
            print('结束时间:', datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            print('执行耗时:', f"{round(end - start, 2)} 秒")
            print('列表参数:', args)
            print('字典参数:', kwargs)
            print('返回结果:', result)
            return result

        return wrapper  # 返回包装后的函数


if __name__ == '__main__':
    # sysHelper.input('1111111\n1111111111: ', number_only=True)
    # exit()

    pass
    # cmd = 'ping baidu.com'
    # cmd = 'explorer D:\code\odps_python\\NeiWangServer\link'
    # cmd = ["powershell.exe", "-Command", 'Get-Process | Select-Object -First 5 Name, Id, CPU | ConvertTo-Json']
    # cmd = '(echo 1 & echo 2) |  D:\programs\python.exe D:/code/useDemo.py'
    # res = sysHelper.run_cmd(cmd)
    # print('--------返回的结果---------')
    # print(res)
    # res = sysHelper.input('清输入：',not_empty=False,number_only=False,choice='12345')
    # res = sysHelper.input('清输入',not_empty=False,number_only=False,choice='yn',default_value='y')
    # print(res)

    # """
    params = [
        [1, 10],
        [1, 0],
        [1, 10],
        [1, 10],
        {'b':10,'a':100},
        'a'
    ]
    def my_func(a,b):
        return a / b
    # params = [1,2,3,4,{'a':1}]
    # res = sysHelper.run_tasks(task_func=lambda a, b: print(a / b), task_params=params)
    res = sysHelper.run_tasks(task_func=my_func, task_params=params)
    print('====================================================================')
    print(res)
    # """

    # @staticmethod
    # async def _async_run_cmd_call():
    #     for i in range(100):
    #         print(i)
    #     print('_async_run_cmd_call')
    #
    #
    # @staticmethod
    # def async_run_cmd():
    #     asyncio.run(sysHelper._async_run_cmd_call())

    # print('---------------------------1---------------------------')
    # res = sysHelper.run_tasks(task_func=sysHelper.run_cmd, task_params=[['ping www.baidu.com'], ['ping www.qq.com']])
    # print(res.results[0]['success'])
    # print('---------------------------2---------------------------')
