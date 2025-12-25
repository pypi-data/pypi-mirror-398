# -*- coding: utf-8 -*-
"""
@Author: HuangJianYi
@Date: 2024-10-15 18:30:21
@LastEditTime: 2025-10-22 14:48:07
@LastEditors: HuangJianYi
@Description:
"""

from seven_framework.mysql import MySQLHelper
from seven_framework.base_model import *
from seven_cloudapp_frame.models.cache_model import *

class TradeInfoExModel(CacheModel):
    def __init__(self, db_connect_key='db_cloudapp', db_config_dict=None, sub_table=None, db_transaction=None, context=None, is_auto=False):
        super(TradeInfoExModel, self).__init__(TradeInfoEx, sub_table)
        if not db_config_dict:
            db_config_dict = config.get_value(db_connect_key)
        self.db = MySQLHelper(self.convert_db_config(db_config_dict, is_auto))
        self.db_connect_key = db_connect_key
        self.db_transaction = db_transaction
        self.db.context = context

class TradeInfoEx:
    def __init__(self):
        super(TradeInfoEx, self).__init__()
        self.id = 0  # id
        self.business_id = 0 # 商家标识
        self.store_id = 0 # 店铺标识
        self.plat_store_id = "" # 平台店铺标识
        self.main_pay_order_no = "" # 主订单号
        self.received_payment = 0.0  # 卖家实收金额
        self.expand_card_basic_price_used = 0.0  # 购物金本金支付金额
        self.expand_card_expand_price_used = 0.0  # 购物金权益金支付金额


    @classmethod
    def get_field_list(self):
        return ['id', 'business_id', 'store_id', 'plat_store_id', 'main_pay_order_no', 'received_payment', 'expand_card_basic_price_used', 'expand_card_expand_price_used']

    @classmethod
    def get_primary_key(self):
        return "id"

    def __str__(self):
        return "trade_info_ex_tb"
