# -*- coding: utf-8 -*-
"""
@Author: HuangJianYi
@Date: 2024-10-15 18:30:21
@LastEditTime: 2025-07-16 18:14:14
@LastEditors: HuangJianYi
@Description:
"""

from seven_framework.mysql import MySQLHelper
from seven_framework.base_model import *
from seven_cloudapp_frame.models.cache_model import *


class TradeOrderExcludeModel(CacheModel):
    def __init__(self, db_connect_key='db_cloudapp', db_config_dict=None, sub_table=None, db_transaction=None, context=None, is_auto=False):
        super(TradeOrderExcludeModel, self).__init__(TradeOrderExclude, sub_table)
        if not db_config_dict:
            db_config_dict = config.get_value(db_connect_key)
        self.db = MySQLHelper(self.convert_db_config(db_config_dict, is_auto))
        self.db_connect_key = db_connect_key
        self.db_transaction = db_transaction
        self.db.context = context


class TradeOrderExclude:
    def __init__(self):
        super(TradeOrderExclude, self).__init__()
        self.id = 0  # id
        self.user_id = "" # 客户ID
        self.business_id = 0 # 商家标识
        self.store_id = 0 # 店铺标识
        self.main_pay_order_no = "" # 主订单号
        self.sub_pay_order_no = "" # 子订单号
        self.goods_id = "" # 商品标识
        self.is_give_integral = 0  # 是否赠送积分(1-是 0-否)
        self.is_give_growth = 0  # 是否赠送成长值(1-是 0-否)
        self.create_date = '1970-01-01 00:00:00'  # 创建时间


    @classmethod
    def get_field_list(self):
        return [
            'id', 'user_id', 'business_id', 'store_id', 'main_pay_order_no', 'sub_pay_order_no', 'goods_id', 'is_give_integral', 'is_give_growth', 'create_date'
        ]

    @classmethod
    def get_primary_key(self):
        return "id"

    def __str__(self):
        return "trade_order_exclude_tb"
