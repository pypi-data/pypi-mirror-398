'''
Created by auto_sdk on 2025.07.07
'''
from seven_top.top.api.base import RestApi


class IndustryTrendyBlindboxAddRequest(RestApi):
    def __init__(self,domain='gw.api.taobao.com',port=80):
        RestApi.__init__(self,domain, port)
        self.trendy_toy_blind_box_record_add_request = None

    def getapiname(self):
        return 'taobao.industry.trendy.blindbox.add'
