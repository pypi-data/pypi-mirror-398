# -*- coding: utf-8 -*-
"""
@Author: HuangJianYi
@Date: 2024-11-19 15:01:40
@LastEditTime: 2025-08-22 17:32:54
@LastEditors: HuangJianYi
@Description: 
"""

#此文件由rigger自动生成
from seven_framework.mysql import MySQLHelper
from seven_framework.base_model import *
from seven_cloudapp_frame.models.cache_model import *

class StoreBaseModel(CacheModel):
    def __init__(self, db_connect_key='db_cloudapp', db_config_dict=None, sub_table=None, db_transaction=None, context=None, is_auto=False):
        super(StoreBaseModel, self).__init__(StoreBase, sub_table)
        if not db_config_dict:
            db_config_dict = config.get_value(db_connect_key)
        self.db = MySQLHelper(self.convert_db_config(db_config_dict, is_auto))
        self.db_connect_key = db_connect_key
        self.db_transaction = db_transaction
        self.db.context = context

    #方法扩展请继承此类

class StoreBase:

    def __init__(self):
        super(StoreBase, self).__init__()
        self.id = 0  # id
        self.guid = None  # guid
        self.business_id = 0  # 商家标识
        self.scheme_id = 0 # 体系标识
        self.platform_id = 0  # 平台标识
        self.store_name = ""  # 店铺名称
        self.seller_nick = ""  # 店铺主账号
        self.plat_store_id = ""  # 平台店铺标识
        self.init_integral_multiple = ""  # 初始积分倍数
        self.init_growth_config = {}  # 初始成长值配置
        self.init_exclude_goods = {} # 初始排除商品
        self.incr_process_start_date = "1970-01-01 00:00:00.000"  # 增量处理时间
        self.is_omid_merge = 0 # 是否走omid合并逻辑(1-是 0-否)
        self.create_date = "1970-01-01 00:00:00.000"  # 创建时间
        self.modify_date = "1970-01-01 00:00:00.000"  # 修改时间


    @classmethod
    def get_field_list(self):
        return ['id', 'guid', 'business_id', 'scheme_id', 'platform_id', 'store_name', 'seller_nick', 'plat_store_id', 'init_integral_multiple', 'init_growth_config', 'init_exclude_goods', 'incr_process_start_date', 'is_omid_merge', 'create_date', 'modify_date']

    @classmethod
    def get_primary_key(self):
        return "id"

    def __str__(self):
        return "store_base_tb"
