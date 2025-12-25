# -*- coding: utf-8 -*-
"""
@Author: HuangJianYi
@Date: 2024-10-15 18:30:21
@LastEditTime: 2024-12-25 13:37:18
@LastEditors: HuangJianYi
@Description: 
"""
from seven_framework.mysql import MySQLHelper
from seven_framework.base_model import *
from seven_cloudapp_frame.models.cache_model import *

class UserTrendsModel(CacheModel):
    def __init__(self, db_connect_key='db_cloudapp', db_config_dict=None, sub_table=None, db_transaction=None, context=None, is_auto=False):
        super(UserTrendsModel, self).__init__(UserTrends, sub_table)
        if not db_config_dict:
            db_config_dict = config.get_value(db_connect_key)
        self.db = MySQLHelper(self.convert_db_config(db_config_dict, is_auto))
        self.db_connect_key = db_connect_key
        self.db_transaction = db_transaction
        self.db.context = context

    # 方法扩展请继承此类

class UserTrends:
    def __init__(self):
        super(UserTrends, self).__init__()
        self.id = 0
        self.business_id = 0 # 商家标识
        self.user_id = "" # 客户标识
        self.source_type = 0 # 来源类型(1-互动 2-订单 3-营销)
        self.trends_desc = {} # 动态描述
        self.create_date = '1970-01-01 00:00:00.000' # 创建时间
        self.create_day = 0 # 创建天

    @classmethod
    def get_field_list(self):
        return [
            'id', 'business_id', 'user_id', 'source_type', 'trends_desc', 'create_date', 'create_day'
        ]

    @classmethod
    def get_primary_key(self):
        return "id"

    def __str__(self):
        return "user_trends_tb"
