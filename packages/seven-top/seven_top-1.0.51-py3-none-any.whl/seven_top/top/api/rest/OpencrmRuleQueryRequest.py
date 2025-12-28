'''
Created by auto_sdk on 2021.11.18
'''
from seven_top.top.api.base import RestApi
class OpencrmRuleQueryRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)
		self.rule_id_list = None

	def getapiname(self):
		return 'taobao.opencrm.rule.query'
