'''
Created by auto_sdk on 2022.05.09
'''
from seven_top.top.api.base import RestApi
class OpencrmStrategyActivityListRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)
		self.activity_type = None

	def getapiname(self):
		return 'taobao.opencrm.strategy.activity.list'
