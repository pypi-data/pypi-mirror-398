# -*- coding: utf-8 -*-
"""
@Author: HuangJianYi
@Date: 2024-11-06 18:48:03
@LastEditTime: 2024-11-15 09:59:53
@LastEditors: HuangJianYi
@Description: 
"""
#此文件由rigger自动生成
from seven_framework.mysql import MySQLHelper
from seven_framework.base_model import *
from seven_cloudapp_frame.models.cache_model import *

class TradeGiveInfoModel(CacheModel):
    def __init__(self, db_connect_key='db_cloudapp', db_config_dict=None, sub_table=None, db_transaction=None, context=None, is_auto=False):
        super(TradeGiveInfoModel, self).__init__(TradeGiveInfo, sub_table)
        if not db_config_dict:
            db_config_dict = config.get_value(db_connect_key)
        self.db = MySQLHelper(self.convert_db_config(db_config_dict, is_auto))
        self.db_connect_key = db_connect_key
        self.db_transaction = db_transaction
        self.db.context = context

    #方法扩展请继承此类


class TradeGiveInfo:
    def __init__(self):
        super(TradeGiveInfo, self).__init__()
        self.id = 0 # id
        self.main_pay_order_no = ""  # 主订单号
        self.process_type = 0  # 处理类型(1-奖励 2-扣减)
        self.source_type = ""  # 来源类型(1-初始化 2-增量订单)
        self.store_id = 0 # 店铺标识
        self.business_id = 0 # 商家标识
        self.user_id = "" # 客户ID
        self.process_title = "" # 标题
        self.integral = 0 # 积分
        self.growth = 0 # 成长值
        self.create_date = '1970-01-01 00:00:00.000' # 创建时间


    @classmethod
    def get_field_list(self):
        return ['id','main_pay_order_no', 'process_type', 'source_type', 'store_id', 'business_id', 'user_id', 'process_title', 'integral', 'growth', 'create_date']

    @classmethod
    def get_primary_key(self):
        return "id"

    def __str__(self):
        return "trade_give_info_tb"
