
#此文件由rigger自动生成
from seven_framework.mysql import MySQLHelper
from seven_framework.base_model import *


class PrefixInfoModel(BaseModel):
    def __init__(self, db_connect_key='db_cloudapp', sub_table=None, db_transaction=None, context=None):
        super(PrefixInfoModel, self).__init__(PrefixInfo, sub_table)
        self.db = MySQLHelper(config.get_value(db_connect_key))
        self.db_connect_key = db_connect_key
        self.db_transaction = db_transaction
        self.db.context = context

    #方法扩展请继承此类
    
class PrefixInfo:

    def __init__(self):
        super(PrefixInfo, self).__init__()
        self.id = 0  # 
        self.guid = None  # 
        self.prefix = ""  # 
        self.status = 0  # 
        self.updated_by_id = 0  # 
        self.created_by_id = 0  # 
        self.updated_at = "1900-01-01 00:00:00"  # 
        self.created_at = "1900-01-01 00:00:00"  # 
        self.create_date = "1900-01-01 00:00:00"  # 

    @classmethod
    def get_field_list(self):
        return ['id', 'guid', 'prefix', 'status', 'updated_by_id', 'created_by_id', 'updated_at', 'created_at', 'create_date']
        
    @classmethod
    def get_primary_key(self):
        return "id"

    def __str__(self):
        return "prefix_info_tb"
    