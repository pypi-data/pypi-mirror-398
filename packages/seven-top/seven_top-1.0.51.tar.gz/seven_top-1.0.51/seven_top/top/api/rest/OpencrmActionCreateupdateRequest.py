'''
Created by auto_sdk on 2021.11.18
'''
from seven_top.top.api.base import RestApi
class OpencrmActionCreateupdateRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)
		self.biz_type = None
		self.content = None
		self.deliver_type = None
		self.operate_type = None
		self.rule_inst_id = None

	def getapiname(self):
		return 'taobao.opencrm.action.createupdate'
