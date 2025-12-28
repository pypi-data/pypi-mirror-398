'''
Created by auto_sdk on 2021.09.14 奇门增量获取卖家会员(调用淘宝源(taobao.crm.members.search.privy)
'''
from seven_top.top.api.base import RestApi


class QmTbCrmMembersSearchPrivyGet(RestApi):
    def __init__(self, domain='gw.api.taobao.com', port=80):
        RestApi.__init__(self, domain, port)
        self.page_size = 10
        self.page_index = 1
        # self.buyer_nick = ""
        # self.grade = 0
        # self.ouid = ""
        # self.last_trade_time_min = ""
        # self.last_trade_time_max = ""
        # self.trade_amount_min = ""
        # self.trade_amount_max = ""
        # self.trade_count_min = 0
        # self.trade_count_max = 0
        # self.relation_source = 0
        # self.group_id = 0
        self.access_permit = ""

    def getapiname(self):
        return 'tb.crm.members.search.privy.get'
