# -*- coding: utf-8 -*-
"""
@Author: HuangJianYi
@Date: 2024-10-15 18:30:21
@LastEditTime: 2025-03-06 10:12:11
@LastEditors: HuangJianYi
@Description: 
"""
from seven_framework.mysql import MySQLHelper
from seven_framework.base_model import *
from seven_cloudapp_frame.models.cache_model import *

class QueueWorkLogModel(CacheModel):
    def __init__(self, db_connect_key='db_cloudapp', db_config_dict=None, sub_table=None, db_transaction=None, context=None):
        super(QueueWorkLogModel, self).__init__(QueueWorkLog, sub_table)
        if not db_config_dict:
            db_config_dict = config.get_value(db_connect_key)
        self.db = MySQLHelper(db_config_dict)
        self.db_connect_key = db_connect_key
        self.db_transaction = db_transaction
        self.db.context = context

    # 方法扩展请继承此类

class QueueWorkLog:
    def __init__(self):
        super(QueueWorkLog, self).__init__()
        self.id = 0 # id
        self.log_id = "" # 记录标识
        self.queue_name = "" # 队列名称
        self.queue_value = "" # 队列值
        self.is_success = "" # 是否成功处理
        self.result_info = "" # 处理结果
        self.create_date = "1970-01-01 00:00:00.000" # 创建时间


    @classmethod
    def get_field_list(self):
        return [
            'id', 'log_id', 'queue_name', 'queue_value', 'is_success', 'result_info', 'create_date'
        ]

    @classmethod
    def get_primary_key(self):
        return "id"

    def __str__(self):
        return "queue_work_log_tb"
