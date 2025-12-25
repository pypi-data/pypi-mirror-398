# -*- coding: utf-8 -*-
"""
@Author: HuangJianYi
@Date: 2024-12-31 11:25:23
@LastEditTime: 2025-07-11 10:32:22
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

class AnalysisReportModel(CacheModel):
    def __init__(self, db_connect_key='db_cloudapp', db_config_dict=None, sub_table=None, db_transaction=None, context=None, is_auto=False):
        super(AnalysisReportModel, self).__init__(AnalysisReport, sub_table)
        if not db_config_dict:
            db_config_dict = config.get_value(db_connect_key)
        self.db = MySQLHelper(self.convert_db_config(db_config_dict, is_auto))
        self.db_connect_key = db_connect_key
        self.db_transaction = db_transaction
        self.db.context = context

    # 方法扩展请继承此类

class AnalysisReport:
    def __init__(self):
        self.id = 0  # 唯一键,根据业务md5int生成
        self.business_id = 0  # 商家标识
        self.platform_id = 0  # 平台标识(1-淘宝 2-抖音 3-京东 4-微信)
        self.store_id = 0  # 店铺标识
        self.scheme_id = 0  # 会员体系标识
        self.cycle_type = 2  # 周期类型(1-年 2-月 3-日)
        self.report_type = 0  # 报表类型
        self.stat_date = 0  # 统计时间
        self.report_data = {}  # 报表数据 (JSON)
        self.modify_date = '1970-01-01 00:00:00.000'  # 修改时间

    @classmethod
    def get_field_list(self):
        return [
            'id', 'business_id', 'platform_id', 'store_id',
            'scheme_id', 'cycle_type', 'report_type',
            'stat_date', 'report_data', 'modify_date'
        ]

    @classmethod
    def get_primary_key(self):
        return "id"

    def __str__(self):
        return "analysis_report_tb"
