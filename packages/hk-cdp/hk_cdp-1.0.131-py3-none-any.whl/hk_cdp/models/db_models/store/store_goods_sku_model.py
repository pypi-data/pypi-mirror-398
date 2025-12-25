from seven_framework.mysql import MySQLHelper
from seven_framework.base_model import *
from seven_cloudapp_frame.models.cache_model import *


class StoreGoodsSkuModel(CacheModel):
    def __init__(self, db_connect_key='db_cloudapp', db_config_dict=None, sub_table=None, db_transaction=None, context=None, is_auto=False):
        super(StoreGoodsSkuModel, self).__init__(StoreGoodsSku, sub_table)
        if not db_config_dict:
            db_config_dict = config.get_value(db_connect_key)
        self.db = MySQLHelper(self.convert_db_config(db_config_dict, is_auto))
        self.db_connect_key = db_connect_key
        self.db_transaction = db_transaction
        self.db.context = context

    # 方法扩展请继承此类


class StoreGoodsSku:
    def __init__(self):
        super(StoreGoodsSku, self).__init__()
        self.id = 0  # ID
        self.business_id = 0  # 商家标识
        self.store_id = 0  # 店铺标识
        self.platform_id = 0  # 平台标识
        self.plat_store_id = ""  # 平台店铺标识
        self.goods_id = ""  # 商品ID
        self.sku_id = ""  # sku_id
        self.goods_code = ""  # 商家编码
        self.properties = ""  # 属性
        self.properties_name = ""  # 属性名称
        self.price = 0.0000  # 价格
        self.quantity = 0  # 数量
        self.status = ''  # sku状态(0-下架 1-上架)
        self.sku_pic = ''  # 图片
        self.create_date = "1970-01-01 00:00:00.000"  # 创建时间
        self.modify_date = "1970-01-01 00:00:00.000"  # 修改时间

    @classmethod
    def get_field_list(self):
        return ['id', 'business_id', 'store_id', 'platform_id', 'plat_store_id', 'goods_id', 'sku_id', 'goods_code', 'properties', 'properties_name', 'price', 'quantity', 'status', 'sku_pic', 'create_date', 'modify_date']

    @classmethod
    def get_primary_key(self):
        return "id"

    def __str__(self):
        return "store_goods_sku_tb"
