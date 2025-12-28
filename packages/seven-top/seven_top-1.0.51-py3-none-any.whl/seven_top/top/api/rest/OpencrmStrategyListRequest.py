'''
Created by auto_sdk on 2021.09.24
'''
from seven_top.top.api.base import RestApi
class OpencrmStrategyListRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)
		self.query_base_do = None
		self.task_open_dto = None

	def getapiname(self):
		return 'taobao.opencrm.strategy.list'
