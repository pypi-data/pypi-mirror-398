'''
Created by auto_sdk on 2021.11.23
'''
from seven_top.top.api.base import RestApi
class OpencrmAnalysisreportGetRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)
		self.activity_id = None
		self.activity_inst_id = None
		self.analysis_type = None
		self.end_time = None
		self.node_id = None
		self.node_inst_id = None
		self.start_time = None

	def getapiname(self):
		return 'taobao.opencrm.analysisreport.get'
