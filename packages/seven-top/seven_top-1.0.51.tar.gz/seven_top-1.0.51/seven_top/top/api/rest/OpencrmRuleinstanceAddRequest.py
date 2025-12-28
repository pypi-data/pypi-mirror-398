'''
Created by auto_sdk on 2021.11.23
'''
from seven_top.top.api.base import RestApi
class OpencrmRuleinstanceAddRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)
		self.params = None
		self.rule_id = None

	def getapiname(self):
		return 'taobao.opencrm.ruleinstance.add'
