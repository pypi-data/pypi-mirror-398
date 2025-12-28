'''
Created by auto_sdk on 2021.11.18
'''
from seven_top.top.api.base import RestApi
class OpencrmDatabankCrowdSyncRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)
		self.activity_id = None
		self.activity_inst_id = None
		self.brand_id = None
		self.crowd_id = None
		self.node_id = None
		self.node_inst_id = None

	def getapiname(self):
		return 'taobao.opencrm.databank.crowd.sync'
