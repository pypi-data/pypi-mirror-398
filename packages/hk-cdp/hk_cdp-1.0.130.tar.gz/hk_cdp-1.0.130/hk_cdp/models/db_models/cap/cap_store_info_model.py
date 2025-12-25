#此文件由rigger自动生成
from seven_framework.mysql import MySQLHelper
from seven_framework.base_model import *
from seven_cloudapp_frame.models.cache_model import *

class CapStoreInfoModel(CacheModel):
    def __init__(self, db_connect_key='db_cloudapp', sub_table=None, db_transaction=None, context=None, is_auto=False):
        super(CapStoreInfoModel, self).__init__(CapStoreInfo, sub_table)
        self.db = MySQLHelper(self.convert_db_config(db_connect_key, is_auto))
        self.db_connect_key = db_connect_key
        self.db_transaction = db_transaction
        self.db.context = context

    #方法扩展请继承此类

class CapStoreInfo:

    def __init__(self):
        super(CapStoreInfo, self).__init__()
        self.id = 0  # id
        self.guid = ""  # guid
        self.business_id = 0  # 商家标识
        self.platform_id = 0 # 平台标识
        self.store_name = "" # 店铺名称
        self.seller_nick = ""  # 店铺主账号
        self.seller_id = "" # 店铺主账号id
        self.plat_store_id = "" # 平台店铺标识
        self.product_id = 0  # 产品标识
        self.extend_info = {}  # 扩展信息
        self.is_release = 0  # 是否发布(1-是 0-否)
        self.create_date = "1900-01-01 00:00:00"  # 创建时间
        self.modify_date = "1900-01-01 00:00:00"  # 修改时间

    @classmethod
    def get_field_list(self):
        return ['id', 'guid', 'business_id','platform_id', 'store_name', 'seller_nick', 'seller_id', 'plat_store_id', 'product_id', 'extend_info', 'is_release', 'create_date', 'modify_date']

    @classmethod
    def get_primary_key(self):
        return "id"

    def __str__(self):
        return "cap_store_info_tb"
