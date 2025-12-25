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

class SyncMemberMobileModel(CacheModel):
    def __init__(self, db_connect_key='db_cloudapp', db_config_dict=None, sub_table=None, db_transaction=None, context=None, is_auto=False):
        super(SyncMemberMobileModel, self).__init__(SyncMemberMobile, sub_table)
        if not db_config_dict:
            db_config_dict = config.get_value(db_connect_key)
        self.db = MySQLHelper(self.convert_db_config(db_config_dict, is_auto))
        self.db_connect_key = db_connect_key
        self.db_transaction = db_transaction
        self.db.context = context

    #方法扩展请继承此类


class SyncMemberMobile:
    def __init__(self):
        super(SyncMemberMobile, self).__init__()
        self.id = 0 # id
        self.user_id = ""  # 客户ID
        self.ouid = ""  # ouid
        self.business_id = 0 # 商家标识
        self.store_id = 0  # 店铺标识
        self.platform_id = 0  # 平台标识(1-淘宝 2-抖音 3-京东 4-微信)
        self.main_pay_order_no = ""  # 主订单号
        self.order_create_date = '1970-01-01 00:00:00.000'  # 订单创建时间
        self.sync_count = 0  # 同步次数
        self.sync_date = '1970-01-01 00:00:00.000'  # 同步时间
        self.create_date = '1970-01-01 00:00:00.000'  # 创建时间


    @classmethod
    def get_field_list(self):
        return ['id', 'user_id', 'ouid', 'business_id', 'store_id', 'platform_id', 'main_pay_order_no', 'order_create_date', 'sync_count', 'sync_date', 'create_date']

    @classmethod
    def get_primary_key(self):
        return "id"

    def __str__(self):
        return "sync_member_mobile_tb"
