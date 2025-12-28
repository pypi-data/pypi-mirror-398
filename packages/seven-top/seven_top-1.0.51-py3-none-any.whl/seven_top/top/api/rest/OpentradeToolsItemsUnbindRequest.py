'''
Created by auto_sdk on 2020.12.07
'''
from seven_top.top.api.base import RestApi
class OpentradeToolsItemsUnbindRequest(RestApi):
    def __init__(self,domain='gw.api.taobao.com',port=80):
        RestApi.__init__(self,domain, port)
        self.item_ids = None
        self.miniapp_id = None

    def getapiname(self):
        return 'taobao.opentrade.tools.items.unbind'
