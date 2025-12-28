'''
Created by auto_sdk on 2022.11.17
'''
from seven_top.top.api.base import RestApi
class MiniappInteractBenefitItemGetRequest(RestApi):
    def __init__(self,domain='gw.api.taobao.com',port=80):
        RestApi.__init__(self,domain, port)
        self.mini_app_seller_strategy_benefit_item_bind_request = None

    def getapiname(self):
        return 'taobao.miniapp.interact.benefit.item.get'
