# -*- coding: utf-8 -*-
"""
@Author: HuangJianYi
@Date: 2024-10-15 18:30:21
@LastEditTime: 2024-11-22 11:57:18
@LastEditors: HuangJianYi
@Description: 
"""
from seven_framework.mysql import MySQLHelper
from seven_framework.base_model import *
from seven_cloudapp_frame.models.cache_model import *

class SyncUserDataModel(CacheModel):
    def __init__(self, db_connect_key='db_cloudapp', db_config_dict=None, sub_table=None, db_transaction=None, context=None, is_auto=False):
        super(SyncUserDataModel, self).__init__(SyncUserData, sub_table)
        if not db_config_dict:
            db_config_dict = config.get_value(db_connect_key)
        self.db = MySQLHelper(self.convert_db_config(db_config_dict, is_auto))
        self.db_connect_key = db_connect_key
        self.db_transaction = db_transaction
        self.db.context = context

    # 方法扩展请继承此类

class SyncUserData:
    def __init__(self):
        super(SyncUserData, self).__init__()
        self.id = 0 # id
        self.business_id = 0 # 商家标识
        self.store_id = 0 # 店铺标识
        self.user_id = "" # 客户ID
        self.sync_count = 0 # 次数
        self.create_date = "1970-01-01 00:00:00.000" # 创建时间


    @classmethod
    def get_field_list(self):
        return [
            'id', 'business_id', 'store_id', 'user_id', 'sync_count', 'create_date'
        ]

    @classmethod
    def get_primary_key(self):
        return "id"

    def __str__(self):
        return "sync_user_data_tb"
