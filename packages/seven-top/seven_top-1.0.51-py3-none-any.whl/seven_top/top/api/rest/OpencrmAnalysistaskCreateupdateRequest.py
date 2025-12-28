'''
Created by auto_sdk on 2023.12.19
'''
from seven_top.top.api.base import RestApi
class OpencrmAnalysistaskCreateupdateRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)
		self.activity_id = None
		self.activity_inst_id = None
		self.analysis_type = None
		self.cover_crowd_inst_ids = None
		self.end_time = None
		self.market_crowd_inst_ids = None
		self.node_id = None
		self.node_inst_id = None
		self.start_time = None

	def getapiname(self):
		return 'taobao.opencrm.analysistask.createupdate'
