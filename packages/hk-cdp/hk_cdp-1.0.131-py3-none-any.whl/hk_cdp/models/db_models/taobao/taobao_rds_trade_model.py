#此文件由rigger自动生成
from seven_framework.mysql import MySQLHelper
from seven_framework.base_model import *
from seven_cloudapp_frame.models.cache_model import *


class TaoBaoRdsTradeModel(CacheModel):
    def __init__(self, db_connect_key='db_cloudapp', db_config_dict=None, sub_table=None, db_transaction=None, context=None, is_auto=False):
        super(TaoBaoRdsTradeModel, self).__init__(TaoBaoRdsTrade, sub_table)
        if not db_config_dict:
            db_config_dict = config.get_value(db_connect_key)
        self.db = MySQLHelper(self.convert_db_config(db_config_dict, is_auto))
        self.db_connect_key = db_connect_key
        self.db_transaction = db_transaction
        self.db.context = context

    #方法扩展请继承此类


class TaoBaoRdsTrade:
    def __init__(self):
        super(TaoBaoRdsTrade, self).__init__()
        self.tid = 0  # 订单号
        self.status = ""  # 状态
        self.type = ""  # 类型
        self.seller_nick = ""  # 卖家昵称
        self.buyer_nick = ""  # 买家昵称
        self.created = ""  # 创建时间
        self.modified = ""  # 修改时间
        self.jdp_hashcode = ""  # jdp_hashcode
        self.jdp_response = {}  # 接口返回值
        self.jdp_created = ""  # jdp_created
        self.jdp_modified = ""  # jdp_modified

    @classmethod
    def get_field_list(self):
        return ['tid', 'status', 'type', 'seller_nick', 'buyer_nick', 'created', 'modified', 'jdp_hashcode', 'jdp_response', 'jdp_created', 'jdp_modified']

    @classmethod
    def get_primary_key(self):
        return "tid"

    def __str__(self):
        return "taobao_rds_trade_tb"
