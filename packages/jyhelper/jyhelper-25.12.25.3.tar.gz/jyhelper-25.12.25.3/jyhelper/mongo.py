#! /usr/bin/env python3
# -*- coding:utf-8 -*-
# @Time : 2025/11/14 17:34 
# @Author : JY
"""
操作mongodb数据库
mongodb://localhost:27017/
mongodb://root:123456@localhost:27017/admin?authSource=admin
mongodb://root:<插入您的密码>@docdb-xxxx.us-west-2.docdb.amazonaws.com:27017/?replicaSet=rs0&readPreference=secondaryPreferred&retryWrites=false
"""
from typing import Union

from bson.objectid import ObjectId
from pymongo import MongoClient
import sqlparse
import re
import ast
import time
import datetime


class mongo:
    def __init__(self, connect_str=None, user=None, password=None, host=None, port=27017, maxPoolSize=100,
                 minPoolSize=0, socketTimeoutMS=None, connectTimeoutMS=10000,waitQueueTimeoutMS=10000,maxIdleTimeMS=600000,serverSelectionTimeoutMS=30000):
        """
        :param connect_str: 连接字符串
        :param user:
        :param password:
        :param host:
        :param port:
        :param maxPoolSize: 最大连接数（默认100）
        :param minPoolSize: 最小空闲连接数（默认0）
        :param socketTimeoutMS: Socket读写超时时间 默认None表示不超时
        :param connectTimeoutMS: 连接建立超时时间  默认10秒
        :param waitQueueTimeoutMS: 连接池无空闲连接时，新请求的排队超时时间。默认：无限排队，若连接池满且无空闲连接，请求会一直阻塞。
        :param maxIdleTimeMS: 连接池中空闲连接的最大存活时间。默认：空闲连接永久存活，不会自动关闭（可能导致连接泄露）。
        :param serverSelectionTimeoutMS: 选择 MongoDB 服务器（如副本集节点）的超时时间。默认 30 秒，若无法找到可用节点，会抛出 ServerSelectionTimeoutError。
        """
        if connect_str is not None:
            self._connect_str = connect_str
        else:
            self._connect_str = f"mongodb://{user}:{password}@{host}:{port}/admin?authSource=admin"
        self._db = None
        self._table = None
        self._connection = None
        self._maxPoolSize = maxPoolSize
        self._minPoolSize = minPoolSize
        self._socketTimeoutMS = socketTimeoutMS
        self._connectTimeoutMS = connectTimeoutMS
        self._waitQueueTimeoutMS = waitQueueTimeoutMS
        self._maxIdleTimeMS = maxIdleTimeMS
        self._serverSelectionTimeoutMS = serverSelectionTimeoutMS

    def _get_connection(self):
        if self._connection is None:
            self._connection = MongoClient(self._connect_str,
                                           maxPoolSize=self._maxPoolSize,
                                           minPoolSize=self._minPoolSize,
                                           socketTimeoutMS=self._socketTimeoutMS,
                                           connectTimeoutMS=self._connectTimeoutMS,
                                           waitQueueTimeoutMS=self._waitQueueTimeoutMS,
                                           maxIdleTimeMS=self._maxIdleTimeMS,
                                           serverSelectionTimeoutMS=self._serverSelectionTimeoutMS
                                           )
        return self._connection

    def db(self, db):
        """设置database"""
        self._db = db
        return self

    def table(self, table):
        """设置数据集(table)"""
        self._table = table
        return self

    def _check_table(self, db, table):
        if db is not None:
            self._db = db
        if table is not None:
            self._table = table
        if self._db is None or self._table is None:
            raise Exception('请设置db和table')

    def insert(self, data: Union[list, dict], db=None, table=None, printInfo=False) -> Union[str,list]:
        """
        写入一条或多条数据\n
        :param data: 待写入的数据dict或者list {'name': '李02', 'age': 22, 'address': {"city": 'aaaa', "city2": 'aaaa'}}
        :param db: db
        :param table: 数据集(table)
        :param printInfo: 显示打印信息
        :return: _id | [_id,_id,...]
        """
        self._check_table(db, table)
        if printInfo:
            start = time.time()
            print(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), '开始写入', self._db, self._table)
        if isinstance(data, list):
            result = self._get_connection()[self._db][self._table].insert_many(data)
            result = [str(_id) for _id in result.inserted_ids]
        elif isinstance(data, dict):
            result = self._get_connection()[self._db][self._table].insert_one(data)
            result = str(result.inserted_id)
        else:
            raise Exception('data只能是dict或者list')
        if printInfo:
            print(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), '结束写入', self._db, self._table,
                  '耗时: %s秒' % round((time.time() - start), 2),
                  '影响: %s条' % len(result) if isinstance(result, list) else 1)
        return result

    def select_one(self, where: Union[dict, str], field: str = None, except_field: str = None, group: list = None,
                   sort: str = None, skip: int = None, limit: int = None, db=None, table=None, printInfo=False) -> dict:
        """
        查询一条记录\n
        :param where: where条件 可以是pymongo的原生dict也可以是简单的mysql条件
        :param field: 要显示的字段
        :param except_field: 要排除的字段
        :param group: 分组聚合 ['address.city,name','count(*) as user_count,avg(age) as avg_age,sum(age),max(age),min(age) min_age']
        :param sort: 排序
        :param skip: 跳过多少条
        :param limit: 最多返回多少条
        :param db: db
        :param table: 数据集(table)
        :param printInfo: 显示打印信息
        :return: dict
        """
        return self._select(where=where, field=field, except_field=except_field, group=group, sort=sort, skip=skip,
                            limit=limit,
                            db=db, table=table,
                            printInfo=printInfo, select_one=True)

    def select(self, where: Union[dict, str], field: str = None, except_field: str = None, group: list = None,
               sort: str = None, skip: int = None, limit: int = None, db=None, table=None, printInfo=False) -> list:
        """
        查询数据\n
        :param where: where条件 可以是pymongo的原生dict也可以是简单的mysql条件
        :param field: 要显示的字段 name,age,city.address
        :param except_field: 要排除的字段 name,age,_id
        :param group: 分组聚合 ['address.city,name','count(*) as user_count,avg(age) as avg_age,sum(age),max(age),min(age) min_age']
        :param sort: 排序  id,name desc
        :param skip: 跳过多少条
        :param limit: 最多返回多少条
        :param db: db
        :param table: 数据集(table)
        :param printInfo: 显示打印信息
        :return: 数组生成器
        """
        return self._select(where=where, field=field, except_field=except_field, group=group, sort=sort, skip=skip,
                            limit=limit,
                            db=db, table=table,
                            printInfo=printInfo, select_more=True)

    def _select(self, where: Union[dict, str], field=None, except_field=None, sort=None, skip=None, limit=None, db=None,
                table=None,
                printInfo=False, select_one=False, select_more=False, group=None):
        # 设置了group后,很多字段就不能设置了
        if group is not None:
            if field is not None or except_field is not None or skip is not None or limit is not None:
                raise Exception('参数[group]和参数[field|except_field|skip|limit]相互排斥')
            if not (isinstance(group, list) and len(group) == 2):
                raise Exception('参数[group]错误')
        where = self._build_where(where)
        self._check_table(db, table)
        if printInfo:
            start = time.time()
            print(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), '开始查询' + ('one' if select_one else ''),
                  self._db, self._table, where)
        collection = self._get_connection()[self._db][self._table]
        result = None
        projection = {}  # 要显示的字段
        if field is not None and except_field is not None:
            raise Exception('field和except_field只能最多设置其中一个参数')
        if field is not None:
            fields = field.strip().split(',')
            for field in fields:
                field = field.strip().replace('`', '')
                if field == '_id':
                    continue
                projection[field] = 1
            projection['_id'] = 1 if '_id' in fields else 0
        if except_field is not None:
            fields = except_field.strip().split(',')
            for field in fields:
                field = field.strip().replace('`', '')
                projection[field] = 0
        if sort is not None:
            tmp = sort.strip().split(',')
            sort = {}
            for row in tmp:
                rows = row.strip().split(' ')
                field = rows[0].replace('`', '')
                sort[field] = 1
                if len(rows) > 1:
                    if rows[-1].lower() == 'desc':
                        sort[field] = -1
        if group is not None:
            pipeline = [{"$match": where}]
            group_field = ['$' + k.strip().replace('`', '') for k in group[0].strip().split(',')]
            pipeline_group = {"$group": {"_id": group_field}}
            for row in group[1].split(','):
                row = [k.replace('`', '').strip() for k in
                       row.strip().replace(' as ', ' ').replace(' As ', ' ').replace(' aS ', ' ').replace(' AS ',
                                                                                                          ' ').split(
                           ' ')]
                row = [row[0], row[-1]]
                new_field_name = row[1]  # as后的字段名
                operator = row[0].split('(')[0].lower()  # 聚合操作 avg sum max ...
                if operator == 'count':
                    operator = 'sum'
                operator_field = row[0].split('(')[1][:-1].strip()  # 操作的字段
                if operator_field == '*':
                    operator_field = 1
                elif mongo._is_int(operator_field):
                    operator_field = int(operator_field)
                else:
                    operator_field = "$" + operator_field
                # print(row,new_field_name,operator,operator_field)
                pipeline_group["$group"][new_field_name] = {f"${operator}": operator_field}
            pipeline.append(pipeline_group)
            if sort is not None:
                pipeline.append({"$sort": sort})
            """ 
            pipeline = [
                    # 阶段1：筛选年龄 >=25 的用户（类似 WHERE）
                    {"$match": {"age": {"$gte": 25}}},
                    # 阶段2：按城市分组（类似 GROUP BY address.city）
                    {"$group": {
                        "_id": "$address.city",  # 分组字段（_id 是分组关键字）
                        "user_count": {"$sum": 1},  # 统计数量（类似 COUNT(*)）
                        "avg_age": {"$avg": "$age"}  # 平均年龄（类似 AVG(age)）
                    }},
                    # 阶段3：按用户数降序排序（类似 ORDER BY user_count DESC）
                    {"$sort": {"user_count": -1}}
                ]
            """
            tmp = collection.aggregate(pipeline)
            # 添加分组字段
            result = []
            for row in tmp:
                for i, k in enumerate(group_field):
                    row[k[1:]] = row['_id'][i]
                result.append(row)
            if select_one:
                result = result[0] if len(result) > 0 else {}
        else:
            if select_more:
                result = collection.find(where, projection)
                if sort is not None:
                    result = result.sort(sort)
                if skip is not None:
                    result = result.skip(skip=skip)
                if limit is not None:
                    result = result.limit(limit=limit)
                result = result.to_list()
            if select_one:
                result = collection.find_one(where, projection)
                result = result if result is not None else {}
        if printInfo:
            print(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), '结束查询' + ('one' if select_one else ''),
                  self._db, self._table,
                  '耗时: %s秒' % round((time.time() - start), 2))
        return result

    def update_one(self, where: Union[dict, str], data_set: dict = None, data_inc: dict = None,
                   data_list_push: dict = None,
                   data_set_push: dict = None,
                   data_list_pull: dict = None, data_field_del: str = None, db=None, table=None,
                   printInfo=False, _push_each_one: bool = None, _pull_each_one: bool = None) -> int:
        return self.update(where=where, data_set=data_set, data_inc=data_inc, data_list_push=data_list_push,
                           data_set_push=data_set_push,
                           data_list_pull=data_list_pull, data_field_del=data_field_del, db=db, table=table,
                           printInfo=printInfo, _push_each_one=_push_each_one, _pull_each_one=_pull_each_one,
                           _update_one=True)

    def update(self, where: Union[dict, str], data_set: dict = None, data_inc: dict = None, data_list_push: dict = None,
               data_set_push: dict = None,
               data_list_pull: dict = None, data_field_del: str = None, db=None, table=None,
               printInfo=False, _push_each_one: bool = None, _pull_each_one: bool = None, _update_one=None) -> int:
        """
        更新数据\n
        :param where: 筛选条件
        :param data_set: 设置字段值 {"age": 26} | {"age": 26, "address.city":"成都"}
        :param data_inc: 字段自增/自减  {"age": 1} age+=1 | {"age": -10} age-=10
        :param data_list_push: 数组添加元素 {'hobbies':'看书'}  {'hobbies': ['钓1鱼', '钓2鱼', '钓3鱼']}
        :param data_set_push: 添加不存在的元素 {'hobbies':'看书'} 如果列表中存在了'看书' 不会重复添加
        :param data_list_pull: 数组删除元素 {'hobbies':'看书'} 如果数组中有多个'看书',会一次性全部删除
        :param data_field_del: 删除字段  name,address.district
        :param db: db
        :param table: 数据集(table)
        :param printInfo: 打印输出信息
        :param _push_each_one: 默认为True, data_list_push和data_set_push设置的数组依次插入而不是作为一个整体
        :param _pull_each_one: 默认为True, data_list_pull设置的数组依次删除而不是作为一个整体
        :param _update_one: 是否只更新一条 默认更新全部匹配到的 可以用update_one更新一条
        :return: int 修改的条目数
        """
        if _push_each_one is None:
            _push_each_one = True
        if _pull_each_one is None:
            _pull_each_one = True
        where = mongo._build_where(where)
        self._check_table(db, table)
        collection = self._get_connection()[self._db][self._table]
        update_data = {}
        if data_set is not None:
            update_data['$set'] = data_set
        if data_inc is not None:
            update_data['$inc'] = data_inc
        if data_list_push is not None:
            if _push_each_one:
                for k, v in data_list_push.items():
                    update_data.setdefault('$push', {})
                    update_data['$push'][k] = {'$each': v} if isinstance(v, list) else v
            else:
                update_data['$push'] = data_list_push
        if data_set_push is not None:
            if _push_each_one:
                for k, v in data_set_push.items():
                    update_data.setdefault('$addToSet', {})
                    update_data['$addToSet'][k] = {'$each': v} if isinstance(v, list) else v
            else:
                update_data['$addToSet'] = data_set_push
        if data_list_pull is not None:
            if _pull_each_one:
                for k, v in data_list_pull.items():
                    update_data.setdefault('$pull', {})
                    update_data['$pull'][k] = {'$in': v} if isinstance(v, list) else v
            else:
                update_data['$pull'] = data_list_pull
        if data_field_del is not None:
            update_data['$unset'] = {k.strip().replace('`', ''): "" for k in data_field_del.strip().split(',')}
        if not update_data:
            raise Exception('没有设定更新数据')
        if printInfo:
            start = time.time()
            print(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), '开始更新' + ('one' if _update_one else ''),
                  self._db, self._table, where,
                  update_data)
        if _update_one is not None:
            result = collection.update_one(
                where,  # 条件
                update_data  # 更新内容
            )
        else:
            result = collection.update_many(
                where,  # 条件
                update_data  # 更新内容
            )
        if printInfo:
            print(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), '结束更新' + ('one' if _update_one else ''),
                  self._db, self._table,
                  '耗时: %s秒' % round((time.time() - start), 2), '匹配: %s条' % result.matched_count,
                  '修改: %s条' % result.modified_count)
        return result.modified_count

    def delete_one(self, where: Union[dict, str], db=None, table=None, printInfo=False) -> int:
        return self.delete(where=where, db=db, table=table, printInfo=printInfo, _delete_one=True)

    def delete(self, where: Union[dict, str], db=None, table=None, printInfo=False, _delete_one=None) -> int:
        """
        删除数据\n
        :param where:
        :param db:
        :param table:
        :param printInfo:
        :param _delete_one:
        :return:
        """
        self._check_table(db, table)
        where = mongo._build_where(where)
        collection = self._get_connection()[self._db][self._table]
        if printInfo:
            start = time.time()
            print(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), '开始删除' + ('one' if _delete_one else ''),
                  self._db, self._table, where)
        if _delete_one:
            result = collection.delete_one(where)
        else:
            result = collection.delete_many(where)
        if printInfo:
            print(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), '结束删除' + ('one' if _delete_one else ''),
                  self._db, self._table,
                  '耗时: %s秒' % round((time.time() - start), 2),
                  '删除: %s条' % result.deleted_count)
        return result.deleted_count

    def DROP_TABLE(self, db, table) -> bool:
        """
        删除表,谨慎操作 操作完成后,库表记录仍是上次的记录\n
        库里面的表删除完了,库就自动没了
        :param db:
        :param table:
        :return:
        """
        result = self._get_connection()[db].drop_collection(table)
        return bool(result.get('ok', False))

    def replace_table_validator(self, fields: list = None, validator=None, db=None, table=None) -> dict:
        """
        替换表验证规则\n
        :param fields: 验证器 [mongo.validator_*, ...]
        :param validator: 原生验证器
        :param db:
        :param table:
        :return:
        """
        return self.create_table_with_validator(table=table,fields=fields, validator=validator, db=db, _replace_mode=True)

    def empty_table_validator(self, db=None, table=None) -> dict:
        """清空表验证器"""
        self._check_table(db, table)
        self._get_connection()[self._db].command({
            "collMod": self._table,
            "validator": {}  # 空字典表示删除所有验证规则
        })
        collection_info = self._get_connection()[self._db].command('listCollections', filter={'name': self._table})
        return collection_info['cursor']['firstBatch'][0]['options'].get('validator', {})

    def create_table_with_validator(self, table,fields: list = None, validator=None, db=None,
                                    _replace_mode=None) -> dict:
        """
        创建带验证器的表 \n
        :param db:
        :param table: 要创建的表
        :param fields: 验证器 [mongo.validator_*, ...]
        :param validator: 原生验证器
        :param _replace_mode: 替换模式
        :return: 当前规则 dict
        """
        """
          validator: {
            $jsonSchema: {
              bsonType: "object",
              required: ["name", "age", "is_active", "join_date", "user_id"],
              properties: {
                // 1. 字符串（扩展：长度约束、正则匹配）
                name: {
                  bsonType: "string",
                  minLength: 2, // 最小长度2
                  maxLength: 20, // 最大长度20
                  description: "用户名必须是2-20位字符串"
                },
                // 2. 整数（区分 int32/int64：用 int 或 long）
                age: {
                  bsonType: "int", // 32位整数（范围：-2^31 ~ 2^31-1）
                  minimum: 0,
                  maximum: 120,
                  description: "年龄必须是0-120的32位整数"
                },
                // 3. 布尔值（true/false）
                is_active: {
                  bsonType: "bool",
                  description: "是否活跃必须是布尔值"
                },
                // 4. 日期类型（支持范围约束）
                join_date: {
                  bsonType: "date",
                  minimum: ISODate("2020-01-01T00:00:00Z"), // 不能早于2020年
                  maximum: new Date(), // 不能晚于当前时间
                  description: "注册日期必须在2020年至今"
                },
                // 5. ObjectId（如关联其他集合的主键）
                user_id: {
                  bsonType: "objectId",
                  description: "用户唯一标识必须是ObjectId类型"
                },
                // 6. 浮点数（double类型，适合小数场景）
                score: {
                  bsonType: "double",
                  minimum: 0,
                  maximum: 100,
                  description: "分数必须是0-100的浮点数"
                },
                // 7. 枚举值（限制字段只能取指定值）
                gender: {
                  bsonType: "string",
                  enum: ["male", "female", "other"], // 仅允许这三个值
                  description: "性别必须是male/female/other之一"
                },
                // 8. 正则匹配（验证字符串格式，如邮箱、手机号）
                email: {
                  bsonType: "string",
                  pattern: "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$", // 邮箱正则
                  description: "邮箱格式必须合法（如xxx@xxx.com）"
                },
                phone: {
                  bsonType: "string",
                  pattern: "^1[3-9]\\d{9}$", // 中国大陆手机号正则
                  description: "手机号必须是11位有效号码"
                }
              }
            }
          }
        """
        self._check_table(db, table)
        if fields is not None and not isinstance(fields, list):
            raise Exception('参数fields需要[mongo.validator_*, ...]')
        if validator is None:
            validator = {
                '$jsonSchema': {
                    "bsonType": "object",
                    "required": [],
                    "properties": {}
                }
            }
            for row in fields:
                field = list(row.keys())[0]
                if '.' in field:  # 处理带.的字段 比如 address.city
                    tmp = field.split('.')
                    if len(tmp) > 2:
                        raise Exception('最多仅支持xx.xx格式的两级结构')
                    main_field = tmp[0]
                    sub_field = tmp[1]
                    if not validator['$jsonSchema']["properties"].get(main_field, False):
                        validator['$jsonSchema']["properties"][main_field] = {
                            "bsonType": "object",
                            "properties": {}
                        }
                    if row['require']:
                        if validator['$jsonSchema']["properties"][main_field].get("required", None) is None:
                            validator['$jsonSchema']["properties"][main_field]["required"] = []
                        # 当前层添加required
                        validator['$jsonSchema']["properties"][main_field]["required"].append(sub_field)
                        # 上一层前层添加required
                        if main_field not in validator['$jsonSchema']["required"]:
                            validator['$jsonSchema']["required"].append(main_field)
                    validator['$jsonSchema']["properties"][main_field]["properties"][sub_field] = row[field]
                else:
                    if row['require']:
                        validator['$jsonSchema']["required"].append(field)
                    validator['$jsonSchema']["properties"][field] = row[field]
            if len(validator['$jsonSchema']['required']) == 0:
                validator['$jsonSchema'].pop('required', None)
        if _replace_mode:
            self._get_connection()[self._db].command({
                "collMod": self._table,  # 要更新的集合名
                "validator": validator,  # 新的完整验证规则
                "validationLevel": "strict",  # 可选：同时修改验证级别（默认 strict）
                "validationAction": "error"  # 可选：同时修改验证动作（默认 error）
            })
        else:
            self._get_connection()[self._db].create_collection(self._table, validator=validator)
        collection_info = self._get_connection()[self._db].command('listCollections', filter={'name': self._table})
        return collection_info['cursor']['firstBatch'][0]['options'].get('validator', {})

    @staticmethod
    def validator_int(field, minimum=None, maximum=None, desc=None, require=True):
        """age: {
          bsonType: "int", // 32位整数（范围：-2^31 ~ 2^31-1）
          minimum: 0,
          maximum: 120,
          description: "年龄必须是0-120的32位整数"
        }"""
        validator = {field: {"bsonType": "int"}, 'require': require}
        if minimum is not None:
            validator[field]['minimum'] = minimum
        if maximum is not None:
            validator[field]['maximum'] = maximum
        if desc is not None:
            validator[field]['description'] = desc
        return validator

    @staticmethod
    def validator_float(field, minimum=None, maximum=None, desc=None, require=True):
        validator = {field: {"bsonType": "double"}, 'require': require}
        if minimum is not None:
            validator[field]['minimum'] = minimum
        if maximum is not None:
            validator[field]['maximum'] = maximum
        if desc is not None:
            validator[field]['description'] = desc
        return validator

    @staticmethod
    def validator_str(field, minLength=None, maxLength=None, desc=None, require=True):
        validator = {field: {"bsonType": "string"}, 'require': require}
        if minLength is not None:
            validator[field]['minLength'] = minLength
        if maxLength is not None:
            validator[field]['maxLength'] = maxLength
        if desc is not None:
            validator[field]['description'] = desc
        return validator

    @staticmethod
    def validator_bool(field, desc=None, require=True):
        validator = {field: {"bsonType": "bool"}, 'require': require}
        if desc is not None:
            validator[field]['description'] = desc
        return validator

    @staticmethod
    def validator_objectId(field, desc=None, require=True):
        validator = {field: {"bsonType": "objectId"}, 'require': require}
        if desc is not None:
            validator[field]['description'] = desc
        return validator

    @staticmethod
    def validator_enum_int(field, enum: list, desc=None, require=True):
        if len(enum) == 0:
            raise Exception('需要设置参数[enum]')
        for i in enum:
            if not isinstance(i, int):
                raise Exception('参数[enum]里每一项需要整数')
        validator = {field: {"bsonType": "int", "enum": enum}, 'require': require}
        if desc is not None:
            validator[field]['description'] = desc
        return validator

    @staticmethod
    def validator_enum_str(field, enum: list, desc=None, require=True):
        if len(enum) == 0:
            raise Exception('需要设置参数[enum]')
        for i in enum:
            if not isinstance(i, str):
                raise Exception('参数[enum]里每一项需要字符串')
        validator = {field: {"bsonType": "string", "enum": enum}, 'require': require}
        if desc is not None:
            validator[field]['description'] = desc
        return validator

    @staticmethod
    def validator_pattern_str(field, pattern, desc=None, require=True):
        """匹配正则字符串"""
        if pattern == 'email':
            pattern = "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$"
        elif pattern == 'phone':
            pattern = "^1[3-9]\\d{9}$"
        validator = {field: {"bsonType": "string", "pattern": pattern}, 'require': require}
        if desc is not None:
            validator[field]['description'] = desc
        return validator

    def create_index(self, single_index: str = None, multi_index: str = None, unique_index: str = None, db=None,
                     table=None):
        """
        创建索引\n 如果不传任何索引参数,将返回当前索引
        :param single_index: 单字段索引 name
        :param multi_index:  联合索引 name,age
        :param unique_index: 唯一索引
        :param db:
        :param table:
        :return:
        """
        self._check_table(db, table)
        collection = self._get_connection()[self._db][self._table]
        if single_index is not None:
            if ',' in single_index:
                raise Exception('参数single_index不合法 %s' % single_index)
            single_index = single_index.strip().replace('`', '')
            collection.create_index(single_index)
        if multi_index is not None:
            if ',' not in multi_index:
                raise Exception('参数multi_index不合法 %s' % multi_index)
            multi_index = [x.strip().replace('`', '') for x in multi_index.strip().split(',')]
            collection.create_index(multi_index)
        if unique_index is not None:
            if ',' in unique_index:
                raise Exception('参数unique_index不合法 %s' % unique_index)
            unique_index = unique_index.strip().replace('`', '')
            collection.create_index(unique_index, unique=True)
        return collection.index_information()

    def drop_index(self, index_name, db=None, table=None):
        """
        删除索引\n
        :param index_name: 索引名 一般单字段索引的索引名是: 字段_1
        :param db:
        :param table:
        :return:
        """
        self._check_table(db, table)
        collection = self._get_connection()[self._db][self._table]
        collection.drop_index(index_name)  # 按索引名删除
        return collection.index_information()

    def list_tables(self, db=None) -> list:
        if db is not None:
            self._db = db
        if self._db is None:
            raise Exception('请设置db')
        results = self._get_connection()[self._db].list_collection_names()
        results.sort()
        return results

    @staticmethod
    def _build_where(where):
        """
        name <> "张and 三" and `age` <= 20 and city.town in (1,2,"or",\'a\') and gender <> \'男\' and gender not in ("女") and exists addr  and not exists `hobbies` and addr != None
        age<=26 and (_id in  ('691ac30a0473c8935aa4d4ca') or name='张三3') and gender='男'
        :param where:
        :return:
        """
        if not bool(where):
            raise Exception('没有where条件')
        if isinstance(where, str):
            operation_hash = {
                '=': '$eq',
                '<>': '$ne',
                '!=': '$ne',
                '>': '$gt',
                '>=': '$gte',
                '<': '$lt',
                '<=': '$lte',
                'IN': '$in',
                'NOT IN': '$nin',
                'EXISTS': '$exists'
            }
            new_where = {"$and": []}
            where = sqlparse.format(where, keyword_case='upper',
                                    use_space_around_operators=True)  # 格式化where 关键字大写 运算符前后加空格
            a = sqlparse.parse(where)  # 解析where
            keys = []
            one = []
            # 把where分解成多个and连接的语句
            for row in a[0].tokens:
                if row.is_whitespace:
                    continue
                if row.is_keyword and str(row) == 'AND':
                    keys.append(one)
                    one = []
                else:
                    one.append(row)
            if len(one) > 0:
                keys.append(one)
            # 处理每一个语句
            for row in keys:
                row_len = len(row)
                if row_len == 1:  # 比较语句 > >= < <= = <> !=
                    if str(row[0]).startswith('('):  # 带括号的语句 括号内只能全是or连接的语句
                        sql = str(row[0]).lstrip('(').rstrip(')').strip()
                        one = []
                        or_where = {"$or": []}
                        # 把where分解成多个and连接的语句
                        for tmp in sqlparse.parse(sql)[0].tokens:
                            if tmp.is_whitespace:
                                continue
                            if tmp.is_keyword and str(tmp) == 'AND':
                                raise Exception('括号内只能全是or连接的语句')
                            if tmp.is_keyword and str(tmp) == 'OR':
                                or_where['$or'].append(mongo._build_where(' '.join([str(k) for k in one]))['$and'][0])
                                one = []
                            else:
                                one.append(tmp)
                        if len(one) > 0:
                            or_where['$or'].append(mongo._build_where(' '.join([str(k) for k in one]))['$and'][0])
                        if len(or_where.get("$or", [])) > 0:
                            new_where["$and"].append(or_where)
                        continue
                    tmp = str(row[0]).strip().split(' ')
                    field = tmp[0].replace('`', '')
                    operation = ''
                    value = ''
                    for i, v in enumerate(tmp):
                        if i == 0:
                            continue
                        if not v:
                            continue
                        operation = v
                        value = ' '.join(tmp[i + 1:]).strip()
                        if value.startswith('"'):  # 字符串
                            value = value.strip('"')
                        elif value.startswith("'"):  # 字符串
                            value = value.strip("'")
                        else:  # 数字类型 整数或者小数
                            pass
                        break
                    if mongo._is_int(value):
                        value = int(value)
                    if mongo._is_float(value):
                        value = float(value)
                    if field == '_id':
                        value = ObjectId(value)
                    new_where['$and'].append({field: {operation_hash[operation]: value}})
                elif row_len == 2:  # 判断字段是否存在 EXISTS
                    # print(row[0],row[1])
                    field = str(row[1]).replace('`', '')
                    if row[0].is_keyword and str(row[0]) == 'EXISTS':
                        new_where['$and'].append({field: {"$exists": True}})
                    else:
                        raise Exception('遇到特殊情况 %s' % str([str(k) for k in row]))
                elif row_len == 3:  # IN / NOT EXISTS / 字段 = None
                    if row[1].is_keyword and str(row[1]) == 'IN':
                        field = str(row[0]).replace('`', '')
                        in_list = ast.literal_eval('[' + str(row[2]).lstrip('(').rstrip(')') + ']')
                        if field == '_id':
                            in_list = [ObjectId(k) for k in in_list]
                        new_where['$and'].append({field: {"$in": in_list}})
                    elif row[0].is_keyword and str(row[0]) == 'NOT' and row[1].is_keyword and str(row[1]) == 'EXISTS':
                        field = str(row[2]).replace('`', '')
                        new_where['$and'].append({field: {"$exists": False}})
                    elif row[2].is_keyword and str(row[2]) == 'NONE':
                        field = str(row[0]).replace('`', '')
                        new_where['$and'].append({field: {operation_hash[str(row[1])]: None}})
                    else:
                        raise Exception('遇到特殊情况 %s' % str([str(k) for k in row]))
                elif row_len == 4:  # NOT IN
                    if row[1].is_keyword and str(row[1]) == 'NOT' and row[2].is_keyword and str(row[2]) == 'IN':
                        field = str(row[0]).replace('`', '')
                        in_list = ast.literal_eval('[' + str(row[3]).lstrip('(').rstrip(')') + ']')
                        if field == '_id':
                            in_list = [ObjectId(k) for k in in_list]
                        new_where['$and'].append({field: {"$nin": in_list}})
                    else:
                        raise Exception('遇到特殊情况 %s' % str([str(k) for k in row]))
                else:
                    raise Exception('遇到特殊情况 %s' % str([str(k) for k in row]))
            if len(new_where.get("$and", [])) == 0:
                raise Exception('没有where条件')
        else:
            new_where = where
        if new_where.get('_id', None):
            new_where['_id'] = ObjectId(new_where['_id'])
        if not new_where:
            raise Exception('没有where条件')
        return new_where

    @staticmethod
    def _is_int(string: str) -> bool:
        """判断字符串是否为整数格式"""
        if not isinstance(string, str):
            string = str(string)
        # 正则表达式：^开头 $结尾，[+-]?可选正负号，\d+至少1位数字
        integer_pattern = re.compile(r'^[+-]?\d+$')
        return bool(integer_pattern.match(string))

    @staticmethod
    def _is_float(string: str) -> bool:
        """判断字符串是否为规范小数格式（含小数点，前后各至少1位数字）"""
        if not isinstance(string, str):
            string = str(string)
        # 正则表达式：^开头 $结尾，[+-]?可选正负号，\d+至少1位数字，\.小数点
        decimal_pattern = re.compile(r'^[+-]?\d+\.\d+$')
        return bool(decimal_pattern.match(string))


if __name__ == '__main__':

    dbIns = mongo(connect_str="mongodb://192.168.41.129:27017/")
    dbIns.db('my_data').table('user0')
    # .table('my_user2')
    # dbIns.insert({'name':'张三','age':20})
    # res = dbIns.update("_id='692010b578daca2439d43d83'",data_set={'age':120})
    # res = dbIns.create_index(single_index='name',multi_index='name,age')
    # res = dbIns.drop_index(index_name='name_1_age_1')
    res = dbIns.update_one(where='_id="6920186bf41a15aa4a632d41"',data_set={'city.a':'aas'})
    # res = dbIns.replace_table_validator(fields=[
    #     mongo.validator_int(field='age',maximum=200,minimum=10,desc='asxxxxxxxx')
    # ])
    # res = dbIns.create_table_with_validator(table='my-user3',fields=[mongo.validator_str(field='name')])
    # res = dbIns.table('my-user3').insert({'name':'qwe'})
    print('操作结果',res)
    # dbIns.DROP_TABLE(db='test2', table='my_user2')

    print('当前数据', dbIns.select('exists _id',field='city.a,city.b'))

    exit()

    # dbIns.create_table_with_validator(db='test2', table='my_user2', fields=[
    #     mongo.validator_int(field='age', minimum=10, maximum=30, desc='年龄需要10-30', require=True),
    #     mongo.validator_str(field='name',minLength=2,maxLength=5,desc='姓名需要2-5'),
    #     mongo.validator_str(field='address.city', minLength=2, maxLength=5, desc='城市需要2-5', require=True),
    # ])
    # dbIns.insert({'name': '李02', 'age': 22, 'address': {"city": 'aaaa', "city2": 'aaaa'}}, db='test2', table='my_user2')
    # dbIns.update(where='_id="691ee6080a568384954a9000"',data_set={'age':13})

    res = dbIns.create_table_with_validator(db='test2', table='my_user2', fields=[
        mongo.validator_int(field='age', minimum=0, maximum=100, desc="年龄需要0-100"),
        mongo.validator_float(field='score', minimum=0, maximum=100, desc="分数需要0-100"),
        mongo.validator_bool(field='live', desc='需要bool类型'),
        mongo.validator_objectId(field='id', desc='需要objectId类型'),
        mongo.validator_enum_str(field='gender', enum=['男', '女'], desc='只能是男女'),
        mongo.validator_enum_int(field='gender2', enum=[2, 3, 5], desc='只能是男女'),
        mongo.validator_pattern_str(field='phone', pattern='phone', require=False)
    ])
    print('当前规则', res)

    dbIns.insert({'name': '李02', 'age': 5, 'address': {"city": 'aaaa', "city2": 'aaaa'}, 'live': True,
                  'id': ObjectId('691ee6080a568384954a9000'), 'score': 100.0, 'gender': '男', 'gender2': 2,
                  'phone': '13113221322'}, db='test2', table='my_user2')
    # dbIns.update(where='_id="691ee6080a568384954a9000"', data_set={'age': 9})
    print('当前数据', dbIns.select('exists _id'))
    exit()
    data1 = [
        {
            "name": "张三",
            "age": 20,
            "gender": "男",
            "hobbies": ["篮球", "音乐"],
            "address": {"city": "北京", "district": "朝阳区"}  # 嵌套子文档
        }, {
            "name": "张三3",
            "age": 28,
            "gender": "男",
            "hobbies": ["篮球", "音乐"],
            "address": {"city": "北京", "district": "朝阳区"}  # 嵌套子文档
        }
    ]
    print('原数据', dbIns.db('test2').table('t0').select('age >= 10'))
    print('聚合数据')
    print(dbIns.db('test2').table('t0').select('age >= 10', group=['address.city,name',
                                                                   'count(*) as user_count,avg(age) as avg_age,sum(age),max(age),min(age) min_age']))
    # dbIns.insert(data)
    exit()
    # res = dbIns.db('test2').list_tables()
    # print(res)
    # exit()
    # for i in range(10):
    #     dbIns.db('test2').table('t%s' % i)
    #     dbIns.insert(data)
    # exit()
    # print(dbIns.DROP_TABLE(db='test',table='test2.users'))
    # exit()
    # res = dbIns.insert(data=data,printInfo=True)
    # exit()
    # res = dbIns.select({'name':'张三',"address.city": {"$in": ["北京", "上海"]},'age':{'$gte':25}})
    # res = dbIns.select_one(
    #     '  name <>    "张and 三"   and   `age`     <=   20 and   city.town   in   (1,2,"or",\'a\')   and   gender <> \'男\' and gender not in ("女") and   exists   addr  and   not   exists   `hobbies`  and addr != None ')
    print('更新前数据')
    group1 = ['name', 'sum(age) as age1']
    res = dbIns.select("exists name")
    for row1 in res:
        print(row1)
    # res = dbIns.update(
    #     where="_id in ('691ac30a0473c8935aa4d4ca','691d3234d77f65df1b0b10ce','691d3234d77f65df1b0b10cf')",
    #     data_set={"age": 30, "address.city": "北京", "address.district": "高新区"},
    #     # data_inc={'age':10},
    #     data_list_pull={'hobbies': [2, 3, '篮球']},
    #     # data_list_pull={'hobbies': ['钓鱼','爬山']},
    #     printInfo=True)
    # res = dbIns.delete(where="name='张三3'",printInfo=True)
    print('更新后数据', res)
    res = dbIns.select("exists name")
    for row1 in res:
        print(row1)
    """
    {"$and": [
        {"name": {"$eq": 1}},
        {"age": {"$eq": 2}},
    ]}和{"name":1,"age":2}
    
    """
