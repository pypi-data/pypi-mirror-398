'''
Created by auto_sdk on 2021.11.25
'''
from seven_top.top.api.base import RestApi
class OpencrmSmsQresultRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)
		self.deliver_type = None
		self.node_inst_id = None
		self.query_type = None
		self.targets = None

	def getapiname(self):
		return 'taobao.opencrm.sms.qresult'
