#! /usr/bin/env python3
# -*- coding:utf-8 -*-
# @Time : 2025/12/02 14:00 
# @Author : JY
"""
一些偶尔会用到的命令
"""


class docHelper:
    """一些偶尔会用到的命令"""

    disk_init = "mkfs.ext4 /dev/xvdc && mkdir -p /data2 && mount /dev/xvdc /data2"
    """
    挂载新卷\n
    重启会失效,需要vim /etc/fstab 在末尾添加 /dev/xvdc /data2  ext4 defaults 0 0才能重启也生效
    """

    disk_umount = "umount /data2 && rm -rf /data2"
    """
    卸载卷\n
    注意执行的时候 不要在/data2目录里面执行,不然会报data2被占用的错误\n
    删除/etc/fstab删的记录(如有)
    """

    zip = "zip -rq test.zip test/"
    """
    打包文件夹为zip文件\n
    包含目录本身
    """

    unzip = "unzip -oq test.zip -d my_dir/"
    """
    可以不设置-d参数默认解压到当前目录
    """

    def __init__(self):
        pass


if __name__ == '__main__':
    docHelper()
