# -*- coding: utf-8 -*-
"""
@Author: HuangJianYi
@Date: 2024-11-06 09:39:45
@LastEditTime: 2025-07-11 10:34:43
@LastEditors: HuangJianYi
@Description: 
"""

# 此文件由rigger自动生成
from seven_framework.mysql import MySQLHelper
from seven_framework.base_model import *
from seven_cloudapp_frame.models.cache_model import *

class CdpStoreInfoModel(CacheModel):
    def __init__(self, db_connect_key='db_cloudapp', sub_table=None, db_transaction=None, context=None, is_auto=False):
        super(CdpStoreInfoModel, self).__init__(CdpStoreInfo, sub_table)
        self.db = MySQLHelper(self.convert_db_config(db_connect_key, is_auto))
        self.db_connect_key = db_connect_key
        self.db_transaction = db_transaction
        self.db.context = context

    # 方法扩展请继承此类

class CdpStoreInfo:

    def __init__(self):
        super(CdpStoreInfo, self).__init__()
        self.id = 0  # id
        self.guid = None  # guid
        self.store_name = ""  # 店铺名称
        self.store_icon = ""  # 店铺图标
        self.plat_store_id = ""  # 平台店铺标识
        self.store_status = 0  # 店铺状态
        self.create_date = '1970-01-01 00:00:00.000'  # 创建时间
        self.modify_date = '1970-01-01 00:00:00.000'  # 修改时间
        self.plat_telephone_key = ""  # 平台手机号密钥
        self.prefix_status = 0  # 号段生成状态
        self.prefix_path = ""  # 号段存储路径
        self.business_id = 0  # 商家标识
        self.seller_nick = ""  # 店铺主账号
        self.seller_id = "" # 店铺主账号id
        self.platform_id = 0  # 平台类型
        self.overdue_date = '1970-01-01 00:00:00.000'  # 过期时间
        self.access_token = ""  # access_token
        self.extend_info = {} # 扩展信息json
        self.description = ""  # 描述
        self.cdp_rawdata_sync_status = 0  # cdp_原始数据同步状态(0-未开始 1-同步历史数据 2-同步增量数据)
        self.history_data_clean_status = 0  # 历史数据清洗状态(0-未开始 1-进行中 2-已完成)
        self.history_member_init_status = 0 # 历史会员初始化状态(0-未开始 1-进行中 2-已完成)
        self.is_start_work = 0  # 是否开启作业服务(1-是 0-否)
        self.work_config = {}  # 作业配置json


    @classmethod
    def get_field_list(self):
        return [
            'id', 'guid', 'store_name', 'store_icon', 'plat_store_id', 'store_status', 'create_date', 'modify_date', 'plat_telephone_key', 'prefix_status', 'prefix_path', 'business_id', 'seller_nick', 'seller_id', 'platform_id', 'overdue_date', 'access_token', 'extend_info',
            'description', 'cdp_rawdata_sync_status', 'history_data_clean_status', 'history_member_init_status', 'is_start_work', 'work_config'
        ]

    @classmethod
    def get_primary_key(self):
        return "id"

    def __str__(self):
        return "cdp_store_info_tb"
