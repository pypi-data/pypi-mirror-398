'''
Created by auto_sdk on 2023.03.13
'''
from seven_top.top.api.base import RestApi
class OpencrmCrowdinstsGatherRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)
		self.action = None
		self.crowd_inst_ids = None
		self.node_inst = None

	def getapiname(self):
		return 'taobao.opencrm.crowdinsts.gather'
