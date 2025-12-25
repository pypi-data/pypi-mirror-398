#此文件由rigger自动生成
from seven_framework.mysql import MySQLHelper
from seven_framework.base_model import *
from seven_cloudapp_frame.models.cache_model import *

class CapBusinessInfoModel(CacheModel):
    def __init__(self, db_connect_key='db_cloudapp', sub_table=None, db_transaction=None, context=None, is_auto=False):
        super(CapBusinessInfoModel, self).__init__(CapBusinessInfo, sub_table)
        self.db = MySQLHelper(self.convert_db_config(db_connect_key, is_auto))
        self.db_connect_key = db_connect_key
        self.db_transaction = db_transaction
        self.db.context = context

    #方法扩展请继承此类

class CapBusinessInfo:

    def __init__(self):
        super(CapBusinessInfo, self).__init__()
        self.id = 0  # id
        self.guid = ""  # guid
        self.business_name = ""  # 商家名称
        self.phone = "" # 手机号
        self.business_desc = "" # 商家描述
        self.business_code = ""  # 商家代码
        self.product_ids = "" # 产品标识(逗号分隔)
        self.extend_info = {} # 扩展信息
        self.is_release = 0  # 是否发布(1-是 0-否)
        self.create_date = "1900-01-01 00:00:00"  # 创建时间
        self.modify_date = "1900-01-01 00:00:00"  # 修改时间

    @classmethod
    def get_field_list(self):
        return ['id', 'guid', 'business_name','phone', 'business_desc', 'business_code', 'product_ids', 'extend_info', 'is_release', 'create_date', 'modify_date']

    @classmethod
    def get_primary_key(self):
        return "id"

    def __str__(self):
        return "cap_business_info_tb"
