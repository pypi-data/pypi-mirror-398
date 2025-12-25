#此文件由rigger自动生成
from seven_framework.mysql import MySQLHelper
from seven_framework.base_model import *


class StorePrefixLogModel(BaseModel):
    def __init__(self, db_connect_key='db_cloudapp', sub_table=None, db_transaction=None, context=None, is_auto=False):
        super(StorePrefixLogModel, self).__init__(StorePrefixLog, sub_table)
        self.db = MySQLHelper(self.convert_db_config(db_connect_key, is_auto))
        self.db_connect_key = db_connect_key
        self.db_transaction = db_transaction
        self.db.context = context

    #方法扩展请继承此类

class StorePrefixLog:

    def __init__(self):
        super(StorePrefixLog, self).__init__()
        self.id = 0  # 主键id
        self.store = ""  # 店铺guid
        self.prefix = ""  # 号段
        self.status = 0  # 状态(0-未生成 1已生成)
        self.created_at = "1900-01-01 00:00:00"  #
        self.create_date = "1900-01-01 00:00:00"  # 创建时间

    @classmethod
    def get_field_list(self):
        return ['id', 'store', 'prefix', 'status', 'created_at', 'create_date']

    @classmethod
    def get_primary_key(self):
        return "id"

    def __str__(self):
        return "store_prefix_log_tb"
