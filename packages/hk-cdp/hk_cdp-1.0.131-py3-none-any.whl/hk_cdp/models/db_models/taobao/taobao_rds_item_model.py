# -*- coding: utf-8 -*-
"""
@Author: HuangJianYi
@Date: 2024-11-22 17:10:05
@LastEditTime: 2025-07-11 10:42:49
@LastEditors: HuangJianYi
@Description: 
"""
#此文件由rigger自动生成
from seven_framework.mysql import MySQLHelper
from seven_framework.base_model import *
from seven_cloudapp_frame.models.cache_model import *


class TaoBaoRdsItemModel(CacheModel):
    def __init__(self, db_connect_key='db_cloudapp', db_config_dict=None, sub_table=None, db_transaction=None, context=None, is_auto=False):
        super(TaoBaoRdsItemModel, self).__init__(TaoBaoRdsItem, sub_table)
        if not db_config_dict:
            db_config_dict = config.get_value(db_connect_key)
        self.db = MySQLHelper(self.convert_db_config(db_config_dict, is_auto))
        self.db_connect_key = db_connect_key
        self.db_transaction = db_transaction
        self.db.context = context

    #方法扩展请继承此类


class TaoBaoRdsItem:
    def __init__(self):
        super(TaoBaoRdsItem, self).__init__()
        self.num_iid = 0  # 商品号
        self.seller_nick = ""  # 卖家昵称
        self.approve_status = ""  # 类型
        self.has_showcase = ""  # 卖家昵称
        self.created = ""  # 创建时间
        self.modified = ""  # 修改时间
        self.cid = ""  # 分类id
        self.has_discount = ""  # 分类id
        self.jdp_hashcode = ""  # jdp_hashcode
        self.jdp_response = {}  # 接口返回值
        self.jdp_delete = 0  # jdp_delete
        self.jdp_created = ""  # jdp_created
        self.jdp_modified = ""  # jdp_modified

    @classmethod
    def get_field_list(self):
        return ['num_iid', 'seller_nick', 'approve_status', 'has_showcase', 'created', 'modified', 'cid', 'has_discount', 'jdp_hashcode', 'jdp_response', 'jdp_delete', 'jdp_created', 'jdp_modified']

    @classmethod
    def get_primary_key(self):
        return "num_iid"

    def __str__(self):
        return "taobao_rds_item_tb"
