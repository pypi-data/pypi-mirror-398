'''
Created by auto_sdk on 2023.09.19
'''
from seven_top.top.api.base import RestApi
class OpencrmExtStrategyQueryRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)
		self.ext_deliver_strategy_dto = None

	def getapiname(self):
		return 'taobao.opencrm.ext.strategy.query'
