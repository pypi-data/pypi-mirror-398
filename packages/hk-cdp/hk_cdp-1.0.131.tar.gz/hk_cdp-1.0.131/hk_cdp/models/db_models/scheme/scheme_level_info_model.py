# -*- coding: utf-8 -*-
"""
@Author: HuangJianYi
@Date: 2024-10-15 18:30:21
@LastEditTime: 2024-11-14 15:22:28
@LastEditors: HuangJianYi
@Description: 
"""
from seven_framework.mysql import MySQLHelper
from seven_framework.base_model import *
from seven_cloudapp_frame.models.cache_model import *

class SchemeLevelInfoModel(CacheModel):
    def __init__(self, db_connect_key='db_cloudapp', db_config_dict=None, sub_table=None, db_transaction=None, context=None, is_auto=False):
        super(SchemeLevelInfoModel, self).__init__(SchemeLevelInfo, sub_table)
        if not db_config_dict:
            db_config_dict = config.get_value(db_connect_key)
        self.db = MySQLHelper(self.convert_db_config(db_config_dict, is_auto))
        self.db_connect_key = db_connect_key
        self.db_transaction = db_transaction
        self.db.context = context

    # 方法扩展请继承此类

class SchemeLevelInfo:
    def __init__(self):
        super(SchemeLevelInfo, self).__init__()
        self.id = 0
        self.guid = "" # guid
        self.scheme_id = 0 # 会员体系标识
        self.level_id = 0 #  等级标识
        self.level_name = 0 # 等级名称
        self.valid_type = 0 # 有效期类型(1-永久有效 2-过期时间)
        self.expire_type = 0 # 过期类型(1-指定天 2-指定年)
        self.expire_value = '' # 过期值
        self.expire_year = 0 # 过期年
        self.expire_month = 0 # 过期月
        self.expire_day = 0 # 过期天
        self.upgrade_threshold = 0 # 升级条件
        self.relegation_threshold = 0 # 保级条件
        self.is_release = 0 # 是否发布(1-是 0-否)
        self.create_date = '1970-01-01 00:00:00.000' # 创建时间
        self.modify_date = '1970-01-01 00:00:00.000' # 修改时间

    @classmethod
    def get_field_list(self):
        return [
            'id', 'guid', 'scheme_id', 'level_id', 'level_name', 'valid_type', 'expire_type', 'expire_value', 'expire_year', 'expire_month', 'expire_day', 'upgrade_threshold', 'relegation_threshold', 'is_release', 'create_date', 'modify_date'
        ]

    @classmethod
    def get_primary_key(self):
        return "id"

    def __str__(self):
        return "scheme_level_info_tb"
