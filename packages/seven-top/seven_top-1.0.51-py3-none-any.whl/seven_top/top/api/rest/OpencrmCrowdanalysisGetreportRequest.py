'''
Created by auto_sdk on 2021.11.23
'''
from seven_top.top.api.base import RestApi
class OpencrmCrowdanalysisGetreportRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)
		self.end_time = None
		self.start_time = None
		self.task_id = None

	def getapiname(self):
		return 'taobao.opencrm.crowdanalysis.getreport'
