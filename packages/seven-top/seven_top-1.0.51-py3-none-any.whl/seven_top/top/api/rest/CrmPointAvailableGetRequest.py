'''
Created by auto_sdk on 2021.11.23
'''
from seven_top.top.api.base import RestApi
class CrmPointAvailableGetRequest(RestApi):
    def __init__(self,domain='gw.api.taobao.com',port=80):
        RestApi.__init__(self,domain, port)
        self.buyer_nick = None
        self.mix_nick = None
        self.open_uid = None

    def getapiname(self):
        return 'taobao.crm.point.available.get'
