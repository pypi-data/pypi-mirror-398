'''
Created by auto_sdk on 2022.02.22
'''
from seven_top.top.api.base import RestApi
class OpencrmStrategyVipcustomergradeGetRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)

	def getapiname(self):
		return 'taobao.opencrm.strategy.vipcustomergrade.get'
