# -*- coding: utf-8 -*-
"""
@Author: HuangJianYi
@Date: 2024-10-15 18:30:21
@LastEditTime: 2024-11-14 15:10:45
@LastEditors: HuangJianYi
@Description: 体系信息表对应的模型类
"""

from seven_framework.mysql import MySQLHelper
from seven_framework.base_model import *
from seven_cloudapp_frame.models.cache_model import *

class SchemeInfoModel(CacheModel):
    def __init__(self, db_connect_key='db_cloudapp', db_config_dict=None, sub_table=None, db_transaction=None, context=None, is_auto=False):
        super(SchemeInfoModel, self).__init__(SchemeInfo, sub_table)
        if not db_config_dict:
            db_config_dict = config.get_value(db_connect_key)
        self.db = MySQLHelper(self.convert_db_config(db_config_dict, is_auto))
        self.db_connect_key = db_connect_key
        self.db_transaction = db_transaction
        self.db.context = context

    # 方法扩展请继承此类

class SchemeInfo:
    def __init__(self):
        super(SchemeInfo, self).__init__()
        self.id = 0  # id
        self.guid = ""  # guid
        self.business_id = 0  # 商家标识
        self.scheme_name = ""  # 体系名称
        self.level_rule_type = 1  # 等级规则类型(1-成长值等级 2-行为等级)
        self.operate_user_id = ""  # 操作用户标识
        self.operate_user_name = ""  # 操作用户名称
        self.extend_info = {}  # 拓展信息
        self.create_date = '1970-01-01 00:00:00.000'  # 创建时间
        self.modify_date = '1970-01-01 00:00:00.000'  # 修改时间

    @classmethod
    def get_field_list(self):
        return [
            'id', 'guid', 'business_id', 'scheme_name', 'level_rule_type', 'operate_user_id', 'operate_user_name', 'extend_info', 'create_date', 'modify_date'
        ]

    @classmethod
    def get_primary_key(self):
        return "id"

    def __str__(self):
        return "scheme_info_tb"
