'''
Created by auto_sdk on 2022.09.19
'''
from seven_top.top.api.base import RestApi
class OpencrmNodereportGetbcRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)
		self.app_type = None
		self.node_inst_id = None

	def getapiname(self):
		return 'taobao.opencrm.nodereport.getbc'
