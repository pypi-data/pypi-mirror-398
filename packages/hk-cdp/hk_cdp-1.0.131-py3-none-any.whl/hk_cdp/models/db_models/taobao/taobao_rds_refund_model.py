#此文件由rigger自动生成
from seven_framework.mysql import MySQLHelper
from seven_framework.base_model import *
from seven_cloudapp_frame.models.cache_model import *


class TaoBaoRdsRefundModel(CacheModel):
    def __init__(self, db_connect_key='db_cloudapp', db_config_dict=None, sub_table=None, db_transaction=None, context=None, is_auto=False):
        super(TaoBaoRdsRefundModel, self).__init__(TaoBaoRdsRefund, sub_table)
        if not db_config_dict:
            db_config_dict = config.get_value(db_connect_key)
        self.db = MySQLHelper(self.convert_db_config(db_config_dict, is_auto))
        self.db_connect_key = db_connect_key
        self.db_transaction = db_transaction
        self.db.context = context

    #方法扩展请继承此类


class TaoBaoRdsRefund:
    def __init__(self):
        super(TaoBaoRdsRefund, self).__init__()
        self.refund_id = 0  # 退款号
        self.seller_nick = ""  # 卖家昵称
        self.buyer_nick = ""  # 买家昵称
        self.status = ""  # 状态
        self.tid = 0  # 订单号
        self.oid = 0  # 子订单号
        self.created = ""  # 创建时间
        self.modified = ""  # 修改时间
        self.jdp_hashcode = ""  # jdp_hashcode
        self.jdp_response = {}  # 接口返回值
        self.jdp_created = ""  # jdp_created
        self.jdp_modified = ""  # jdp_modified

    @classmethod
    def get_field_list(self):
        return ['refund_id', 'seller_nick', 'buyer_nick', 'status', 'tid', 'oid', 'created', 'modified', 'jdp_hashcode', 'jdp_response', 'jdp_created', 'jdp_modified']

    @classmethod
    def get_primary_key(self):
        return "refund_id"

    def __str__(self):
        return "taobao_rds_refund_tb"
