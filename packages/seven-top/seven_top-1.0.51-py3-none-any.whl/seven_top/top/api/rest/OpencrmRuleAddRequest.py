'''
Created by auto_sdk on 2021.11.23
'''
from seven_top.top.api.base import RestApi
class OpencrmRuleAddRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)
		self.biz_type = None
		self.grade_code = None
		self.rule_desc = None
		self.rule_name = None
		self.rule_text = None
		self.rule_type = None
		self.total_flag = None

	def getapiname(self):
		return 'taobao.opencrm.rule.add'
