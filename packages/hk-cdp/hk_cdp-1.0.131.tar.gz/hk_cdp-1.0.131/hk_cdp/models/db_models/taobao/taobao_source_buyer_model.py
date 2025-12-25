# -*- coding: utf-8 -*-
"""
@Author: HuangJianYi
@Date: 2024-10-15 18:30:21
@LastEditTime: 2024-10-16 18:35:57
@LastEditors: HuangJianYi
@Description: 
"""
from seven_framework.mysql import MySQLHelper
from seven_framework.base_model import *
from seven_cloudapp_frame.models.cache_model import *

class TaobaoSourceBuyerModel(CacheModel):
    def __init__(self, db_connect_key='db_cloudapp', db_config_dict=None, sub_table=None, db_transaction=None, context=None, is_auto=False):
        super(TaobaoSourceBuyerModel, self).__init__(TaobaoSourceBuyer, sub_table)
        if not db_config_dict:
            db_config_dict = config.get_value(db_connect_key)
        self.db = MySQLHelper(self.convert_db_config(db_config_dict, is_auto))
        self.db_connect_key = db_connect_key
        self.db_transaction = db_transaction
        self.db.context = context

    # 方法扩展请继承此类

class TaobaoSourceBuyer:
    def __init__(self):
        super(TaobaoSourceBuyer, self).__init__()
        self.ouid = ""
        self.store_id = ""
        self.open_uid = ""
        self.item_num = 0
        self.close_trade_amount = 0.0000
        self.group_ids = ""
        self.status = ""
        self.relation_source = 0
        self.trade_amount = 0.0000
        self.grade = 0
        self.close_trade_count = 0
        self.last_trade_time = "1900-01-01 00:00:00.000"
        self.trade_count = 0
        self.biz_order_id = 0
        self.grade_name = ""
        self.item_close_count = 0
        self.city = ""
        self.province = ""
        self.avg_price = 0.0000
        self.modify_time = "1900-01-01 00:00:00.000"
        self.create_time = "1900-01-01 00:00:00.000"

    @classmethod
    def get_field_list(self):
        return [
            'ouid', 'store_id', 'open_uid', 'item_num', 'close_trade_amount',
            'group_ids', 'status', 'relation_source', 'trade_amount', 'grade',
            'close_trade_count', 'last_trade_time', 'trade_count', 'biz_order_id',
            'grade_name', 'item_close_count', 'city', 'province', 'avg_price',
            'modify_time', 'create_time'
        ]

    @classmethod
    def get_primary_key(self):
        return "ouid"

    def __str__(self):
        return "taobao_source_buyer_tb"
