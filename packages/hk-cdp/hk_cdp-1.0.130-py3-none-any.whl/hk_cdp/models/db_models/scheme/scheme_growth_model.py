# -*- coding: utf-8 -*-
"""
@Author: HuangJianYi
@Date: 2024-10-15 18:30:21
@LastEditTime: 2025-07-11 10:38:04
@LastEditors: HuangJianYi
@Description: 
"""
from seven_framework.mysql import MySQLHelper
from seven_framework.base_model import *
from seven_cloudapp_frame.models.cache_model import *

class SchemeGrowthModel(CacheModel):
    def __init__(self, db_connect_key='db_cloudapp', db_config_dict=None, sub_table=None, db_transaction=None, context=None, is_auto=False):
        super(SchemeGrowthModel, self).__init__(SchemeGrowth, sub_table)
        if not db_config_dict:
            db_config_dict = config.get_value(db_connect_key)
        self.db = MySQLHelper(self.convert_db_config(db_config_dict, is_auto))
        self.db_connect_key = db_connect_key
        self.db_transaction = db_transaction
        self.db.context = context

    # 方法扩展请继承此类

class SchemeGrowth:
    def __init__(self):
        super(SchemeGrowth, self).__init__()
        self.id = 0
        self.guid = "" # guid
        self.scheme_id = 0 # 会员体系标识
        self.is_grant = 0 # 是否开启发放（1-是 0-否）
        self.config_type = 0 # 配置类型（1-初始设置 2-基础设置 3-扣减设置 4-有效期设置）
        self.config_content = {} # 配置内容
        self.create_date = '1970-01-01 00:00:00.000' # 创建时间
        self.modify_date = '1970-01-01 00:00:00.000' # 修改时间

    @classmethod
    def get_field_list(self):
        return [
            'id', 'guid', 'scheme_id', 'is_grant', 'config_type', 'config_content', 'create_date', 'modify_date'
        ]

    @classmethod
    def get_primary_key(self):
        return "id"

    def __str__(self):
        return "scheme_growth_tb"
