# -*- coding: utf-8 -*-
"""
@Author: HuangJianYi
@Date: 2024-12-31 11:25:23
@LastEditTime: 2025-07-15 19:08:55
@LastEditors: HuangJianYi
@Description: 
"""
# -*- coding: utf-8 -*-
"""
@Author: HuangJianYi
@Date: 2024-10-15 18:30:21
@LastEditTime: 2025-07-11 10:31:39
@LastEditors: HuangJianYi
@Description: 
"""
from seven_framework.mysql import MySQLHelper
from seven_framework.base_model import *
from seven_cloudapp_frame.models.cache_model import *


class AnalysisGoodsRepurchaseModel(CacheModel):
    def __init__(self, db_connect_key='db_cloudapp', db_config_dict=None, sub_table=None, db_transaction=None, context=None, is_auto=False):
        super(AnalysisGoodsRepurchaseModel, self).__init__(AnalysisGoodsRepurchase, sub_table)
        if not db_config_dict:
            db_config_dict = config.get_value(db_connect_key)
        self.db = MySQLHelper(self.convert_db_config(db_config_dict, is_auto))
        self.db_connect_key = db_connect_key
        self.db_transaction = db_transaction
        self.db.context = context

    # 方法扩展请继承此类


class AnalysisGoodsRepurchase:
    def __init__(self):
        self.id = 0  # 唯一键,根据业务md5int生成
        self.business_id = 0  # 商家标识
        self.platform_id = 0  # 平台标识(1-淘宝 2-抖音 3-京东 4-微信)
        self.store_id = 0  # 店铺标识
        self.goods_id = ''  # 商品ID
        self.total_sales = 0  # 总销量
        self.buyer_count = 0  # 购买人数
        self.repurchase_count = 0  # 复购人数
        self.repurchase_rate = 0  # 复购率
        self.avg_purchase_times = 0  # 人均购买次数
        self.avg_repurchase_cycle = 0  # 平均复购周期(天)
        self.today_expired_count = 0  # 今日到期未购买人数
        self.recent_7days_expired_count = 0  # 近7日到期未购买人数
        self.stat_date = 0  # 统计时间(20241231)
        self.create_date = '1970-01-01 00:00:00.000'  # 创建时间

    @classmethod
    def get_field_list(self):
        return ['id', 'business_id', 'platform_id', 'store_id', 'goods_id', 'total_sales', 'buyer_count', 'repurchase_count', 'repurchase_rate', 'avg_purchase_times', 'avg_repurchase_cycle', 'today_expired_count', 'recent_7days_expired_count', 'stat_date', 'create_date']

    @classmethod
    def get_primary_key(self):
        return "id"

    def __str__(self):
        return "analysis_goods_repurchase_tb"
