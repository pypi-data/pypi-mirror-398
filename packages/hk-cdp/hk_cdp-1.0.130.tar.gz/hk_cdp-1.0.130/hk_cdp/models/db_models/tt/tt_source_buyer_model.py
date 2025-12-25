# -*- coding: utf-8 -*-
"""
@Author: HuangJianYi
@Date: 2024-12-18 14:23:22
@LastEditTime: 2025-07-16 18:15:16
@LastEditors: HuangJianYi
@Description: 
"""
#此文件由rigger自动生成
from seven_framework.mysql import MySQLHelper
from seven_framework.base_model import *
from seven_cloudapp_frame.models.cache_model import *


class TtSourceBuyerModel(CacheModel):
    def __init__(self, db_connect_key='db_cloudapp', db_config_dict=None, sub_table=None, db_transaction=None, context=None, is_auto=False):
        super(TtSourceBuyerModel, self).__init__(TtSourceBuyer, sub_table)
        if not db_config_dict:
            db_config_dict = config.get_value(db_connect_key)
        self.db = MySQLHelper(self.convert_db_config(db_config_dict, is_auto))
        self.db_connect_key = db_connect_key
        self.db_transaction = db_transaction
        self.db.context = context

    # 方法扩展请继承此类

class TtSourceBuyer:
    def __init__(self):
        super(TtSourceBuyer, self).__init__()
        self.doudian_open_id = ""  # ouid
        self.store_id = ""  # 店铺id
        self.status = ""  # 显示会员的状态
        self.province = ""  # 省份
        self.city = ""  # 城市
        self.last_trade_time = "1900-01-01 00:00:00.000"  # 最后交易的日期
        self.modify_time = "1900-01-01 00:00:00.000"  # 修改时间
        self.create_time = "1900-01-01 00:00:00.000"  # 创建时间

    @classmethod
    def get_field_list(self):
        return [
            'doudian_open_id', 'store_id', 'status', 'province', 'city',
            'last_trade_time', 'modify_time', 'create_time'
        ]

    @classmethod
    def get_primary_key(self):
        return "doudian_open_id"

    def __str__(self):
        return "tt_source_buyer_tb"
