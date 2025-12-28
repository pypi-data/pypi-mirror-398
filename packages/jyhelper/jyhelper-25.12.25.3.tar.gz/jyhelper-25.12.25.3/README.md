# 一些常用的类、方法

#### 介绍
一些常用的类、方法，不定时更新

#### 软件架构
```commandline
 db/mysql 数据库操作
 timeHelper 时间相关
 fileHelper 文件操作
 common 一些常用的方法
 feishuRobot 飞书机器人发送消息
 sysHelper 系统相关
 strHelper 字符串相关
 listHelper 列表相关
 dictHelper 字典相关
```


#### 安装教程

```commandline
安装
pip install jyhelper
python3 -m pip install jyhelper
更新
pip install jyhelper -U
pip install  --upgrade jyhelper -i https://pypi.org/simple
python3 -m pip install jyhelper --upgrade -i https://pypi.org/simple
```

#### 使用说明

```python3
from jyhelper import db
from jyhelper import timeHelper
from jyhelper import common
from jyhelper import fileHelper
from jyhelper import feishuRobot

dbIns = db(host='',user='root',password='',port=3306,db='')
for row in dbIns.table('table').select():
    print(row)

print(common.explodeList([1,2,3],2))

print(timeHelper.getDate())

fileHelper.read(file_path='')
```