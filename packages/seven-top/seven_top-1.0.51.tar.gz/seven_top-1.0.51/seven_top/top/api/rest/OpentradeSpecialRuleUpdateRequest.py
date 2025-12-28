'''
Created by auto_sdk on 2020.10.14
'''
from seven_top.top.api.base import RestApi
class OpentradeSpecialRuleUpdateRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)
		self.item_ids = None
		self.limit_num = None

	def getapiname(self):
		return 'taobao.opentrade.special.rule.update'
