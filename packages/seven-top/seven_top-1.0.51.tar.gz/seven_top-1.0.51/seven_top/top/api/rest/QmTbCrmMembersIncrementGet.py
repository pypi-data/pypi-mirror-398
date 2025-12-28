'''
Created by auto_sdk on 2021.09.14 奇门增量获取卖家会员(调用淘宝源taobao.crm.members.increment.get)
'''
from seven_top.top.api.base import RestApi


class QmTbCrmMembersIncrementGet(RestApi):
    def __init__(self, domain='gw.api.taobao.com', port=80):
        RestApi.__init__(self, domain, port)
        self.page_size = 10
        self.page_index = 1
        # self.grade = 0
        # self.modify_time_min = ""
        # self.modify_time_max = ""
        self.access_permit = ""

    def getapiname(self):
        return 'tb.crm.members.increment.get'
