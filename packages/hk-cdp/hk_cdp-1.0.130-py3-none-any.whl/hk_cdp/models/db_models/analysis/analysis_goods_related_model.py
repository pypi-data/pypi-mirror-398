# -*- coding: utf-8 -*-
"""
@Author: HuangJianYi
@Date: 2024-10-15 18:30:21
@LastEditTime: 2025-07-15 17:20:19
@LastEditors: HuangJianYi
@Description: 
"""
from seven_framework.mysql import MySQLHelper
from seven_framework.base_model import *
from seven_cloudapp_frame.models.cache_model import *


class AnalysisGoodsRelatedModel(CacheModel):
    def __init__(self, db_connect_key='db_cloudapp', db_config_dict=None, sub_table=None, db_transaction=None, context=None, is_auto=False):
        super(AnalysisGoodsRelatedModel, self).__init__(AnalysisGoodsRelated, sub_table)
        if not db_config_dict:
            db_config_dict = config.get_value(db_connect_key)
        self.db = MySQLHelper(self.convert_db_config(db_config_dict, is_auto))
        self.db_connect_key = db_connect_key
        self.db_transaction = db_transaction
        self.db.context = context

    # 方法扩展请继承此类


class AnalysisGoodsRelated:
    def __init__(self):
        self.id = 0  # 唯一键,根据业务md5int生成
        self.business_id = 0  # 商家标识
        self.platform_id = 0  # 平台标识(1-淘宝 2-抖音 3-京东 4-微信)
        self.store_id = 0  # 店铺标识
        self.a_goods_id = ''  # A商品ID
        self.a_buyer_count = 0  # 购买A商品人数
        self.b_goods_id = ''  # B商品ID
        self.b_buyer_count = 0  # 购买B商品人数
        self.a_and_b_buyer_count = 0  # 同时购买A和B人数
        self.buy_rate = 0  # 购买连带率
        self.recommend_buyer_count = 0  # 可推荐人数
        self.rank_num = 0  # 排行号
        self.stat_date = 0  # 统计时间(20241231)
        self.create_date = '1970-01-01 00:00:00.000'  # 创建时间

    @classmethod
    def get_field_list(self):
        return ['id', 'business_id', 'platform_id', 'store_id', 'a_goods_id', 'a_buyer_count', 'b_goods_id', 'b_buyer_count', 'a_and_b_buyer_count', 'buy_rate', 'recommend_buyer_count', 'rank_num', 'stat_date', 'create_date']

    @classmethod
    def get_primary_key(self):
        return "id"

    def __str__(self):
        return "analysis_goods_related_tb"
