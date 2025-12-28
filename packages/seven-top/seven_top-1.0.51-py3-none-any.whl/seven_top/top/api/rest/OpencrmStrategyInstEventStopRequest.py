'''
Created by auto_sdk on 2023.04.03
'''
from seven_top.top.api.base import RestApi
class OpencrmStrategyInstEventStopRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)
		self.code = None
		self.task_inst_id = None

	def getapiname(self):
		return 'taobao.opencrm.strategy.inst.event.stop'
