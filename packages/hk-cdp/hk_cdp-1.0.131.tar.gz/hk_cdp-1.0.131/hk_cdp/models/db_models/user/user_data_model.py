# -*- coding: utf-8 -*-
"""
@Author: HuangJianYi
@Date: 2024-10-15 18:30:21
@LastEditTime: 2024-12-31 10:54:55
@LastEditors: HuangJianYi
@Description: 
"""
from seven_framework.mysql import MySQLHelper
from seven_framework.base_model import *
from seven_cloudapp_frame.models.cache_model import *

class UserDataModel(CacheModel):
    def __init__(self, db_connect_key='db_cloudapp', db_config_dict=None, sub_table=None, db_transaction=None, context=None, is_auto=False):
        super(UserDataModel, self).__init__(UserData, sub_table)
        if not db_config_dict:
            db_config_dict = config.get_value(db_connect_key)
        self.db = MySQLHelper(self.convert_db_config(db_config_dict, is_auto))
        self.db_connect_key = db_connect_key
        self.db_transaction = db_transaction
        self.db.context = context

    # 方法扩展请继承此类

class UserData:
    def __init__(self):
        super(UserData, self).__init__()
        self.id = 0 # id
        self.user_id = "" # 客户ID
        self.ouid = "" # ouid
        self.business_id = 0 # 商家标识
        self.platform_id = 0 # 平台标识(1-淘宝 2-抖音 3-京东)
        self.store_id = 0 # 店铺标识
        self.plat_store_id = "" # 平台店铺标识
        self.first_order_date = "1970-01-01 00:00:00.000" # 首次下单时间
        self.first_pay_date = "1970-01-01 00:00:00.000" # 首次付款时间
        self.last_order_date = "1970-01-01 00:00:00.000" # 最近下单时间
        self.last_pay_date = "1970-01-01 00:00:00.000" # 最近付款时间
        self.last_second_pay_date = "1970-01-01 00:00:00.000"  # 倒数第二次付款时间
        self.last_trade_date = "1970-01-01 00:00:00.000" # 最近交易时间
        self.trade_success_price = 0.0000 # 交易成功金额
        self.trade_success_num = 0 # 交易成功笔数
        self.buy_num = 0 # 购买件数
        self.refund_price = 0.0000 # 退款金额
        self.refund_num = 0 # 退款笔数
        self.presell_order_num = 0 # 预售下单笔数
        self.presell_pay_num = 0 # 预售付款笔数
        self.presell_order_price = 0.0000 # 预售下单金额
        self.presell_pay_price = 0.0000 # 预售付款金额
        self.buy_back_day = 0 # 回购周期天

    @classmethod
    def get_field_list(self):
        return [
            'id', 'user_id', 'ouid', 'business_id', 'platform_id', 'store_id', 'plat_store_id', 'first_order_date', 'first_pay_date', 'last_order_date', 'last_pay_date', 'last_second_pay_date', 'last_trade_date', 'trade_success_price', 'trade_success_num', 'buy_num',
            'refund_price', 'refund_num', 'presell_order_num', 'presell_pay_num', 'presell_order_price', 'presell_pay_price', 'buy_back_day'
        ]

    @classmethod
    def get_primary_key(self):
        return "id"

    def __str__(self):
        return "user_data_tb"
