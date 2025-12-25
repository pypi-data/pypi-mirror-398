# -*- coding: utf-8 -*-
"""
@Author: HuangJianYi
@Date: 2024-10-15 18:30:21
@LastEditTime: 2025-03-14 18:28:56
@LastEditors: HuangJianYi
@Description: 
"""
from seven_framework.mysql import MySQLHelper
from seven_framework.base_model import *
from seven_cloudapp_frame.models.cache_model import *

class MemberEventModel(CacheModel):
    def __init__(self, db_connect_key='db_cloudapp', db_config_dict=None, sub_table=None, db_transaction=None, context=None, is_auto=False):
        super(MemberEventModel, self).__init__(MemberEvent, sub_table)
        if not db_config_dict:
            db_config_dict = config.get_value(db_connect_key)
        self.db = MySQLHelper(self.convert_db_config(db_config_dict, is_auto))
        self.db_connect_key = db_connect_key
        self.db_transaction = db_transaction
        self.db.context = context

    # 方法扩展请继承此类

class MemberEvent:
    def __init__(self):
        super(MemberEvent, self).__init__()
        self.id = 0
        self.business_id = 0  # 商家标识
        self.one_id = ""  # one_id
        self.store_id = 0  # 店铺标识
        self.platform_id = 0  # 平台标识(1-淘宝 2-抖音 3-京东 4-微信)
        self.event_type = 0  # 事件类型(1-初始化 2-激活 3-绑定 4-注册 5-退会 6-合并 7-获取手机号)
        self.event_reason = ""  # 事件原因
        self.event_desc = {} # 事件描述
        self.create_date = '1970-01-01 00:00:00.000' # 创建时间

    @classmethod
    def get_field_list(self):
        return ['id', 'business_id', 'one_id', 'store_id', 'platform_id', 'event_type', 'event_reason', 'event_desc', 'create_date']

    @classmethod
    def get_primary_key(self):
        return "id"

    def __str__(self):
        return "member_event_tb"
