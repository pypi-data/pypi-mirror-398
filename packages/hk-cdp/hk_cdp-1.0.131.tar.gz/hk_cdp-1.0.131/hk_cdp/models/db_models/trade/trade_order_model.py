# -*- coding: utf-8 -*-
"""
@Author: HuangJianYi
@Date: 2024-10-15 18:30:21
@LastEditTime: 2025-07-16 18:14:14
@LastEditors: HuangJianYi
@Description:
"""

from seven_framework.mysql import MySQLHelper
from seven_framework.base_model import *
from seven_cloudapp_frame.models.cache_model import *

class TradeOrderModel(CacheModel):
    def __init__(self, db_connect_key='db_cloudapp', db_config_dict=None, sub_table=None, db_transaction=None, context=None, is_auto=False):
        super(TradeOrderModel, self).__init__(TradeOrder, sub_table)
        if not db_config_dict:
            db_config_dict = config.get_value(db_connect_key)
        self.db = MySQLHelper(self.convert_db_config(db_config_dict, is_auto))
        self.db_connect_key = db_connect_key
        self.db_transaction = db_transaction
        self.db.context = context

class TradeOrder:
    def __init__(self):
        super(TradeOrder, self).__init__()
        self.id = 0  # id
        self.business_id = 0 # 商家标识
        self.store_id = 0 # 店铺标识
        self.plat_store_id = "" # 平台店铺标识
        self.user_id = "" # 客户ID
        self.ouid = "" # ouid
        self.platform_id = 0 # 平台标识
        self.main_pay_order_no = "" # 主订单号
        self.sub_pay_order_no = "" # 子订单号
        self.goods_code = "" # 商家编码
        self.goods_name = "" # 商品名称
        self.goods_pic = "" # 商品图片
        self.goods_id = "" # 商品标识
        self.sku_id = "" # sku_id
        self.buy_num = 0 # 购买数量
        self.goods_price = 0.0 # 商品价格
        self.order_price = 0.0 # 子订单金额
        self.pay_price = 0.0 # 子支付金额
        self.discount_price = 0.0 # 优惠金额
        self.divide_order_price = 0.0 # 分摊后子订单实付金额
        self.order_status = "" # 子订单状态
        self.refund_status = "" # 退款状态
        self.refund_id = "" # 退款订单号
        self.refund_price = 0.0 # 退款金额

    @classmethod
    def get_field_list(self):
        return [
            'id', 'business_id', 'store_id', 'plat_store_id', 'user_id', 'ouid', 'platform_id', 'main_pay_order_no', 'sub_pay_order_no', 'goods_code', 'goods_name', 'goods_pic', 'goods_id', 'sku_id', 'buy_num', 'goods_price', 'order_price', 'pay_price', 'discount_price',
            'divide_order_price', 'order_status', 'refund_status', 'refund_id', 'refund_price'
        ]

    @classmethod
    def get_primary_key(self):
        return "id"

    def __str__(self):
        return "trade_order_tb"
