'''
Created by auto_sdk on 2022.09.19
'''
from seven_top.top.api.base import RestApi
class OpencrmCrowdinstFilterRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)
		self.crowd_inst_id = None
		self.node_inst = None
		self.rules = None

	def getapiname(self):
		return 'taobao.opencrm.crowdinst.filter'
