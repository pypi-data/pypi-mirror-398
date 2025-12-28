'''
Created by auto_sdk on 2022.03.28
'''
from seven_top.top.api.base import RestApi
class OpencrmStrategyTemplateListRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)

	def getapiname(self):
		return 'taobao.opencrm.strategy.template.list'
