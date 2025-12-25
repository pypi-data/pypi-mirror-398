# -*- coding: utf-8 -*-
"""
@Author: HuangJianYi
@Date: 2024-10-15 18:30:21
@LastEditTime: 2025-01-07 15:21:16
@LastEditors: HuangJianYi
@Description: 抖音历史会员表模型
"""
from seven_framework.mysql import MySQLHelper
from seven_framework.base_model import *
from seven_cloudapp_frame.models.cache_model import *

class TtSourceHistoryMemberModel(CacheModel):
    def __init__(self, db_connect_key='db_cloudapp', db_config_dict=None, sub_table=None, db_transaction=None, context=None, is_auto=False):
        super(TtSourceHistoryMemberModel, self).__init__(TtSourceHistoryMember, sub_table)
        if not db_config_dict:
            db_config_dict = config.get_value(db_connect_key)
        self.db = MySQLHelper(self.convert_db_config(db_config_dict, is_auto))
        self.db_connect_key = db_connect_key
        self.db_transaction = db_transaction
        self.db.context = context

    # 方法扩展请继承此类

class TtSourceHistoryMember:
    def __init__(self):
        super(TtSourceHistoryMember, self).__init__()
        self.doudian_open_id = ""  # doudian_open_id
        self.union_id = "" # union_id
        self.store_id = ""  # 店铺id
        self.current_points = ""  # 积分余额
        self.level_id = 0  # 等级
        self.mobile = ""  # 明文手机号
        self.mask_mobile = ""  # 掩码手机号
        self.encode_mobile = "" # 加密手机号（可能是明文手机号或掩码手机号的加密值）
        self.apply_time = '1900-01-01 00:00:00.000'  # 入会时间
        self.order_total_amount = 0.0000  # 订单总金额
        self.order_count = 0  # 订单量
        self.modify_time = '1900-01-01 00:00:00.000'  # 修改时间
        self.create_time = '1900-01-01 00:00:00.000'  # 创建时间

    @classmethod
    def get_field_list(self):
        return ['doudian_open_id', 'union_id', 'store_id', 'current_points', 'level_id', 'mobile', 'mask_mobile', 'encode_mobile', 'apply_time', 'order_total_amount', 'order_count', 'modify_time', 'create_time']

    @classmethod
    def get_primary_key(self):
        return "doudian_open_id"

    def __str__(self):
        return "tt_source_history_member_tb"
